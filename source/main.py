import pandas as pd

from data.table_data import TableData

def main():
    df = pd.DataFrame()
    for i in range(10):
        for j in range(10):
            df.at[i, j] = 1
    td = TableData(dataframe=df)
    td.add_formula(1, "B", "5 * A1 + B2 - 2*C3")
    print(td.get_cell_value(1, "B"))

if __name__ == '__main__':
    main()

