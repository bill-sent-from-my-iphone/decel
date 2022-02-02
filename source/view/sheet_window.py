import curses
import numpy as np

from .utils import fix_text_to_width, align_text
from .window import Window
from data.table_data import TableData
from data.formula import colint, colval, has_tokens


CTRL_J = 10
CTRL_K = 11
CTRL_L = 12
CTRL_H = 263
ENTER = CTRL_J
BACKSPACE = 127


class SheetWindow(Window):

    I_TYPE_DISPLAY = "@"
    I_TYPE_ENTRY = "="
    I_TYPE_CMD = "/"

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
        self.active_cell = (0, 0)
        self.input_active = False
        self.current_input = ''
        self.current_input_type = SheetWindow.I_TYPE_DISPLAY
        self.entry_color = self.colors.get_color_id("Black", "Green")
        self.draw_page()

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

    def draw_sheet(self):
        offset = self.get_row_label_offset()
        cur_col = self.current_col
        self.draw_row_labels()
        while offset < self.width:
            self.draw_column(cur_col, offset=offset)
            offset += self.get_column_width(self.current_col) + 1
            cur_col += 1

    def get_row_label_offset(self):
        cur_row = str(self.current_row + self.c_height)
        return len(cur_row) + 2

    def draw_row_labels(self):
        width = self.get_row_label_offset()
        row_color = self.colors.get_color_id("Blue", "White")
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

        for r in range(self.current_row, self.current_row + cur_row):
            colname = colval(column)
            value = self.table.get_cell_value(colname, r)
            row_height = self.get_row_height(r)
            R = self.c_row + current_visual_row + 1
            cell_args = { 'alignment' : 'r' }

            mod = 0
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
            return formula.get_display_formula()
        r, c = self.cursor
        v = self.table.get_cell_value(colval(c), r)
        if v is None:
            return ""
        if isinstance(v, float):
            out = str(v)
            out = out.rstrip('0').rstrip('.')
            return out
        return str(v)

    def draw_entry(self):
        self.draw_box(self.c_col, self.c_height-2, 3, self.c_width, fill=' ')

        beginning = " {} ".format(self.current_input_type)
        text_to_draw = beginning
        if self.current_input_type == SheetWindow.I_TYPE_DISPLAY:
            text_to_draw += self.entry_display_value()
        else:
            text_to_draw += self.current_input
            if len(text_to_draw) > self.c_width - 2:
                text_to_draw = beginning + ".." + self.current_input[-(self.c_width-7):]
        self.draw_text(text_to_draw, self.c_height - 1, self.c_row + 1, self.entry_color)

    def prerefresh(self):
        '''
            update in between state changes
        '''
        pass

    def move_cursor(self, rchange, cchange):
        r, c = self.cursor
        newr = r + rchange
        newc = c + cchange
        if newr < 0:
            newr = 0
        if newc < 0:
            newc = 0
        self.update_cursor((newr, newc))

    def update_cursor(self, new_cursor):
        self.cursor = new_cursor
        row, col = new_cursor
        if row < self.current_row:
            self.current_row = row
        if col < self.current_col:
            self.current_col = col

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

    def enter_value_into_cell(self):
        val = self.current_input
        r, c = self.active_cell
        self.table.set_string_value(r, c, val)

    def process_input_char(self, charval):
        if charval == BACKSPACE:
            self.current_input = self.current_input[:-1]
        elif charval == ENTER:
            ctype = self.current_input_type
            if ctype == SheetWindow.I_TYPE_ENTRY:
                self.enter_value_into_cell()
            self.close_input()
        else:
            self.current_input += chr(charval)

    def process_char(self, char):
        if self.input_active:
            self.process_input_char(char)
        else:
            if char == ord('='):
                self.enter_cell_input()
            if char == CTRL_J:
                self.vertical_scroll(1)
            if char == CTRL_K:
                self.vertical_scroll(-1)
            if char == CTRL_L:
                self.horizontal_scroll(1)
            if char == CTRL_H:
                self.horizontal_scroll(-1)

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


