import pandas as pd

from data.table_data import TableData
from view.sheet_window import SheetWindow
from view.mainwindow import MainWindow
from view.popup import Popup

def main():
    m = MainWindow()
    m.loop()

if __name__ == '__main__':
    main()

