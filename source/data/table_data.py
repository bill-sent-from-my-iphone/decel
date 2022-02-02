import re
import os
import pandas as pd;
import csv

from .formula import Formula, colval, has_tokens

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
        self.dependencies = {}

    def clear_data(self):
        self.data = pd.DataFrame()
        self.formulae = {}
        self.dependencies = {}

    def get_cell_value(self, row, col, f=False):
        if self._has_formula(row, col):
            return self.formulae[row][col].get_value()
        return self.data.get(row, {}).get(col, None)

    def get_cell_range(self, start_pos, end_pos):
        output = []
        rows = sorted([start_pos[0], end_pos[0]])
        cols = sorted([start_pos[1], end_pos[1]])
        for row in range(rows[0], rows[1]+1):
            for col in range(cols[0], cols[1]+1):
                val = self.get_cell_value(colval(col), row)
                output.append(val)
        return output

    def get_formula(self, row, col):
        if self._has_formula(row, col):
            return self.formulae[row][col]
        return None

    def _has_formula(self, row, col):
        if row in self.formulae:
            return col in self.formulae[row]
        return False

    def update_value(self, row, col):
        if self._has_formula(row, col):
            val = self.formulae[row][col].get_value()
            self.data.at[row, col] = val


    def add_dependency(self, lead_token, dependent_token):
        if lead_token not in self.dependencies:
            self.dependencies[lead_token] = {}
        self.dependencies[lead_token][dependent_token] = True

    def add_dependencies(self, formula):
        tokens = formula.get_dependent_tokens()
        f_pos = formula.position
        for token in tokens:
            self.add_dependency(token, f_pos)

    def get_dependencies(self, row, col):
        return self.dependencies.get((row, col), {}).keys()

    def token_changed(self, cell):
        # TODO: Optimize this.
        # Look at which tokens have more/fewer dependencies and don't
        # duplicate cells that are dependent on something that is going to change
        # anyway
        # eg: A0 = 1
        #     A1 = A0
        #     A2 = A0 + A1
        # If the user updates A0, we would want to update A1 first, because updating
        # A2 would calculate it with a false A1, then when A1 changes it would be
        # recalculated

        for d_row, d_col in self.dependencies.get(cell, {}):
            self.update_value(d_row, d_col)

    def add_formula(self, row, col, formula):
        new_formula = Formula((row, col), formula, self)
        if row not in self.formulae:
            self.formulae[row] = {}
        self.formulae[row][col] = new_formula
        val = new_formula.get_value()
        self.set_value(row, col, val)
        self.add_dependencies(new_formula)
        self.token_changed((row, col))

    def set_string_value(self, r, c, val):
        col = colval(c)
        if has_tokens(val):
            self.add_formula(r, col, val)
        else:
            try:
                value = eval(val)
                self.set_value(r, col, value)
            except:
                self.set_value(r, col, val)

    def set_value(self, row, col, value):
        self.data.at[row, col] = value
        self.token_changed((row, col))

    def load_csv(self, filepath):
        body = []

        self.clear_data()
        df = pd.DataFrame()
        self.data = df
        with open(filepath) as csvfile:
            content = csv.reader(csvfile, delimiter=' ', quotechar='|')
            b = ""
            for row in content:
                body.append(row)
        num_cols = max([len(r) for r in body])
        for row_ind in range(len(body)):
            row = body[row_ind]
            for col  in range(len(row)):
                value = row[col].rstrip(',')
                self.set_string_value(row_ind, col, value)


