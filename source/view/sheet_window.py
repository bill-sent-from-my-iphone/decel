import curses
import numpy as np
import pandas as pd
import copy
import re

from .utils.input import BasicInput
from .utils.general import fix_text_to_width, align_text, min_max, iterate_range_2d
from .window import Window
from data.table_data import TableData
from data.formula import colint, colval, has_tokens, Formula
from .popup import Popup, InputPopup
from .utils.keys import *


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

def make_token(cell):
    return colval(cell[1]) + str(cell[0])

class SheetWindow(Window):

    I_TYPE_DISPLAY = "@"
    I_TYPE_ENTRY = "="
    I_TYPE_CMD = ":"
    I_TYPE_MOVE = ">"

    def __init__(self, *args, **kwargs):
        self.default_col_width = 9
        self.default_row_height = 1
        self.table = kwargs.get('table', TableData())
        if 'table' in kwargs:
            del kwargs['table']
        super().__init__(*args, **kwargs)
        #self.table.load_csv('example_file.csv')
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
        self.finding_cell = False
        self.input_active = False
        self.yank_vals = {}
        self.teleporting = False

        self.input = BasicInput(on_confirm=self.confirm_input, on_cancel=self.cancel_input)
        self.tmp_message = ''


        self.current_input_type = SheetWindow.I_TYPE_DISPLAY
        self.entry_color = self.colors.get_color_id("Black", "Green")
        self.grab_start = None
        self.grab_movement = []
        self.grabbing = False
        self.current_motion = ''

        self.commands = {}

        self.last_column = 0
        self.num_viewable_columns = 0
        self.row_jump_size = 5
        self.col_jump_size = 3

        self.draw_page()
        ## DEBUG
        self.wait_for_key = False

    def force_refresh(self):
        self.table.force_update()

    def load_config(self, config):
        self.default_col_width = config.default_column_width()
        self.row_jump_size = config.row_jump_size()
        self.col_jump_size = config.col_jump_size()
        self.commands = config.get_commands()
        self.draw_page()

    def set_input_active(self, input_type):
        self.input_active = True
        self.current_input_type = input_type
        self.active_cell = self.cursor

        self.input.clear()


    def close_input(self):
        if self.current_input_type == SheetWindow.I_TYPE_ENTRY:
            self.cursor = self.active_cell
        self.current_input_type = SheetWindow.I_TYPE_DISPLAY
        self.input_active = False
        self.input.clear()

    def get_input(self):
        return self.input.text

    def get_column_width(self, col):
        if col in self.column_widths:
            return self.column_widths[col]
        return self.default_col_width

    def get_row_height(self, row):
        if row in self.row_heights:
            return self.row_heights[row]
        return self.default_row_height

    def change_column_size(self, size=None, col=None, negative=False):
        if not col:
            col_start = self.cursor[1]
        if not size:
            size = self.get_motion_size()
        cols = [col_start]
        if self.select_anchor:
            cols = []
            ac = self.select_anchor[1]
            cs = [ac, col_start]
            mn = min(cs)
            mx = max(cs)
            cols = [x for x in range(mn, mx+1)]

            
        if negative:
            size = -size

        for col in cols:
            w = self.column_widths.get(col, self.default_col_width)
            nsize = w + size
            MIN_SIZE = 3
            if nsize < MIN_SIZE:
                nsize = MIN_SIZE
            self.num_viewable_columns = 0
            self.column_widths[col] = nsize

    def change_row_size(self, size, row=None):
        if not row:
            row = self.cursor[0]
        h = self.row_heights.get(row, self.default_row_height)
        self.row_heights[row] = h + size

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
            body = body[:width - 2] + ".."
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
        self.table.trigger_update()
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
                mod = self.colors.get_color_id('White', 'Red')
            if self.finding_cell and r == self.active_cell[0] and column == self.active_cell[1]:
                mod = self.colors.get_color_id('Magenta', 'Yellow')
            self.draw_cell_inner(value, R, offset + self.c_col,
                                 row_height, col_width, alignment='r', mod=mod, selected=selected)

            current_visual_row += row_height

    def set_tmp_message(self, val):
        self.tmp_message = val

    def entry_display_value(self):
        tmp = self.tmp_message
        if tmp:
            self.set_tmp_message('')
            return tmp
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
            text_to_draw += self.get_input()
            if len(text_to_draw) > self.c_width - 2:
                text_to_draw = beginning + ".." + self.get_input()[-(self.c_width-7):]
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
        self.update_cursor((newr, newc))

    def move_cursor(self, rchange, cchange):
        if self.teleporting:
            self.teleport(rchange, cchange)
        else:
            self._move_cursor_inner(rchange, cchange)

    def _find_until(self, start, vertical, positive, radius=2, max_iter=1000):
        amount = 1 if positive else -1
        change = (amount, 0) if vertical else (0, amount)
        offsets = [x for x in range(-radius, radius+1)]
        if vertical:
            pairs = [(0, i) for i in offsets]
        else:
            pairs = [(i, 0) for i in offsets]

        def real_cell_has_value(start, offset):
            sr, sc = start
            mr, mc = offset
            r = sr + mr
            c = sc + mc
            return self.table.has_value(r, colval(c))

        r, c = start
        dr, dc = change

        start_pairs = {}
        for p in pairs:
            start_pairs[p] = real_cell_has_value((r + dr, c + dc), p)

        found = False
        for i in range(max_iter):
            r += dr
            c += dc
            place = (r, c)
            for offset in pairs:
                initial_val = start_pairs[offset]
                new_val = real_cell_has_value(place, offset)
                if initial_val != new_val:
                    found = True
                    break
            if found:
                break
        if found:
            return (r, c)
        return None

    def teleport(self, rchange, cchange):
        ncursor = self.cursor
        if rchange != 0:
            if rchange > 0:
                ncursor = self._find_until(self.cursor, True, True)
            else:
                ncursor = self._find_until(self.cursor, True, False)
            pass
        if cchange != 0:
            if cchange > 0:
                ncursor = self._find_until(self.cursor, False, True)
            else:
                ncursor = self._find_until(self.cursor, False, False)
        self.teleporting = False
        if ncursor:
            self.update_cursor(ncursor)

    def update_cursor(self, new_cursor):
        orow, ocol = self.cursor
        nr, nc = new_cursor
        if nr < 0:
            nr = 0
        if nc < 0:
            nc = 0
        self.cursor = (nr, nc)
        if nr < self.current_row:
            self.current_row = nr
        if nc < self.current_col:
            self.current_col = nc

        max_cols = self.get_num_viewable_columns() - 1
        max_rows = self.c_height - 4

        rdiff = nr - self.current_row
        if rdiff >= max_rows:
            self.current_row += rdiff - max_rows

        cdiff = nc - self.current_col
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

    def enter_move_input(self):
        self.set_input_active(SheetWindow.I_TYPE_MOVE)

    def cancel_input(self):
        self.close_input()

    def confirm_input(self):
        itype = self.current_input_type
        if self.current_input_type == SheetWindow.I_TYPE_ENTRY:
            self.enter_value_into_cell()
        if self.current_input_type == SheetWindow.I_TYPE_CMD:
            self.enter_cmd()
        if self.current_input_type == SheetWindow.I_TYPE_MOVE:
            self.enter_movement_input()
        self.close_input()

    def enter_value_into_cell(self):
        val = self.get_input()
        r, c = self.active_cell
        self.table.set_string_value(r, c, val)

    def enter_movement_input(self):
        inp = self.get_input()
        r, c = self.cursor
        row = re.findall(r'[0-9]+', inp)
        if row:
            r = int(row[0])
        col = re.findall(r'[a-zA-Z]+', inp)
        if col:
            c = colint(col[0].upper())
        self.update_cursor((r, c))

    def try_save_file(self):
        if not self.table.has_filename():
            self.get_filename_input()
            return
        self.save_file()

    def enter_cmd(self):
        inp = self.get_input()
        if inp == 'w':
            self.try_save_file()
        self.start_command(inp)

    def save_file(self):
        fname = self.table.filename()
        try:
            self.table.save()
            self.set_tmp_message('Saved file: {}'.format(fname))
        except:
            self.set_tmp_message('Error saving file: {}'.format(fname))

    def confirm_filename_and_save(self, name):
        self.table.set_filename(name)
        self.save_file()

    def get_filename_input(self):
        p = InputPopup("Error", "You must specify a filename:", self.confirm_filename_and_save, None, parent=self, colors=self.colors)
        self.add_child(p)
        self.set_active(p)

    def transfer_cell(self, start, dest):
        sr, sc = start
        dr, dc = dest
        form = self.table.get_formula(sr, sc)
        if form:
            formula = form.make_child(dest)
            self.table.add_formula(dr, dc, formula)
        else:
            v = self.table.get_cell_value(sc, sr)
            self.table.set_value(dr, dc, v)

    def clear_value(self):
        if self.select_anchor:
            r1, c1 = self.cursor
            r2, c2 = self.select_anchor
            rows = [r1, r2]
            cols = [c1, c2]
            rm = min(rows)
            rM = max(rows)
            cm = min(cols)
            cM = max(cols)
            for r in range(rm, rM+1):
                for c in range(cm, cM+1):
                    self.table.set_value(r, colval(c), None)
            self.end_select()
        else:
            r, c = self.cursor
            self.table.set_value(r, colval(c), None)

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
                    source = (r, colval(src_col))
                    dest = (r, colval(dst_col))
                    self.transfer_cell(source, dest)
            right_col = cur_col

        if cur_col < left_col:
            cols = left_col - cur_col
            for r in range(top_row, bottom_row + 1):
                for c in range(cols):
                    src_col = left_col - c
                    dst_col = src_col - 1
                    source = (r, colval(src_col))
                    dest = (r, colval(dst_col))
                    self.transfer_cell(source, dest)
            left_col = cur_col

        # Modify Cols

        if cur_row > bottom_row:
            rows = cur_row - bottom_row
            for c in range(left_col, right_col + 1):
                column = colval(c)
                for r in range(rows):
                    src_row = bottom_row + r
                    dst_row = src_row + 1
                    source = (src_row, column)
                    dest = (dst_row, column)
                    self.transfer_cell(source, dest)

        if cur_row < top_row:
            rows = bottom_row - cur_row
            for c in range(left_col, right_col + 1):
                column = colval(c)
                for r in range(rows):
                    src_row = top_row - r
                    dst_row = src_row - 1
                    source = (src_row, column)
                    dest = (dst_row, column)
                    self.transfer_cell(source, dest)

        self.grabbing = False
        self.grab_start = None
        self.end_select()
        self.force_refresh()

    def end_select(self):
        self.select_anchor = None

    def start_select(self):
        self.select_anchor = self.cursor

    def start_command(self, cmd):
        command = self.commands.get(cmd, None)
        if command:
            for k in command:
                self.process_char(k)

    def get_yank_value(self, r, c):
        '''
            Integer value for r, c
        '''
        formula = self.table.get_formula(r, colval(c))
        if formula:
            return formula
        else:
            return self.table.get_cell_value(colval(c), r)

    def yank(self):
        yank_vals = {}
        start = None
        if self.select_anchor:
            for r, c in iterate_range_2d(self.select_anchor, self.cursor):
                if not start:
                    start = (r, c)
                coords = (r, c)
                mr = r - start[0]
                mc = c - start[1]
                mod_coords = (mr, mc)
                yank_vals[mod_coords] = self.get_yank_value(r, c)
            self.yank_vals = yank_vals
            self.end_select()
        else:
            self.yank_vals = { (0, 0) : self.get_yank_value(*self.cursor)}

    def paste(self):
        row, col = self.cursor
        for r, c in self.yank_vals:
            dst_row = row + r
            dst_col = colval(col + c)
            val = self.yank_vals[(r,c)]
            if isinstance(val, Formula):
                child = val.make_child((dst_row, dst_col))
                self.table.add_formula(dst_row, dst_col, child)
            else:
                self.table.set_value(dst_row, dst_col, val)

    def get_motion_size(self, base_val=1):
        if not self.current_motion:
            return base_val
        out = int(self.current_motion) * base_val
        self.current_motion = ''
        return out

    def start_teleport(self):
        self.teleporting = True

    def start_secondary_select(self):
        self.active_cell = self.cursor
        self.finding_cell = True

    def confirm_secondary_select(self):
        if self.select_anchor:
            anchor = self.select_anchor
            cursor = self.cursor
            cursor, anchor = swap_vertical(cursor, anchor, 1)
            cursor, anchor = swap_horizontal(cursor, anchor, 1)
            token = make_token(anchor) + ':' + make_token(cursor)
        else:
            token = make_token(self.cursor)
        self.input.process_text(token)
        self.end_secondary_select()

    def cancel_secondary_select(self):
        self.end_secondary_select()

    def end_secondary_select(self):
        self.cursor = self.active_cell
        self.finding_cell = False
        self.end_select()

    def input_process_char(self, char):
        if self.current_input_type == SheetWindow.I_TYPE_ENTRY:
            if char == CTRL_F:
                self.start_secondary_select()
                return
        self.input.process_char(char)

    def process_char(self, char):
        if self.wait_for_key:
            raise Exception(char)
        if char == ord('!'):
            self.wait_for_key = True
        if self.input_active and not self.finding_cell:
            self.input_process_char(char)
        else:

            if not self.finding_cell:

                if self.grabbing and char == ENTER:
                    self.end_grab()
                    self.draw_page()
                    return
                if char == ord('='):
                    self.enter_cell_input()
                if char == ord(':'):
                    self.enter_cmd_input()

                if char == ord('g') and not self.grabbing:
                    self.start_grab()

                if char == ord('x'):
                    self.clear_value()

                if char == ord('y'):
                    self.yank()
                if char == ord('p'):
                    self.paste()

            if self.finding_cell:
                if char == ENTER:
                    self.confirm_secondary_select()
                    self.draw_page()
                    return

            if char == CTRL_J:
                self.vertical_scroll(1)
            if char == CTRL_K:
                self.vertical_scroll(-1)
            if char == CTRL_L:
                self.horizontal_scroll(1)
            if char == CTRL_H:
                self.horizontal_scroll(-1)

            if chr(char) in '0123456789':
                self.current_motion += chr(char)

        ## SELECTION ##
            if char == ord('v'):
                self.start_select()

            if char == ESCAPE:
                if self.select_anchor:
                    self.end_select()
                elif self.finding_cell:
                    self.cancel_secondary_select()
                if self.current_motion:
                    self.current_motion = ''
                if self.grabbing:
                    self.grabbing = False

            if char == ord('>'):
                self.change_column_size()
            if char == ord('<'):
                self.change_column_size(negative=True)
            if char == ord('R'):
                self.force_refresh()


        ## MOVEMENT ##
            if char == ord('s'):
                self.start_teleport()
            if char == ord('m'):
                self.enter_move_input()
            if char == ord('j'):
                s = self.get_motion_size()
                self.move_cursor(s, 0)
            if char == ord('k'):
                s = self.get_motion_size()
                self.move_cursor(-s, 0)
            if char == ord('l'):
                s = self.get_motion_size()
                self.move_cursor(0, s)
            if char == ord('h'):
                s = self.get_motion_size()
                self.move_cursor(0, -s)

            if char == ord('J'):
                s = self.row_jump_size
                self.move_cursor(s, 0)
            if char == ord('K'):
                s = self.row_jump_size
                self.move_cursor(-s, 0)
            if char == ord('L'):
                s = self.col_jump_size
                self.move_cursor(0, s)
            if char == ord('H'):
                s = self.col_jump_size
                self.move_cursor(0, -s)
            pass
        self.draw_page()


