import re
import pandas as pd;

from .formula import Formula

def read_token(token):
    row_lock = False
    col_lock = False
    if token.startswith('$'):
        col_lock = True
        token = token[1:]

    if '$' in token:
        row_lock = True

    col_re = r'[A-Z]+'
    m = re.search(col_re, token)
    col = get_col(m.group(0))

    row_re = r'[0-9]+'
    m = re.search(row_re, token)
    row = int(m.group(0))
    return row, row_lock, col, col_lock

class TableCell:

    def __init__(self, value=None):
        self._value = value;
        self.needs_refresh = True

    def refresh(self):
        self.needs_refresh = False

    @property
    def value(self):
        if (self.needs_refresh):
            self.refresh()
        return self._value

    def set_value(self, new_value):
        self._value = new_value

    def set_needs_update(self):
        self.needs_refresh = True

    def read_formla(self, formula):
        pass

class TableData:
    '''
        This will contain data for a given row
        Rows/Column data will be stored in a dictionary

        There will be different types of data:
            - Raw - Values entered directly into the spreadsheet
            - Calculated - Values derived from raw values
    '''

    def __init__(self, dataframe=None):
        if dataframe is None:
            self.data = pd.DataFrame()
        else:
            self.data = dataframe
        self.formulae = {}

    def get_cell_value(self, row, col, f=False):
        if self._has_formula(row, col):
            raise Exception("FORM")
            return self.formulae[row][col].get_value()
        return self.data.get(row, {}).get(col, None)

    def get_cell_range(self, start_pos, end_pos):
        output = []
        rows = sorted([start_pos[0], end_pos[0]])
        cols = sorted([start_pos[1], end_pos[1]])
        for row in range(rows[0], rows[1]+1):
            for col in range(cols[0], cols[1]+1):
                val = self.get_cell_value(row, col)
                output.append(val)
        return output

    def _has_formula(self, row, col):
        if row in self.formulae:
            raise Exception(self.formulae)
            return col in self.formulae[row]
        return False

    def add_formula(self, row, col, formula):
        new_formula = Formula([row, col], formula, self)
        if row not in self.formulae:
            self.formulae[row] = {}
        self.formulae[row][col] = new_formula
        val = new_formula.get_value()
        self.set_value(row, col, val)

    def set_value(self, row, col, value):
        self.data.at[row, col] = value




