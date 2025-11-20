import pandas as pd

def load_2025():
    xls = pd.ExcelFile("F1_Manager_2026.xlsx")
    return {
        "xls": xls
    }
