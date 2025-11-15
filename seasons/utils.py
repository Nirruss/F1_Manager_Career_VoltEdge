import pandas as pd

def load_season_data(xls_path: str):
    """
    Загружает:
    - лист GP_List_XXXX
    - WDC_XXXX
    - WCC_XXXX
    - Teams_XXXX
    - ВСЕ гонки по их кодам (BAH, SAU, AUS…)
    """

    xls = pd.ExcelFile(xls_path)

    # ------ 1. Определяем сезон ------

    # путь заканчивается на F1_Manager_2024.xlsx → берём "2024"
    season_year = xls_path.split("_")[-1].split(".")[0]
    gp_sheet = f"GP_List_{season_year}"

    gp_list_df = pd.read_excel(xls, gp_sheet)

    # нормализуем имена
    gp_list_df.columns = ["code", "name"]
    gp_list_df["code"] = gp_list_df["code"].astype(str).str.strip()
    gp_list_df["name"] = gp_list_df["name"].astype(str).strip()

    # создаём mapping: CODE → NAME
    gp_map = dict(zip(gp_list_df["code"], gp_list_df["name"]))

    # ------ 2. Загружаем командные листы ------

    wdc = pd.read_excel(xls, f"WDC_{season_year}")
    wcc = pd.read_excel(xls, f"WCC_{season_year}")
    teams = pd.read_excel(xls, f"Teams_{season_year}")

    # ------ 3. Загружаем ВСЕ гонки по кодам ------

    grand_prix = {}

    for code in gp_map.keys():
        if code not in xls.sheet_names:
            print(f"[WARNING] Лист гонки '{code}' отсутствует в Excel.")
            continue

        df = pd.read_excel(xls, code)

        # делим на секции
        # Квалификация / Гонка — пилоты / Гонка — команды
        sections = {}
        current_key = None
        temp = []

        for _, row in df.iterrows():
            cell = str(row.iloc[0]).strip().lower()

            if "квалификация" in cell:
                if current_key and temp:
                    sections[current_key] = pd.DataFrame(temp).dropna(how="all")
                    temp = []
                current_key = "qualifying"

            elif "гонка" in cell and "пилот" in cell:
                if current_key and temp:
                    sections[current_key] = pd.DataFrame(temp).dropna(how="all")
                    temp = []
                current_key = "race_drivers"

            elif "гонка" in cell and "команд" in cell:
                if current_key and temp:
                    sections[current_key] = pd.DataFrame(temp).dropna(how="all")
                    temp = []
                current_key = "race_teams"

            else:
                if current_key:
                    temp.append(list(row))

        if current_key and temp:
            sections[current_key] = pd.DataFrame(temp).dropna(how="all")

        # добавляем гонку в словарь
        grand_prix[code] = sections

    # ------ 4. Возвращаем структуру данных сезона ------

    return {
        "gp_map": gp_map,          # CODE → Name
        "grand_prix": grand_prix,  # данные гонок
        "wdc": wdc,
        "wcc": wcc,
        "teams": teams,
    }
