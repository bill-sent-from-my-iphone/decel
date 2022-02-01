
import pandas as pd

from ..formula import Formula, colint, colval
from ..table_data import TableData

def test_colint():
    assert colint('A') == 0
    assert colint('B') == 1
    assert colint('Z') == 25
    assert colint('AA') == 26
    assert colint('BA') == 52
    assert colint('ZADDS') == 11901778

def test_colmods():
    vals = ['A', 'B', 'A', 'AA', 'BA',  'ZADDS']
    for v in vals:
        i = colint(v)
        assert colval(i) == v


def get_basic_table():
    frame = pd.DataFrame()
    for row in range(20):
        for col in range(30):
            frame.at[row, col] = row + col
    return TableData(dataframe=frame)

def test_basic_locked_formula():
    f = Formula([2, 'B'], '$A$1', get_basic_table())
    assert f._get_value_for_cell([10, 'A']) == 0
    assert f._get_value_for_cell([11, 'B']) == 0

def test_dynamic_formula():
    f = Formula([2, 'B'], 'A1', get_basic_table())
    assert f._get_value_for_cell([3, 'C']) == 2
    assert f._get_value_for_cell([4, 'D']) == 4
    assert f._get_value_for_cell([6, 'F']) == 8
    assert f._get_value_for_cell([3, 'L']) == 11

def test_addition_formula():
    df = pd.DataFrame()
    for i in range(10):
        for j in range(10):
            df.at[i, j] = 1
    td = TableData(dataframe=df)
    td.add_formula(1, "B", "5 * A1 + B2 - 2*C3")
    td.add_formula(2, "C", "5 * A1 + sum(A1:A5)")
    assert td.get_cell_value(1, "B") == 4
    assert td.get_cell_value(2, "C") == 10



