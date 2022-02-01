import re

class FormulaDecipherException(Exception):

    def __init__(self, token):
        msg = "Error deciphering token: {}".format(token)
        super().__init__(msg)

def letter_val(char):
    return ord(char) - 64

def char_val(intval):
    return chr(intval + 64)

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

def colval(val):
    cur_val = val + 1
    output = ""
    while cur_val > 0:
        m = cur_val % 26
        cur_val -= m
        output = char_val(m) + output
    return output

class IFormula:

    def __init__(self, cell):
        self.position = cell

    def _origin_row(self):
        return self.position[0]

    def _origin_col(self):
        return self.position[1]


    def get_value_for_cell(self, row, col):
        return None
        
    def get_value(self):
        return self.get_value_for_cell((self._origin_row(), self._origin_col()))


column_re = r'\$?[A-Z]+'
row_re = r'\$?[0-9]+'
cell_re = column_re + row_re
token_re = cell_re + '(?::' + cell_re + ')?'


def has_tokens(value):
    ms = re.findall(token_re, value)
    return len(ms) > 0

class Formula(IFormula):
    '''
        position - [row, col] of formula (eg [1, "AB"])
        formula - the formula (eg $A:B23:$100)
    '''
    def __init__(self, cell, formula, table):
        super().__init__(cell)
        self.table = table
        self.formula = formula
        self.formula_dict = {}
        self.range_dict = {}
        self._decipher()

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
            row = token[len(col):]

        if col is None or row is None:
            raise FormulaDecipherToken(token)

        get_row = None
        get_col = None

        if row_lock:
            get_row = lambda r_in: row
        else:
            get_row = lambda r_in: r_in + (row - self._origin_row())

        if col_lock:
            get_col = lambda c_in: colint(col)
        else:
            get_col = lambda c_in: colint(c_in) + (colint(col) - colint(self._origin_col()))

        # Remove 1 because display is 1 index but data is 0
        row = int(row) - 1

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

    def get_value_for_cell(self, cell):
        row, col = cell
        tokens_to_replace = sorted(self.formula_dict.keys(), key=len, reverse=True)
        tokens = {}
        for token in tokens_to_replace:
            row_mod, col_mod = self.formula_dict[token](*cell)
            new_row = row + row_mod
            new_col = colval(colint(col) + col_mod)
            raise Exception(cell, (new_row, new_col), (row_mod, col_mod))
            if self.range_dict.get(token, False):
                tokens[token] = self.table.get_cell_range(row_mod, col_mod)
            else:
                tokens[token] = self.table.get_cell_value(new_row, new_col)

        raise Exception(tokens)

        token_index = 0
        local_vars = {}
        tmp_formula = self.formula
        for token in tokens:
            token_index += 1
            varname = "DECEL_VAR_" + colval(token_index)
            local_vars[varname] = tokens[token]
            tmp_formula = tmp_formula.replace(token, varname)

        x = eval(tmp_formula, {}, local_vars)
        raise Exception(tmp_formula, local_vars)
        raise Exception(x)
        return x

class ChildFormula(IFormula):

    def __init__(self, formula, cell):
        super().__init__()
        self.formula = formula

    def get_value_for_cell(row, cell):
        return self.formula.get_value_for_cell(cell)


