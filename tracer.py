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


TICK_TIME = 1.8

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


keyboard.add_hotkey('ctrl + shift + plus', increment_execution_time)
keyboard.add_hotkey('ctrl + shift + -', decrement_execution_time)
# keyboard.wait()


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
    trace = True
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
                    terminal_size = os.get_terminal_size()
                    lines, columns = terminal_size.lines, terminal_size.columns
                    clear_screen()
                    orig_print("\n" * math.floor(lines / 2))
                    message = "Getting inside %s" % filename.replace(os.getcwd(), "").lstrip(os.path.sep)
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
    clear_screen()
    terminal_size = os.get_terminal_size()
    lines, columns = terminal_size.lines, terminal_size.columns
    bname = os.path.basename(filename)
    display_name = "{0} {1}".format(">" * math.floor((columns - len(bname)) / 2), bname)
    display_name = "{0} {1}".format(display_name, "<" * (columns - len(display_name) - 1))

    # Reducing the available number of lines by 1 so that new line character of the last line 
    # doesn't impact the view
    remaining_lines = lines - 1    
    # orig_print(f"{'-' * columns}" % ())
    orig_print(f"{Color.FG.lightgreen}{Color.bold}{display_name}")
    # orig_print("-" * columns)
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
            orig_print("%s%s:%d\t%s%s" % (Color.BG.orange, bname.strip(), current_line_num, line, Color.reset), end='')
        else:
            orig_print("%s:%d\t%s%s" % (bname.strip(), current_line_num, line, Color.reset), end='') 

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
