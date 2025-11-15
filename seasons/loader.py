import pandas as pd

def load_season(filename: str):
    xl = pd.ExcelFile(filename)

    # список ГП
    gp_list = xl.parse("GP_List_" + filename[-9:-5])
    gp_map = dict(zip(gp_list["Код"], gp_list["Название"]))

    # загрузка базовых таблиц
    year = filename[-9:-5]
    teams = xl.parse(f"Teams_{year}")
    wdc = xl.parse(f"WDC_{year}")
    wcc = xl.parse(f"WCC_{year}")

    # загрузка данных по гонкам
    races = {}
    for code in gp_map.keys():
        if code in xl.sheet_names:
            races[code] = xl.parse(code)
        else:
            races[code] = None

    return {
        "teams": teams,
        "wdc": wdc,
        "wcc": wcc,
        "gp_codes": list(gp_map.keys()),
        "gp_names": list(gp_map.values()),
        "gp_code_to_name": gp_map,
        "races": races,
    }
