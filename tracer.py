import os
import sys
import threading
import linecache
import sysconfig
from time import monotonic as _time, sleep
from trace import _modname, _Ignore


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

        # if start_time:
        #     print('%.2f' % (_time() - localtrace_trace.start_time), end=' ')

        # bname = os.path.basename(filename)
        # print("\033[43m%s:%d %s \033[0m" % (filename.strip(), lineno,
        #                         linecache.getline(filename, lineno)), end='')
        print_code(filename, lineno)
    return localtrace_trace


def print_code(filename, lineno):
    os.system("clear")
    bname = os.path.basename(filename)
    current_line = linecache.getline(filename, lineno)
    if 'print' in current_line:
        return
    
    for idx,line in enumerate(linecache.getlines(filename)):
        if idx+1 == lineno:
            print("\033[43m%s:%d %s \033[0m" % (bname.strip(), idx + 1, line), end='')
        else:
            print("%s:%d %s \033[0m" % (bname.strip(), idx + 1, line), end='')
    sleep(1.5)


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
        }
        threading.settrace(global_trace)
        sys.settrace(global_trace)
        try:
            exec(code, globs, globs)
        finally:
            sys.settrace(None)
            threading.settrace(None)
    except OSError as err:
        sys.exit("Cannot run file %r because: %s" % (sys.argv[0], err))
    except SystemExit:
        pass
    
if __name__ == '__main__':
    main()
