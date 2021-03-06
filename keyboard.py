#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on 13/10/2021 15:48
@author: hheise

"""

import curses

# get the curses screen window
screen = curses.initscr()

# turn off input echoing
curses.noecho()

# respond to keys immediately (don't wait for enter)
curses.cbreak()

# map arrow keys to special values
screen.keypad(True)

try:
    while True:
        char = screen.getch()
        if char == ord('q'):
            break
        elif char == curses.KEY_RIGHT:
            screen.addstr(0, 0, 'right')
        elif char == curses.KEY_LEFT:
            screen.addstr(0, 0, 'left ')
        elif char == curses.KEY_UP:
            screen.addstr(0, 0, 'up   ')
        elif char == curses.KEY_DOWN:
            screen.addstr(0, 0, 'down ')
finally:
    # shut down
    curses.nocbreak()
    screen.keypad(0)
    curses.echo()
    curses.endwin()
