import re
import os
import pandas as pd;
import csv
import json

from .script_loader import get_loader
from .formula import Formula, colval, has_tokens, colint
from .dependency_tree import DependencyNode, DependencyTree
from .stocks import tick

unnamed_col = r'Unnamed: [0-9]+'

global defaults
defaults = {}

def add_func(f):
    name = f.__name__
    defaults[name] = f

add_func(tick)

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
    col = colint(m.group(0))

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
        out = self.data.get(row, {}).get(col, None)


        # This makes no sense but sometimes numpy floats throw a fit
        if isinstance(out, float):
            out = float(out)

        return out

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
            if col in self.formulae[row]:
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
        return new_formula

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
                local_vars = defaults
                local_vars.update(get_loader().get_vars())
                value = eval(val, {}, local_vars)
                if isinstance(value, pd.DataFrame):
                    cols = value.columns
                    rowind = 0
                    has_index = False
                    for ind, row in value.iterrows():
                        rowind += 1
                        nrow = r + rowind
                        colrange = len(cols)

                        start_col_offset = 0

                        if has_index or not isinstance(ind, int):
                            has_index = True
                            self.set_value(nrow, colval(c), ind)
                            start_col_offset = 1
                        else:
                            rowind = ind

                        for i in range(len(cols)):
                            col_ = cols[i]
                            val = row[col_]
                            ncol = colval(c + i + start_col_offset)
                            self.set_value(nrow, ncol, val)

                    for i in range(len(cols)):
                        ncol = colval(c + i + start_col_offset)
                        self.set_value(r, ncol, cols[i])

                    return
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

    def load_file(self, filepath):
        if filepath.endswith('.dc'):
            self.load_dc(filepath)
            return
        if filepath.endswith('.csv'):
            self.load_csv(filepath)
            return
        raise Exception('Invalid Filetype')

    def load_dc(self, filepath):
        with open(filepath, 'r') as f:
            content = json.load(f)
        decel_data = content['decel']

        formulae = decel_data['formulae']
        csv_data = decel_data['csv']

        tmp_csv = os.path.join(os.getcwd(), 'tmp_csv.csv')
        with open(tmp_csv, 'w+') as f:
            f.write(csv_data)

        self.load_csv(tmp_csv)

        for f in formulae:
            formula_data = formulae[f]
            r, _, c, _ = read_token(f)
            cell = (r, c)
            formula = formula_data['formula']
            t_data = [read_token(t) for t in formula_data['children'].split(',')]
            children = [(t[0], t[2]) for t in t_data]
            
            base = self.make_formula(r, colval(c), formula)
            for cr, cc in children:
                child_formula = base.make_child((cr, colval(cc)))
                self.add_formula(cr, colval(cc), child_formula)

        #os.remove(tmp_csv)
        self.set_filename(filepath)

    def load_csv(self, filepath):
        body = []

        new_df = pd.DataFrame()
        csv_df = pd.read_csv(filepath, header=None)
        p_cols = csv_df.columns

        self.clear_data()
        self.data = new_df
        for i in range(len(p_cols)):
            csv_col = p_cols[i]
            col_name = colval(i)

            for r in range(len(csv_df)):
                raw_val = csv_df.at[r, csv_col]
                if pd.isna(raw_val):
                    self.set_value(r, i, None)
                else:
                    v = str(raw_val).strip(' ')
                    self.set_string_value(r, i, v)

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
        if fname.endswith('.dc'):
            self.save_dc(fname)

    def save_csv(self, filepath):
        if not filepath:
            filepath = self.current_file
        self.data.to_csv(filepath, header=None, index=None)

    def iter_formulae(self):
        for r in self.formulae:
            row = self.formulae[r]
            for c in row:
                formula = row[c]
                yield (r,c), formula
        pass

    def cell_str(self, cell):
        return '{}{}'.format(cell[1], cell[0])

    def make_formula_dict(self, formula):
        return {
                 'location' : self.cell_str(formula.position),
                 'formula' : formula.get_display_formula(),
                 'children' : []
               }

    def get_formula_jsondata(self):
        root_formulae = {}
        children = {}
        for cell, formula in self.iter_formulae():
            parent = formula.root()
            ppos = parent.position
            if ppos not in root_formulae:
                root_formulae[ppos] = self.make_formula_dict(parent)

            if ppos not in children:
                children[ppos] = [cell]
            else:
                children[ppos].append(cell)

        for f in root_formulae:
            # Need to turn this into a range or something. String gets too big
            fdata = root_formulae[f]
            child_cells = children[f]
            childstring = ','.join([self.cell_str(cell) for cell in child_cells])
            fdata['children'] = childstring

        output = {}

        for f in root_formulae:
            output[self.cell_str(f)] = root_formulae[f]

        return output

    def save_dc(self, filepath):
        output_data = {}
        decel_data = {}

        formula_data = self.get_formula_jsondata()
        decel_data['formulae'] = formula_data

        current = os.getcwd()
        tmp_csv = os.path.join(current, 'tmp_csv.csv')

        self.save_csv(tmp_csv)
        with open(tmp_csv) as f:
            content = f.read()
            decel_data['csv'] = content
        os.remove(tmp_csv)

        output_data['decel'] = decel_data

        dest_path = filepath
        if not os.path.exists(filepath):
            dest_path = os.path.join(current, filepath)

        with open(dest_path, 'w+') as f:
            json.dump(output_data, f)



