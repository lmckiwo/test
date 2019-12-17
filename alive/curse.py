from curses import wrapper
import curses
import json
from collections import OrderedDict
from time import sleep
import datetime

def main(stdscr):

    height, width = stdscr.getmaxyx()
    stdscr.addstr(0,int((width - len("ATIC MONITOR"))/2), "ATIC MONITOR", curses.A_BOLD)
    stdscr.hline(1,0,'=',width)

    while True:
        stdscr.addstr(0,0, str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        with open('status.json', 'r') as statusfile:
            data = json.load(statusfile, object_pairs_hook=OrderedDict)

        spacing = 0
        row = 2
        for car in data:
            stdscr.addstr(row,spacing, car, curses.A_UNDERLINE)
            for param in data[car]:
                row+=1
                stdscr.addstr(row, spacing + 0, param + ": ", curses.A_BOLD)
                for value in data[car][param].split():
                    stdscr.addstr(row,spacing + 12, value.ljust(8))
            spacing += 25
            row = 2

#        stdscr.addstr(35, 0, " ")
        stdscr.refresh()
        # stdscr.getkey()
        sleep(5)

wrapper(main)
