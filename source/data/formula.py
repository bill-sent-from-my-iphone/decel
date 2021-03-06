import re

from .script_loader import get_loader

class FormulaDecipherException(Exception):

    def __init__(self, token):
        msg = "Error deciphering token: {}".format(token)
        super().__init__(msg)

def letter_val(char):
    return ord(char) - 64

def char_val(intval):
    return chr(intval + 64)



letter_re = r'[A-Z]+'
def split_token(token):
    col = re.match(letter_re, token).group()
    row = token[len(col):]
    return (int(row), col)

column_values = {}

def colint(col_text):
    if col_text in column_values:
        return column_values[col_text]
    length = len(col_text)
    value = 0
    for power in range(length):
        digit = col_text[length-power-1]
        value += letter_val(digit) * pow(26, power)
    return value - 1

def ocolval(val):
    cur_val = val + 1
    output = ""
    while cur_val > 0:
        m = cur_val % 26
        cur_val -= m
        output = char_val(m) + output
    return output

def colval(num):
    numeric = num  % 26
    letter = chr(65 + numeric)
    num2 = int(num / 26)
    if num2 > 0:
        return colval(num2 - 1) + letter
    return letter


column_re = r'\$?[A-Z]+'
row_re = r'\$?[0-9]+'
cell_re = column_re + row_re
token_re = cell_re + '(?::' + cell_re + ')?'



def has_tokens(value):
    ms = re.findall(token_re, value)
    return len(ms) > 0

class Formula:
    '''
        position - [row, col] of formula (eg [1, "AB"])
        formula - the formula (eg $A:B23:$100)
    '''
    def __init__(self, cell, formula, table):
        self.position = cell
        self.table = table
        self.formula = formula
        self.formula_dict = {}
        self.range_dict = {}
        self._decipher()

    def root(self):
        return self

    def _origin_row(self):
        return self.position[0]

    def _origin_col(self):
        return self.position[1]

    def get_value(self):
        return self.get_value_for_cell((self._origin_row(), self._origin_col()))

    def get_dependent_tokens(self):
        tokens = self._get_dependent_tokens(self.position)
        output = []
        for t in tokens:
            if ':' in t:
                t1, t2 = t.split(':')
                output.extend(self.iterate_range(t1, t2))
            else:
                row, col = split_token(t)
                output.append((row, col))
        return output

    def make_child(self, cell):
        child = ChildFormula(self.root(), cell)
        return child

    def get_display_formula(self):
        return self.formula

    def _decipher(self):
        tokens = re.findall(token_re, self.formula)
        self._load_dict(tokens)

    def _get_cell(self, token):
        col_lock = False
        row_lock = False
        col = None
        row = None

        if token.startswith('$'):
            col_lock = True
            token = token[1:]

        if '$' in token:
            row_lock = True
            col, row = token.split('$')

        if col is None: # not split
            col_re = r'[A-Z]+'
            col = re.match(col_re, token).group()
            row = int(token[len(col):])

        if col is None or row is None:
            raise FormulaDecipherToken(token)

        get_row = None
        get_col = None

        ls = (row_lock, col_lock)
        p = (row, col)

        if row_lock:
            get_row = lambda r_in: row
        else:
            def calc_row(r_in):
                diff = row - self._origin_row()
                out = r_in + (row - self._origin_row())
                return out
            get_row = calc_row

        if col_lock:
            get_col = lambda c_in: colint(col)
        else:
            get_col = lambda c_in: colint(c_in) + (colint(col) - colint(self._origin_col()))

        # Remove 1 because display is 1 index but data is 0
        return lambda R, C: (get_row(R), get_col(C))

    def _generate_token_formula(self, token):
        if ':' in token:
            start, end = token.split(':')
            get_start_cell = self._get_cell(start)
            get_end_cell = self._get_cell(end)
            return lambda r_in, c_in: (get_start_cell(r_in, c_in), get_end_cell(r_in, c_in))
        else:
            get_cell = self._get_cell(token)
            return get_cell

    def _load_dict(self, tokens):
        f_dict = {}
        range_dict = {}
        for token in tokens:
            formula = self._generate_token_formula(token)
            f_dict[token] = formula
            if ':' in token:
                range_dict[token] = True
        self.formula_dict = f_dict
        self.range_dict = range_dict

    def get_dependent_coordinates(self, cell):
        row, col = cell
        tokens_to_replace = sorted(self.formula_dict.keys(), key=len, reverse=True)
        cells = []
        for token in tokens_to_replace:
            a, b = self.formula_dict[token](*cell)
            if self.range_dict.get(token, False):
                cells.extend(self.table.get_cell_range_coords(a, b))
            else:
                cells.append((a, colval(b)))
        return cells

    def _get_dependent_tokens(self, cell):
        row, col = cell
        tokens_to_replace = sorted(self.formula_dict.keys(), key=len, reverse=True)
        tokens = {}
        for token in tokens_to_replace:
            a, b = self.formula_dict[token](*cell)

            if self.range_dict.get(token, False):
                tokens[token] = self.table.get_cell_range(a, b)
            else:
                t_col = colval(b)
                tokens[token] = self.table.get_cell_value(t_col, a)
        return tokens

    def iterate_range(self, cellA, cellB):
        r1, c1 = split_token(cellA)
        r2, c2 = split_token(cellB)
        rows = [r1, r2]
        cols = [colint(c1), colint(c2)]
        rowmin = min(rows)
        rowmax = max(rows)
        colmin = min(cols)
        colmax = max(cols)
        output = []
        for r in range(rowmin, rowmax+1):
            for c in range(colmin, colmax+1):
                col = colval(c)
                output.append((r, col))
        return output

    def get_value_for_cell(self, cell):
        row, col = cell
        tokens = self._get_dependent_tokens(cell)

        token_index = 0
        local_vars = get_loader().get_vars()
        tmp_formula = self.formula
        for token in tokens:
            token_index += 1
            varname = "DECEL_VAR_" + colval(token_index)
            local_vars[varname] = tokens[token]
            tmp_formula = tmp_formula.replace(token, varname)
        try:
            val = eval(tmp_formula, {}, local_vars)
            return val
        except:
            val = "Formula Error: ({})".format(tmp_formula)
            return val

