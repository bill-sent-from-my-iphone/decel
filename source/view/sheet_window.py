import curses
import numpy as np
import pandas as pd

from .utils import fix_text_to_width, align_text, min_max
from .window import Window
from data.table_data import TableData
from data.formula import colint, colval, has_tokens


CTRL_A = 1
CTRL_E = 5
CTRL_F = 6
CTRL_J = 10
CTRL_K = 11
CTRL_L = 12
CTRL_H = 263
ENTER = CTRL_J
BACKSPACE = 127
ESCAPE = 27
LEFT = 260
RIGHT = 261
UP = 259
DOWN = 258

def in_range_inc(s, e, v):
    return v >= s and v <= e

def in_range_2d(st, et, point):
    r1, c1 = st
    r2, c2 = et
    min_r, max_r = min_max(r1, r2)
    min_c, max_c = min_max(c1, c2)
    row, col = point
    col = colint(col)
    return in_range_inc(min_r, max_r, row) and in_range_inc(min_c, max_c, col)

def swap_vertical(active, anchor, value):
    down = value > 0
    r1, c1 = active
    r2, c2 = anchor

    if down:
        if r1 < r2:
            return (r2, c1), (r1, c2)
    else:
        if r1 > r2:
            return (r2, c1), (r1, c2)
    return active, anchor

def swap_horizontal(active, anchor, value):
    right = value > 0
    r1, c1 = active
    r2, c2 = anchor

    if right:
        if c1 < c2:
            return (r1, c2), (r2, c1)
    else:
        if c1 > c2:
            return (r1, c2), (r2, c1)
    return active, anchor

def normalize_anchor(active, anchor):
    if active[0] < anchor[0]:
        active, anchor = swap_vertical(active, anchor, 1)
    if active[1] < anchor[1]:
        active, anchor = swap_horizontal(active, anchor, 1)
    return active, anchor

