import math
import os

from utils import clear_screen, get_relative_path
from colors import Color
from constants import *


translation_white_space_map = {
    9: None,    # horizontal tab (\t)
    10: None,   # new line character (\n)
    13: None,   # carriage return (\r)
}


def get_terminal_size():
    terminal_size = os.get_terminal_size()
    return terminal_size.lines, terminal_size.columns


def display_vars(global_vars, local_vars, char=">"):
    from demonstrate import orig_print

    lines, cols = get_terminal_size()
    lineno, position = 2, math.floor(cols * 0.65)
    maxlength = cols - position
    message = " Local Variables ".center(maxlength, char)
    orig_print(f"\x1b[{lineno};{position}f{Color.FG.lightgreen}{ message }{Color.reset}", end="")
    lineno += 1
    for key, value in tuple(local_vars.items())[:10]:
        message = f"{Color.FG.lightgreen}{char * 2}{Color.reset} " + f"{key}: {value}"[:maxlength - 3]
        message = message.translate(translation_white_space_map)
        orig_print(f"\x1b[{lineno};{position}f{ message }", end="")
        lineno += 1
    else:
        orig_print(f"\x1b[{lineno};{position}f{Color.FG.lightgreen}{char * 2}{Color.reset}", end="")
        lineno += 1

    message = " Global Variables ".center(maxlength, char)
    orig_print(f"\x1b[{lineno};{position}f{Color.FG.lightgreen}{ message }{Color.reset}", end="")
    lineno += 1
    for key, value in tuple(global_vars.items())[:10]:
        message = f"{Color.FG.lightgreen}{char * 2}{Color.reset} " + f"{key}: {value}"[:maxlength - 3]
        message = message.translate(translation_white_space_map)
        orig_print(f"\x1b[{lineno};{position}f{ message }", end="")
        lineno += 1
    else:
        orig_print(f"\x1b[{lineno};{position}f{Color.FG.lightgreen}{char * 2}{Color.reset}", end="")
        lineno += 1

    message = char * maxlength
    orig_print(f"\x1b[{lineno};{position}f{Color.FG.lightgreen}{ message }{Color.reset}", end="")
    lineno += 1
    for i in range(lines - lineno):
        orig_print(f"\x1b[{lineno + i};{position}f{Color.FG.lightgreen}{char * 2}{Color.reset}", end="")


def display_and_release_output(output_stream):
    # This prints the actual `stdout` output from the provided program and releases 
    # `output_stream` resource for garbage collection
    from demonstrate import orig_print

    clear_screen()
    _, cols = get_terminal_size()
    output_stream.seek(0)
    orig_print(Color.FG.lightgreen, "x" * cols, sep="")
    orig_print(" Program Output ".center(cols, "x"))
    orig_print("x" * cols, Color.reset)
    orig_print(output_stream.read())
    del output_stream

    
def display_filename(filename, lpad=">", rpad="<"):
    from demonstrate import orig_print
   
    _, cols = get_terminal_size()
    relative_path = get_relative_path(filename)
    left_padding = lpad * math.floor((cols - len(relative_path)) / 2)
    right_padding = rpad * (cols - len(left_padding + relative_path) - 2)
    display_name = "{0} {1} {2}".format(left_padding, relative_path, right_padding)
    orig_print(f"\x1b[H{Color.FG.lightgreen}{Color.bold}{display_name}{Color.reset}")
    # orig_print(f"{Color.reset}")


def display_code(filename, code_lines, lineno, char='>'):
    from demonstrate import orig_print

    clear_screen()
    lines, columns = get_terminal_size()

    # Reducing the available number of lines by 1 so that new line character of the last line 
    # doesn't impact the view
    remaining_lines = lines - 1   
    display_filename(filename)
    remaining_lines -= 1
    
    if lineno < remaining_lines < len(code_lines):
        start, end = 0, remaining_lines
    elif lineno <= len(code_lines) <= remaining_lines:
        start, end = 0, len(code_lines)
    elif lineno + remaining_lines > len(code_lines):
        start, end = len(code_lines) - remaining_lines, len(code_lines)
    else:
        start, end = lineno - math.floor(remaining_lines / 2), lineno + math.floor(remaining_lines / 2)
        
    for idx,line in enumerate(code_lines[start:end]):
        current_line_num = start + idx + 1 
        if current_line_num == lineno:
            orig_print(f"{Color.FG.lightgreen}{char}{current_line_num:5} {char * 2}{Color.reset} {Color.BG.orange}{line}{Color.reset}", end='')
        else:
            orig_print(f"{Color.FG.lightgreen}{char}{current_line_num:5} {char * 2}{Color.reset} {line}{Color.reset}", end='')

    for i in range(remaining_lines + start - end):
        orig_print(f"{Color.FG.lightgreen}{char: <6} {char * 2}{Color.reset}")


def display_module_message(filename):
    from demonstrate import orig_print

    clear_screen()
    lines, columns = get_terminal_size()
    orig_print("\n" * math.floor(lines / 2))
    message = f"Getting inside {filename}".center(columns)
    orig_print(message)
