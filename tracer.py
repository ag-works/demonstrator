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
from utils import clear_screen, get_terminal_size, MOVE_CURSOR_UP


TICK_TIME = 1.8
EXECUTION_PAUSED = False

global orig_print, output_stream, displayed_module
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
    lines, _ = get_terminal_size()
    orig_print(MOVE_CURSOR_UP * lines, "Paused" if EXECUTION_PAUSED else "Running")


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
    else returns self.localtrace.
    """
    while EXECUTION_PAUSED is True:
        sleep(TICK_TIME)

    global displayed_module
    if event == 'call':
        code = frame.f_code
        filename = frame.f_globals.get('__file__', None)
        if filename:
            modulename = _modname(filename)
            relative_filepath = filename.replace(os.getcwd(), "").lstrip(os.path.sep)
            if modulename is not None and relative_filepath != displayed_module:
                ignore = get_ignore_object([], [])
                ignore_it = ignore.names(filename, modulename)
                if ignore_it:
                    return

                clear_screen()
                lines, columns = get_terminal_size()
                orig_print("\n" * math.floor(lines / 2))
                message = "Getting inside %s" % relative_filepath
                displayed_module = relative_filepath
                orig_print(" " * math.floor((columns - len(message)) / 2), message)
                sleep(TICK_TIME)
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
    while EXECUTION_PAUSED is True:
        sleep(TICK_TIME)

    clear_screen()
    lines, columns = get_terminal_size()
    display_name = "{0} {1}".format(">" * math.floor((columns - len(displayed_module)) / 2), displayed_module)
    display_name = "{0} {1}".format(display_name, "<" * (columns - len(display_name) - 1))

    # Reducing the available number of lines by 1 so that new line character of the last line 
    # doesn't impact the view
    remaining_lines = lines - 1    
    orig_print(f"{Color.FG.lightgreen}{Color.bold}{display_name}")
    orig_print(f"{Color.reset}")
    remaining_lines -= 2
    
    code_lines = linecache.getlines(filename)
    if lineno < remaining_lines:
        start, end = 0, remaining_lines
    elif lineno + remaining_lines > len(code_lines):
        start, end = len(code_lines) - remaining_lines, len(code_lines)
    else:
        start, end = lineno - math.floor(remaining_lines / 2), lineno + math.floor(remaining_lines / 2)
        
    for idx,line in enumerate(code_lines[start:end]):
        current_line_num = start + idx + 1 
        if current_line_num == lineno:
            orig_print("%s%d\t%s%s" % (Color.BG.orange, current_line_num, line, Color.reset), end='')
        else:
            orig_print("%d\t%s%s" % (current_line_num, line, Color.reset), end='') 

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
