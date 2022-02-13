import re
import os
import pandas as pd;
import csv

from .script_loader import get_loader
from .formula import Formula, colval, has_tokens
from .dependency_tree import DependencyNode, DependencyTree

unnamed_col = r'Unnamed: [0-9]+'

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
        self.current_file = ''
        self.tree = DependencyTree()

    def clear_data(self):
        self.data = pd.DataFrame()
        self.formulae = {}
        self.dependencies = {}

    def force_update(self):
        for row, rowdata in self.data.iterrows():
            for col, value in rowdata.iteritems():
                self.token_changed((row, col))
        self.trigger_update()

    def has_value(self, row, col):
        if self._has_formula(col, row):
            return True
        if col not in self.data:
            return False
        val = self.data.get(col, {}).get(row, False)
        if isinstance(val, float):
            if pd.isna(val):
                return False
        return bool(val)

    def get_cell_value(self, row, col):
        if self._has_formula(row, col):
            return self.formulae[row][col].get_value()
        return self.data.get(row, {}).get(col, None)

    def get_cell_range_coords(self, start_pos, end_pos):
        output = []
        rows = sorted([start_pos[0], end_pos[0]])
        cols = sorted([start_pos[1], end_pos[1]])
        for row in range(rows[0], rows[1]+1):
            for col in range(cols[0], cols[1]+1):
                output.append((row, colval(col)))
        return output

    def get_cell_range(self, start_pos, end_pos):
        output = []
        coords = self.get_cell_range_coords(start_pos, end_pos)
        for row, col in coords:
                val = self.get_cell_value(col, row)
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

    def add_table_table(self, new_table):
        pass

    def update_value(self, row, col):
        if self._has_formula(row, col):
            val = self.formulae[row][col].get_value()
            self.set_value(row, col, val)

    def remove_formula(self, row, col):
        if row in self.formulae:
            del self.formulae[row][col]

    def add_dependency(self, lead_token, dependent_token):
        if lead_token not in self.dependencies:
            self.dependencies[lead_token] = {}
        self.dependencies[lead_token][dependent_token] = True

    def add_dependencies(self, formula):
        tokens = formula.get_dependent_coordinates(formula.position)
        f_pos = formula.position
        for token in tokens:
            self.add_dependency(token, f_pos)

    def token_changed(self, cell):
        for child in self.dependencies.get(cell, {}):
            self.tree.add_dependency(cell, child)

    def trigger_update(self):
        for row, col in self.tree.yield_values():
            self.update_value(row, col)
        self.tree.shake()

    def make_formula(self, row, col, formula):
        new_formula = Formula((row, col), formula, self)
        self.add_formula(row, col, new_formula)

    def add_formula(self, row, col, new_formula):
        if row not in self.formulae:
            self.formulae[row] = {}
        self.formulae[row][col] = new_formula

        val = new_formula.get_value()
        self.add_dependencies(new_formula)
        self.set_value(row, col, val)
        self.token_changed((row, col))

    def set_string_value(self, r, c, val):
        col = colval(c)
        if self._has_formula(r, col):
            self.remove_formula(r, col)
        val = val.strip(' ')
        if has_tokens(val):
            self.make_formula(r, col, val)
        else:
            try:
                local_vars = get_loader().get_vars()
                value = eval(val, {}, local_vars)
                try:
                    v = float(value)
                    self.set_value(r, col, v)
                except:
                    self.set_value(r, col, value)
            except:
                self.set_value(r, col, val)

    def set_value(self, row, col, value):
        self.data.at[row, col] = value
        self.token_changed((row, col))

    def load_csv(self, filepath):
        body = []

        new_df = pd.DataFrame()
        csv_df = pd.read_csv(filepath)
        p_cols = csv_df.columns

        self.clear_data()
        self.data = new_df
        for i in range(len(p_cols)):
            csv_col = p_cols[i]
            col_name = colval(i)

            csv_col_name = csv_col
            if re.match(unnamed_col, csv_col_name):
                csv_col_name = ''
            new_df.at[0, col_name] = csv_col_name
            for r in range(len(csv_df)):
                raw_val = csv_df.at[r, csv_col]
                if pd.isna(raw_val):
                    self.set_value(r+1, i, None)
                    #self.set_string_value(r+1, i, "")
                else:
                    v = str(raw_val).strip(' ')
                    self.set_string_value(r+1, i, v)

        self.set_filename(filepath)

    def filename(self):
        return self.current_file

    def set_filename(self, fname):
        self.current_file = fname

    def has_filename(self):
        return len(self.current_file) > 0

    def save(self):
        fname = self.current_file
        if not fname:
            raise Exception('No file specified')
        if fname.endswith('.csv'):
            self.save_csv(fname)

    def save_csv(self, filepath):
        if not filepath:
            filepath = self.current_file
        self.data.to_csv(filepath, header=None, index=None)

