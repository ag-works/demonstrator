import os
import sys
import math
import threading
import linecache
import sysconfig
from tempfile import TemporaryFile
from time import monotonic as _time, sleep
from trace import _modname, _Ignore

import keyboard
from colors import Color
from utils import clear_screen


TICK_TIME = 1.5

global orig_print, output_stream
orig_print, output_stream = print, TemporaryFile(mode="w+")

def print_func(*args, **kargs): orig_print(*args, **kargs)
def dummy_print(*args, **kwargs): orig_print(*args, file=output_stream, **kwargs)
print = dummy_print


def increment_execution_time():
    TICK_TIME += 1
    print("New tick time is ", TICK_TIME, "seconds")
    sys.exit(0)

def decrement_execution_time():
    TICK_TIME -= 1
    print("New tick time is ", TICK_TIME, "seconds")
    sys.exit(0)


keyboard.add_hotkey('ctrl+shift+plus', increment_execution_time)
keyboard.add_hotkey('ctrl+shift+-', decrement_execution_time)
# keyboard.wait()


def get_ignore_object(ignore_module, ignore_dir):
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
    else returns self.localtrace.
    """
    trace = True
    # print(event, arg, frame)
    ignore = get_ignore_object([], [])
    if event == 'call':
        code = frame.f_code
        filename = frame.f_globals.get('__file__', None)
        if filename:
            # XXX _modname() doesn't work right for packages, so
            # the ignore support won't work right for packages
            modulename = _modname(filename)
            if modulename is not None:
                ignore_it = ignore.names(filename, modulename)
                if not ignore_it:
                    if trace:
                        # print((" --- modulename: %s, funcname: %s" % (modulename, code.co_name)))
                        pass
                    return localtrace_trace
        else:
            return None


def localtrace_trace(frame, event, arg):
    if event == "line":
        # record the file name and line number of every trace
        filename = frame.f_code.co_filename
        lineno = frame.f_lineno
        lvars = frame.f_locals

        if filename == __file__:
            return localtrace_trace

        print_code(filename, lineno)

    return localtrace_trace


def print_code(filename, lineno):
    clear_screen()
    terminal_size = os.get_terminal_size()
    lines, columns = terminal_size.lines, terminal_size.columns
    bname = os.path.basename(filename)
    current_line = linecache.getline(filename, lineno)
    display_name = "{0} {1}".format("*" * math.floor((columns - len(bname)) / 2), bname)
    display_name = "{0} {1}".format(display_name, "*" * (columns - len(display_name) - 1))

    orig_print("*" * columns)
    orig_print(display_name)
    orig_print("*" * columns, "\n")
    
    for idx,line in enumerate(linecache.getlines(filename)):
        if idx+1 == lineno:
            orig_print("%s%s:%d\t%s%s" % (Color.BG.orange, bname.strip(), idx + 1, line, Color.reset), end='')
        else:
            orig_print("%s:%d\t%s%s" % (bname.strip(), idx + 1, line, Color.reset), end='')
    sleep(TICK_TIME)


def display_and_release_output():
    # This prints the actual `stdout` output from the provided program and releases 
    # `output_stream` resource for garbage collection
    global output_stream
    clear_screen()
    output_stream.seek(0)
    orig_print(output_stream.read())
    del output_stream


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

        display_and_release_output()
    except OSError as err:
        sys.exit("Cannot run file %r because: %s" % (sys.argv[0], err))
    except SystemExit:
        pass
    
if __name__ == '__main__':
    main()
