import curses
import pandas as pd
from .colors import CursesColors
from .window import Window
from .popup import Popup
from .sheet_window import SheetWindow
from data.table_data import TableData

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
        self.create_sheet()
        self.active_window = None

    def get_active_window(self):
        if self.active_window == None:
            self.active_window = self.sheet
        return self.active_window

    def create_sheet(self):
        df = pd.DataFrame()
        for i in range(5):
            for j in range(10):
                df.at[i, j] = 1.0
        td = TableData(dataframe=df)
        #td.add_formula(1, "B", "5 * A1 + B2 - 2*C3")
        #td.add_formula(2, "C", "5 * A1 + sum(A1:A5)")

        self.sheet = SheetWindow(0, 0, self.height, self.width, colors=self.colors, table=td)
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

    def loop(self):
        while True:
            self.refresh(self.stdscr)
            self.stdscr.refresh()
            ch = self.stdscr.getch()
            self.get_active_window().process_char(ch)
            if (ch == ord('q')):
                self.terminate()
                break
            if (ch == ord('p')):
                self.add_popup("Warning! Something happened!", "Yo my dood I'm not sure what's going on but")


