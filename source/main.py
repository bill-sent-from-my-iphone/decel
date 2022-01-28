import pandas as pd

from data.table_data import TableData

def main():
    df = pd.DataFrame()
    for i in range(10):
        for j in range(10):
            df.at[i, j] = 1
    td = TableData(dataframe=df)
    td.add_formula(1, "B", "5 * A1 + B2 - 2*C3")
    td.add_formula(2, "C", "5 * A1 + sum(A1:A5)")
    print(td.get_cell_value(2, "C"))

if __name__ == '__main__':
    main()

