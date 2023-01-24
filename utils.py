import os


MOVE_CURSOR_UP = "\033[1A"
ERASE = "\x1b[2K"

def clear_screen():
    if os.name == 'nt':
        os.system('cls')
    else:
        os.system('clear')

def move_one_line_up_in_ternimal():
    print(MOVE_CURSOR_UP + ERASE, end="")
