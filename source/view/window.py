import curses
import pandas as pd

from .utils.general import fix_text_to_width
from .colors import CursesColors

class Window:

    """
        col, row = coordinates of the top left position of the window
        height, width = self explanatory
        parent = parent window
    """

    def __init__(self, col, row, height, width, parent=None, colors=None, defaultchar=' ', defaultattr=0):
        self.parent = parent
        self.changed = []
        self.children = []
        self.colors = colors
        self.col = col
        self.row = row
        self.height = height
        self.width = width
        self.data = [[(defaultchar, defaultattr) for i in range(width)] for j in range(height)]
        self.set_all_changed()
        self.to_delete = False

    def delete(self):
        self.to_delete = True

    def set_changed(self, row, col):
        self.changed.append((row, col))

    def update_value(self, row, col, value, modifier):
        if row < len(self.data):
            if col < len(self.data[row]):
                self.data[row][col] = (value, modifier)
                self.set_changed(row, col)


    def draw_box(self, col, row, height, width, modifier=0,
                    topline='-', bottomline='-', rightline='|', leftline='|',
                    tl='+', tr='+', bl='+', br='+', fill=''):
        for i in range(1, width-1):
            self.update_value(row , col + i, topline, modifier)
            self.update_value(row + height - 1, col + i, bottomline, modifier)

        for i in range(1, height-1):
            self.update_value(row + i, col, leftline, modifier)
            self.update_value(row + i, col + width - 1, rightline, modifier)

        self.update_value(row, col, tl, modifier)
        self.update_value(row, col + width - 1, tr, modifier)
        self.update_value(row + height - 1, col, bl, modifier)
        self.update_value(row + height - 1, col + width - 1, br, modifier)

        if fill:
            for r in range(row+1, row+height - 1):
                for c in range(col+1, col + width - 1):
                    self.update_value(r, c, fill, modifier)

    def draw_button(self, col, row, content, **kwargs):
        body = ' {} '.format(content)
        self.draw_box(col, row, 3, len(body) + 2)
        for i in range(len(body)):
            self.update_value(row+1, col + i + 1, body[i], kwargs.get('modifier', 0))

    def draw_border(self, modifier=0, title="",
                    topline='-', bottomline='-', rightline='|', leftline='|',
                    tl='+', tr='+', bl='+', br='+'):
        self.draw_box(0, 0, self.height, self.width, modifier=modifier,
                        topline=topline, bottomline=bottomline, rightline=rightline,
                        leftline=leftline, tl=tl, tr=tr, bl=bl, br=br)
        if title:
            t = " {} ".format(title)
            for i in range(len(t)):
                self.update_value(0, i + 2, t[i], modifier | curses.A_REVERSE)

    def draw_text(self, text, row, col, mod):
        for i in range(len(text)):
            self.update_value(row, col+i, text[i], mod)

    def draw_text_box(self, text, row, col, height, width, alignment='l', mod=0):
        lines = fix_text_to_width(text, width, alignment=alignment)
        for r in range(min(height, len(lines))):
            line = lines[r]
            for i in range(len(line)):
                self.update_value(row + r, col + i, line[i], mod)

    def set_all_changed(self):
        for r in range(self.height):
            for c in range(self.width):
                self.set_changed(r, c)

    def remove_child(self, child):
        row = child.row
        col = child.col
        width = child.width
        height = child.height
        for r in range(height):
            for c in range(width):
                self.set_changed(row + r, col + c)
        self.children.remove(child)
        self.set_active(self)

    def prerefresh(self):
        pass

    def refresh(self, stdscr, force=False, seen_dict=None):
        self.prerefresh()
        for child in self.children:
            if child.to_delete:
                self.remove_child(child)

        if force:
            self.set_all_changed(self)

        if not seen_dict:
            seen_dict = {}

        for child in reversed(self.children):
            child.refresh(stdscr, force=force, seen_dict=seen_dict)
            child.update_parent_indices(seen_dict)

        for coords in self.changed:
            if not seen_dict.get(coords, False):
                val, mod = self.get_value(*coords)
                row, col = self.get_scr_indices(*coords)
                try:
                    stdscr.addch(row, col, ord(val), mod)
                except:
                    pass
            self.changed = []

    def get_scr_indices(self, row, col):
        outRow = self.row + row
        outCol = self.col + col
        if self.parent:
            pr, pc = self.parent.get_scr_indices(0, 0)
            outRow += pr
            outCol += pc
        return (outRow, outCol)

    def update_parent_indices(self, seen):
        for row in range(self.height):
            for col in range(self.width):
                ind = self.get_scr_indices(row, col)
                if ind  not in seen:
                    seen[ind] = True

    def get_value(self, row, col):
        # Needs to include more information; color + modifiers
        return self.data[row][col]

    def add_child(self, window):
        self.children.append(window)

    def process_char(self, char):
        pass

    def set_active(self, window):
        self.parent.set_active(window)

