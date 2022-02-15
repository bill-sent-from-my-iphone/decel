import os
import curses
import pandas as pd
from .colors import CursesColors
from .window import Window
from .popup import Popup
from .sheet_window import SheetWindow
from data.table_data import TableData
from configfile import DecelConfig

class MainWindow(Window):

    def __init__(self, args):
        self.stdscr = None
        self.refresh_data = pd.DataFrame(dtype=bool)
        self.scr = curses.initscr()
        curses.start_color()
        self.colors = CursesColors()
        curses.noecho()
        curses.cbreak()
        rows, columns = self.size()
        self.stdscr = curses.newwin(rows, columns, 0, 0)
        self.stdscr.keypad(True)
        self.cursor = (0, 0)
        super().__init__(0, 0, rows, columns, colors=self.colors)
        self.create_sheet()
        self.active_window = None
        self.config = self.get_config()
        self.sheet.load_config(self.config)

        if args:
            filename = args[0]
            self.sheet.load_file(filename)

    def get_config(self):
        cfg = DecelConfig()
        return cfg

    def get_active_window(self):
        if self.active_window == None:
            self.active_window = self.sheet
        return self.active_window

    def create_sheet(self):
        self.sheet = SheetWindow(0, 0, self.height, self.width, parent=self, colors=self.colors)
        self.add_child(self.sheet)
        pass

    def terminate(self):
        curses.nocbreak()
        self.stdscr.keypad(False)
        curses.echo()
        curses.endwin()

    def size(self):
        return self.scr.getmaxyx()

    def add_window(self, window):
        self.windows.append(window)

    def add_popup(self, title, message):
        p = Popup("Warning!", "Yo my dood I'm not sure what's going on but I don't like it",
                parent=self, colors=self.colors)
        self.add_child(p)
        self.set_active(p)

    def set_active(self, window):
        self.active_window = window

    def set_cursor(self, row, col):
        self.cursor = (row, col)

    def loop(self):
        while True:
            self.refresh(self.stdscr)
            self.stdscr.refresh()
            self.stdscr.move(*self.cursor)
            ch = self.stdscr.getch()
            if ch == curses.KEY_RESIZE:
                continue
            else:
                self.get_active_window().process_char(ch)