class SheetWindow(Window):

    I_TYPE_DISPLAY = "@"
    I_TYPE_ENTRY = "="
    I_TYPE_CMD = ":"

    def __init__(self, *args, **kwargs):
        self.default_col_width = 9
        self.default_row_height = 1
        self.table = kwargs.get('table', TableData())
        if 'table' in kwargs:
            del kwargs['table']
        super().__init__(*args, **kwargs)
        self.table.load_csv('example_file.csv')
        self.column_widths = {}
        self.row_heights = {}
        self.draw_border(title='Decel')
        self.current_row = 0
        self.current_col = 0
        self.c_row = 1
        self.c_col = 1
        self.c_width = self.width - 2
        self.c_height = self.height - 2
        self.cursor = (0, 0)
        self.select_anchor = None
        self.grab_anchor = None
        self.active_cell = (0, 0)
        self.input_active = False
        self.current_input = ''
        self.text_cursor = 0
        self.current_input_type = SheetWindow.I_TYPE_DISPLAY
        self.entry_color = self.colors.get_color_id("Black", "Green")
        self.grab_start = None
        self.grab_movement = []
        self.grabbing = False

        self.last_column = 0
        self.num_viewable_columns = 0

        self.draw_page()
        ## DEBUG
        self.wait_for_key = False

    def set_input_active(self, input_type):
        self.input_active = True
        self.current_input_type = input_type
        self.active_cell = self.cursor

    def close_input(self):
        self.current_input_type = SheetWindow.I_TYPE_DISPLAY
        self.input_active = False
        self.current_input = ""
        self.cursor = self.active_cell

    def get_column_width(self, col):
        if col in self.column_widths:
            return self.column_widths[col]
        return self.default_col_width

    def get_row_height(self, row):
        if row in self.row_heights:
            return self.row_heights[row]
        return self.default_row_height

    def draw_cell_inner(self, content, row, col, height, width,
                        alignment='r', mod=0, selected=False):
        body = ''
        if isinstance(content, float):
            body = '{:.5f}'.format(content)
            body = body.rstrip('0').rstrip('.')
        elif content is None:
            body = ''
        else:
            body = str(content)

        if body == "nan":
            body = ''

        body_len = len(body)
        if body_len > width - 1:
            body = body[:width - 3] + ".."
        else:
            body = align_text(body, width, alignment=alignment)

        body += '|'

        for i in range(len(body)):
            m = mod
            if mod | curses.A_UNDERLINE:
                m |= curses.A_UNDERLINE
            if selected and i != len(body) - 1:
                m |= curses.A_REVERSE
            self.update_value_body(row, col + i, body[i], m)

    def update_value_body(self, row, col, value, mod):
        if row == 0 or row == self.height - 1 or col == 0 or col == self.width - 1:
            return
        else:
            self.update_value(row, col, value, mod)

    def get_column_offset(self, column):
        offset = 0
        col = self.current_col
        while(col != column):
            offset += self.get_column_width(col)
        return offset

    def get_current_cell(self):
        r, c = self.cursor
        return (r, colval(c))

    def draw_page(self):
        self.draw_sheet()
        self.draw_entry()

    def get_num_viewable_columns(self):
        if self.last_column == self.current_col and self.num_viewable_columns != 0:
            return self.num_viewable_columns
        self.last_column = self.current_col
        cur_col = self.current_col
        cur_offset = 1
        num_cols = 0
        while cur_offset < self.c_width:
            cur_offset += self.get_column_width(cur_col) + 1
            cur_col += 1
            num_cols += 1
        self.num_viewable_columns = num_cols - 1
        return num_cols

    def draw_sheet(self):
        offset = self.get_row_label_offset()
        cur_col = self.current_col
        self.draw_row_labels()
        cols = self.get_num_viewable_columns()
        for i in range(cols):
            self.draw_column(cur_col, offset=offset)
            offset += self.get_column_width(cur_col) + 1
            cur_col += 1

    def get_row_label_offset(self):
        cur_row = str(self.current_row + self.c_height)
        return len(cur_row) + 2

    def draw_row_labels(self):
        width = self.get_row_label_offset()
        row_color = self.colors.get_color_id("Yellow", "Black")
        for r in range(self.c_height):
            cur_row = self.current_row + r
            self.draw_cell_inner(str(cur_row), self.c_row + r + 1, 0, 1, width, alignment='r',
                                 mod=row_color, selected=False)

    def draw_column(self, column, offset=None):
        if offset is None:
            offset = self.get_column_offset(column)

        num_rows = 1
        cur_row = self.current_row
        while num_rows < self.c_height:
            num_rows += self.get_row_height(cur_row)
            cur_row += 1

        col_width = self.get_column_width(column)

        current_visual_row = 0
        col_label_color = self.colors.get_color_id("Cyan", "Black")
        self.draw_cell_inner(colval(column), self.c_row, offset + self.c_col, 1, col_width,
                             alignment='c', mod=col_label_color)

        in_select = False

        for r in range(self.current_row, self.current_row + cur_row):
            mod = 0
            colname = colval(column)
            if self.select_anchor:
                if in_range_2d(self.select_anchor, self.cursor, (r, colname)):
                    mod = self.colors.get_color_id('Green', 'Blue')
                sr, sc = self.select_anchor
            value = self.table.get_cell_value(colname, r)
            row_height = self.get_row_height(r)
            R = self.c_row + current_visual_row + 1
            cell_args = { 'alignment' : 'r' }

            selected = False
            if r == self.cursor[0] and column == self.cursor[1]:
                selected = True
            self.draw_cell_inner(value, R, offset + self.c_col,
                                 row_height, col_width, alignment='r', mod=mod, selected=selected)

            current_visual_row += row_height

    def entry_display_value(self):
        r, c = self.cursor
        row, col = (r, colval(c))
        formula = self.table.get_formula(row, col)
        if formula:
            return formula.get_display_formula() + " (formula)"
        r, c = self.cursor
        v = self.table.get_cell_value(colval(c), r)
        if v is None:
            return ""
        if isinstance(v, float):
            if pd.isna(v):
                return ""
            out = str(v)
            out = out.rstrip('0').rstrip('.')
            return out + " (float)"
        strval = str(v)
        if len(strval) == 0:
            return ""
        return strval + " (str)"

    def draw_entry(self):
        input_line = self.c_height
        self.draw_box(self.c_col, input_line-1, 3, self.c_width, fill=' ')

        beginning = " {} ".format(self.current_input_type)
        text_to_draw = beginning
        if self.current_input_type == SheetWindow.I_TYPE_DISPLAY:
            text_to_draw += self.entry_display_value()
        else:
            text_to_draw += self.current_input
            if len(text_to_draw) > self.c_width - 2:
                text_to_draw = beginning + ".." + self.current_input[-(self.c_width-7):]
        self.draw_text(text_to_draw, input_line, self.c_row + 1, self.entry_color)

    def prerefresh(self):
        '''
            update in between state changes
        '''
        pass

    def expand_grab_vertical(self, amount):
        active, anchor = swap_vertical(self.cursor, self.select_anchor, amount)
        self.cursor = active
        self.select_anchor = anchor
        self._move_cursor_inner(amount, 0)

    def expand_grab_horizontal(self, amount):
        active, anchor = swap_horizontal(self.cursor, self.select_anchor, amount)
        self.cursor = active
        self.select_anchor = anchor
        self._move_cursor_inner(0, amount)

    def _move_cursor_inner(self, rchange, cchange):
        r, c = self.cursor
        newr = r + rchange
        newc = c + cchange
        if newr < 0:
            newr = 0
        if newc < 0:
            newc = 0
        self.update_cursor((newr, newc))

    def move_cursor(self, rchange, cchange):
        self._move_cursor_inner(rchange, cchange)

    def update_cursor(self, new_cursor):
        orow, ocol = self.cursor
        self.cursor = new_cursor
        row, col = new_cursor
        if row < self.current_row:
            self.current_row = row
        if col < self.current_col:
            self.current_col = col

        max_cols = self.get_num_viewable_columns() - 1
        max_rows = self.c_height - 4

        rdiff = row - self.current_row
        if rdiff >= max_rows:
            self.current_row += rdiff - max_rows

        cdiff = col - self.current_col
        if cdiff >= max_cols:
            self.current_col += cdiff - max_cols


    def vertical_scroll(self, amount=1):
        new_amount = self.current_row + amount
        if new_amount < 0:
            new_amount = 0
        self.current_row = new_amount

    def horizontal_scroll(self, amount=1):
        new_amount = self.current_col + amount
        if new_amount < 0:
            new_amount = 0
        self.current_col = new_amount

    def enter_cell_input(self):
        self.set_input_active(SheetWindow.I_TYPE_ENTRY)

    def enter_cmd_input(self):
        self.set_input_active(SheetWindow.I_TYPE_CMD)

    def cancel_input(self):
        self.close_input()

    def enter_value_into_cell(self):
        val = self.current_input
        r, c = self.active_cell
        self.table.set_string_value(r, c, val)

    def enter_cmd(self):
        pass

    def process_input_char(self, charval):
        ctype = self.current_input_type
        
        inp = self.current_input
        cursor_pos = self.text_cursor
        pre_cursor = inp[:cursor_pos]
        post_cursor = inp[cursor_pos:]

        if charval == ESCAPE:
            self.cancel_input()
        elif charval == LEFT:
            ncursor = cursor_pos - 1
            if ncursor >= 0:
                self.text_cursor = ncursor
        elif charval == RIGHT:
            ncursor = cursor_pos + 1
            if ncursor <= len(self.current_input):
                self.text_cursor = ncursor
            pass
        elif charval == BACKSPACE:
            pre_cursor = pre_cursor[:-1]
            self.text_cursor -= 1
            self.current_input = pre_cursor + post_cursor
        elif charval == ENTER:
            if ctype == SheetWindow.I_TYPE_ENTRY:
                self.enter_value_into_cell()
            if ctype == SheetWindow.I_TYPE_CMD:
                self.enter_cmd()
            self.close_input()
        elif ctype == SheetWindow.I_TYPE_ENTRY and charval == CTRL_F:
            # Find
            pass
        else:
            self.current_input = pre_cursor + chr(charval) + post_cursor
            self.text_cursor += 1

    # Grab and drag values to easily expand formulae
    def start_grab(self):
        if not self.select_anchor:
            self.start_select()
        self.grab_start = (self.cursor, self.select_anchor)
        self.grabbing = True

    def end_grab(self):
        (bottom_row, right_col), (top_row, left_col) = normalize_anchor(*self.grab_start)
        cur_row, cur_col = self.cursor

        if cur_col > right_col:
            cols = cur_col - right_col
            for r in range(top_row, bottom_row + 1):
                for c in range(cols):
                    src_col = right_col + c
                    dst_col = src_col + 1
                    form = self.table.get_formula(r, colval(src_col))
                    if form:
                        formula = form.make_child((r, colval(dst_col)))
                        self.table.add_formula(r, colval(dst_col), formula)
                    else:
                        v = self.table.get_cell_value(colval(src_col), r)
                        self.table.set_value(r, colval(dst_col), v)
        self.grabbing = False
        self.grab_start = None
        self.end_select()

    def end_select(self):
        self.select_anchor = None

    def start_select(self):
        self.select_anchor = self.cursor

    def process_char(self, char):
        if self.wait_for_key:
            raise Exception(char)
        if char == ord('!'):
            self.wait_for_key = True
        if self.input_active:
            self.process_input_char(char)
        else:
            if self.grabbing and char == ENTER:
                self.end_grab()
                self.draw_page()
                return
            if char == ord('='):
                self.enter_cell_input()
            if char == ord(':'):
                self.enter_cmd_input()
            if char == CTRL_J:
                self.vertical_scroll(1)
            if char == CTRL_K:
                self.vertical_scroll(-1)
            if char == CTRL_L:
                self.horizontal_scroll(1)
            if char == CTRL_H:
                self.horizontal_scroll(-1)

        ## SELECTION ##
            if char == ord('v'):
                self.start_select()
            if char == ESCAPE:
                if self.select_anchor:
                    self.end_select()

            if char == ord('g') and not self.grabbing:
                self.start_grab()

        ## MOVEMENT ##
            if char == ord('j'):
                self.move_cursor(1, 0)
            if char == ord('k'):
                self.move_cursor(-1, 0)
            if char == ord('l'):
                self.move_cursor(0, 1)
            if char == ord('h'):
                self.move_cursor(0, -1)

            if char == ord('J'):
                self.move_cursor(5, 0)
            if char == ord('K'):
                self.move_cursor(-5, 0)
            if char == ord('L'):
                self.move_cursor(0, 3)
            if char == ord('H'):
                self.move_cursor(0, -3)
            pass
        self.draw_page()


