import sys
import pandas as pd

from data.table_data import TableData
from view.sheet_window import SheetWindow
from view.mainwindow import MainWindow
from view.popup import Popup

def main():
    args = sys.argv[1:]
    m = MainWindow(args)
    m.loop()

if __name__ == '__main__':
    main()

