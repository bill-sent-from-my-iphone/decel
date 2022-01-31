import curses

# 0:black, 1:red, 2:green, 3:yellow, 4:blue, 5:magenta, 6:cyan, and 7:white.

colors = {
        "Black" : 0,
        "Red" : 1,
        "Green" : 2,
        "Yellow" : 3,
        "Blue" : 4,
        "Magenta" : 5,
        "Cyan" : 6,
        "White": 7
        }

cs = {
        0 : curses.COLOR_BLACK,
        1 : curses.COLOR_RED,
        2 : curses.COLOR_GREEN,
        3 : curses.COLOR_YELLOW,
        4 : curses.COLOR_BLUE,
        5 : curses.COLOR_MAGENTA,
        6 : curses.COLOR_CYAN,
        7 : curses.COLOR_WHITE,
        }

class CursesColors:

    def __init__(self):
        self.create()
        self.colors = colors
        self.color_ids = { colors[i] : i for i in colors }
        self.create()

    def create(self):
        for bg in range(8):
            for fg in range(8):
                color_id = bg * 8 + fg + 1
                try:
                    curses.init_pair(color_id, cs[fg], cs[bg])
                except:
                    pass

    def get_color_id(self, background, foreground):
        bg = self.colors[background]
        fg = self.colors[foreground]
        return curses.color_pair(bg * 8 + fg + 1)
