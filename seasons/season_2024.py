import pandas as pd

def load_2024():
    xls = pd.ExcelFile("F1_Manager_2024.xlsx")
    return {
        "xls": xls
    }
