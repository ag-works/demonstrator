import os
import sys
import threading
import linecache
import sysconfig
from tempfile import TemporaryFile
from time import sleep
from trace import _modname, _Ignore

import keyboard
from utils import get_relative_path
from terminal import display_code, display_vars, display_and_release_output, display_module_message
from constants import *

TICK_TIME = 1.8
EXECUTION_PAUSED = False

orig_print, output_stream = print, TemporaryFile(mode="w+")
displayed_module = None

def print_func(*args, **kargs): orig_print(*args, **kargs)
def dummy_print(*args, **kwargs): orig_print(*args, file=output_stream, **kwargs)
print = dummy_print


def increment_execution_time():
    global TICK_TIME
    TICK_TIME += 1


def decrement_execution_time():
    global TICK_TIME
    TICK_TIME -= 1


def toggle_execution_mode():
    global EXECUTION_PAUSED
    EXECUTION_PAUSED = not EXECUTION_PAUSED
    orig_print("\x1b[H", "Paused" if EXECUTION_PAUSED else "Running", sep="")


try:
    keyboard.add_hotkey('ctrl+shift+plus', increment_execution_time, suppress=True)
    keyboard.add_hotkey('ctrl+shift+-', decrement_execution_time, suppress=True)
    keyboard.add_hotkey('space', toggle_execution_mode, suppress=True)
except OSError as e:
    pass


def get_ignore_object(ignore_module, ignore_dir):
    """Returns an Ignore object for ignoring the provided modules and directories"""

    _prefix = sysconfig.get_path("stdlib")
    _exec_prefix = sysconfig.get_path("platstdlib")
    _data = sysconfig.get_path("data")

    def parse_ignore_dir(s):
        s = os.path.expanduser(os.path.expandvars(s))
        s = s.replace('$prefix', _prefix).replace('$exec_prefix', _exec_prefix)
        return os.path.normpath(s)

    ignore_module = [mod.strip() for i in ignore_module for mod in i.split(',')]
    ignore_dir = [parse_ignore_dir(s) for i in ignore_dir for s in i.split(os.pathsep)]
    ignore_dir.extend([_prefix, _data])
    return _Ignore(ignore_module, ignore_dir)


def global_trace(frame, event, arg):
    """Handler for call events.

    If the code block being entered is to be ignored, returns `None',
    else returns localtrace.
    """
    while EXECUTION_PAUSED is True:
        sleep(TICK_TIME)

    global displayed_module
    if event == 'call':
        code = frame.f_code
        filename = frame.f_globals.get('__file__', None)
        if filename:
            if filename == __file__ :
                return

            modulename = _modname(filename)
            relative_filepath = get_relative_path(filename)
            if modulename is not None and relative_filepath != displayed_module:
                ignore = get_ignore_object([], [])
                ignore_it = ignore.names(filename, modulename)
                if ignore_it:
                    return

                display_module_message(relative_filepath)
                sleep(TICK_TIME)
                displayed_module = relative_filepath
                return localtrace_trace
        else:
            return None


def localtrace_trace(frame, event, arg):
    while EXECUTION_PAUSED is True:
        sleep(TICK_TIME)

    if event == "line":
        # record the file name and line number of every trace
        filename = frame.f_code.co_filename
        lineno = frame.f_lineno
        lvars = frame.f_locals
        gvars = frame.f_globals

        code_lines = linecache.getlines(filename)
        if filename == __file__ or len(code_lines) == 0:
            return localtrace_trace

        display_vars(gvars, lvars)
        display_code(filename, code_lines, lineno)
        sleep(TICK_TIME)

    return localtrace_trace


def main():
    try:
        arguments = sys.argv
        progname = sys.argv[1]
        sys.argv = [progname, *arguments[2:]]
        sys.path[0] = os.path.dirname(progname)

        with open(progname, 'rb') as fp:
            code = compile(fp.read(), progname, 'exec')
        # try to emulate __main__ namespace as much as possible
        globs = {
            '__file__': progname,
            '__name__': '__main__',
            '__package__': None,
            '__cached__': None,
            'print': dummy_print,
        }
        threading.settrace(global_trace)
        sys.settrace(global_trace)
        try:
            exec(code, globs, globs)
        finally:
            sys.settrace(None)
            threading.settrace(None)

        display_and_release_output(output_stream)
    except OSError as err:
        sys.exit("Cannot run file %r because: %s" % (sys.argv[0], err))
    except SystemExit:
        pass
    
if __name__ == '__main__':
    main()
