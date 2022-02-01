import curses

from .utils import fix_text_to_width, align_text
from .window import Window
from data.table_data import TableData
from data.formula import colint, colval

class SheetWindow(Window):

    def __init__(self, *args, **kwargs):
        self.default_col_width = 8
        self.default_row_height = 1
        self.table = kwargs.get('table', TableData())
        del kwargs['table']
        super().__init__(*args, **kwargs)
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
        self.draw_page()

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
            body = '{:.3f}'.format(content)
        elif content is None:
            body = ''
        else:
            body = str(content)

        body_len = len(body)
        if body_len > width - 1:
            body = body[:width - 3] + ".."
        else:
            body = align_text(body, width)

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

    def draw_page(self):
        offset = self.get_row_label_offset()
        cur_col = self.current_col
        self.draw_row_labels()
        while offset < self.width:
            self.draw_column(cur_col, offset=offset)
            offset += self.get_column_width(self.current_col) + 1
            cur_col += 1

    def get_row_label_offset(self):
        cur_row = str(self.current_row)
        return len(cur_row) + 2

    def draw_row_labels(self):
        width = self.get_row_label_offset()
        row_color = self.colors.get_color_id("Blue", "White")
        for r in range(self.c_height):
            cur_row = self.current_row + r
            self.draw_cell_inner(str(cur_row), self.c_row + r + 1, 0, 1, width, alignment='l',
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
        self.draw_cell_inner(colval(column+1), self.c_row, offset + self.c_col, 1, col_width,
                             alignment='c', mod=col_label_color)

        for r in range(self.current_row, self.current_row + cur_row):
            value = self.table.get_cell_value(r, column)
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

    def draw_cell(self, row, col):
        val = self.table.get_cell_value(row, col)
        raise Exception(val)
        pass

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
        self.cursor = (newr, newc)

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

    def process_char(self, char):
        if char == 10: # ctrl J
            self.vertical_scroll(1)
        if char == 11: # ctrl K
            self.vertical_scroll(-1)
        if char == 12: # ctrl L
            self.horizontal_scroll(1)
        if char == 263: # ctrl H
            self.horizontal_scroll(-1)
        if char == ord('j'):
            self.move_cursor(1, 0)
        if char == ord('k'):
            self.move_cursor(-1, 0)
        if char == ord('l'):
            self.move_cursor(0, 1)
        if char == ord('h'):
            self.move_cursor(0, -1)
        pass
        self.draw_page()


