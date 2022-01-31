import curses
import pandas as pd
from .colors import CursesColors
from .window import Window
from .popup import Popup

class MainWindow(Window):

    def __init__(self):
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
        super().__init__(0, 0, rows, columns, colors=self.colors)

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
        pass

    def loop(self):
        while True:
            self.refresh(self.stdscr)
            self.stdscr.refresh()
            ch = self.stdscr.getch()
            if (ch == ord('q')):
                self.terminate()
                break


