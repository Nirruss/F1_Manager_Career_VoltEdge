import pandas as pd

def load_season(season_year: str):
    file_path = f"F1_Manager_{season_year}.xlsx"

    try:
        xls = pd.ExcelFile(file_path)
    except Exception:
        return {"error": f"Файл {file_path} не найден."}

    # грузим GP List
    gp_list_sheet = f"GP_List_{season_year}"
    try:
        gp_list = xls.parse(gp_list_sheet)
    except:
        return {"error": f"Лист {gp_list_sheet} не найден."}

    gp_list.columns = ["Код", "Название"]

    # ЗАГРУЗКА ЛИСТОВ WDC/WCC/Teams
    def safe_load(sheet):
        try:
            return xls.parse(sheet)
        except:
            return None

    wdc = safe_load("WDC")
    wcc = safe_load("WCC")
    teams = safe_load("Teams")

    # функция загрузки конкретного ГП
    def load_gp(code):
        return {
            "qualifying": safe_load(f"{code}_Q"),
            "race_drivers": safe_load(f"{code}_RD"),
            "race_teams": safe_load(f"{code}_RT")
        }

    return {
        "xls": xls,
        "gp_list": gp_list,
        "wdc": wdc,
        "wcc": wcc,
        "teams": teams,
        "load_gp": load_gp,
    }