def adjust_single_token(token, cell):
    c_row, c_col = cell
    my_re = r'(\$?[A-Z]+)(\$?[0-9]+)'
    row, col = re.findall(my_re, token)[0]
    output = ''
    if row.startswith('$'):
        output += '$'
    output += colval(c_col)
    if col.startswith('$'):
        output += '$'
    output += str(c_row)
    return output

def adjust_token(token, formula, cell_s):
    if ':' in token:
        start, end = cell_s
        sr, sc = start
        er, ec = end

        one, two = token.split(':')
        s_token = adjust_single_token(one, start)
        e_token = adjust_single_token(two, end)
        return s_token + ':' + e_token
    else:
        return adjust_single_token(token, cell_s)

class ChildFormula(Formula):

    def __init__(self, parent, cell):
        super().__init__(cell, parent.formula, parent.table)
        self.position = cell
        self.parent = parent
        self.display_formula = None

    def get_display_formula(self):
        formula = self.parent.formula
        if not self.display_formula:
            tokens_to_replace = sorted(self.parent.formula_dict.keys(), key=len, reverse=True)
            tokens = {}
            for token in tokens_to_replace:
                a, b = self.root().formula_dict[token](*self.position)
                new_token = adjust_token(token, formula, (a, b))
                tokens[token] = new_token
            for token in tokens:
                formula = formula.replace(token, tokens[token])
            self.display_formula = formula
        return self.display_formula

    def root(self):
        return self.parent.root()

    def get_value_for_cell(self, cell):
        return self.parent.get_value_for_cell(cell)

    def get_dependent_coordinates(self, cell):
        coords = self.parent.get_dependent_coordinates(cell)
        return coords


colval(26)
