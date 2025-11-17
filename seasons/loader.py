import pandas as pd


def _extract_block(df: pd.DataFrame, start: int, end: int):
    """
    Вырезает блок таблицы между start и end.
    Первая строка блока — это заголовки.
    Остальные строки — данные.
    """
    # всё между start+1 и end
    block = df.iloc[start+1:end].reset_index(drop=True)

    # если блок пустой – пропускаем
    if block.empty:
        return None

    # первая строка — header
    header = block.iloc[0]
    data = block.iloc[1:].reset_index(drop=True)
    data.columns = header

    # убираем полностью пустые строки
    data = data.dropna(how="all")

    return data if not data.empty else None


def _parse_grand_prix_sheet(xl: pd.ExcelFile, code: str):
    """
    Разделяет Qualification / Race_Pilots / Race_Teams для листа ГП.
    """
    df = xl.parse(code, header=None)

    q_start = rp_start = rt_start = None

    # ищем строки начала секций
    for i, row in df.iterrows():
        cell = str(row.iloc[0]).strip().lower()

        if cell == "qualification":
            q_start = i
        elif cell == "race_pilots":
            rp_start = i
        elif cell == "race_teams":
            rt_start = i

    # теперь определим границы
    # qualification: q_start → rp_start
    # race_pilots:   rp_start → rt_start
    # race_teams:    rt_start → конец
    last = len(df)

    q_end = rp_start if rp_start else last
    rp_end = rt_start if rt_start else last
    rt_end = last

    qualifying   = _extract_block(df, q_start, q_end) if q_start is not None else None
    race_drivers = _extract_block(df, rp_start, rp_end) if rp_start is not None else None
    race_teams   = _extract_block(df, rt_start, rt_end) if rt_start is not None else None

    return {
        "qualifying": qualifying,
        "race_drivers": race_drivers,
        "race_teams": race_teams,
    }


def load_season(filename: str):
    xl = pd.ExcelFile(filename)

    # определяем год
    year = filename[-9:-5]

    gp_list = xl.parse(f"GP_List_{year}")
    gp_map = dict(zip(gp_list["Код"], gp_list["Название"]))

    teams = xl.parse(f"Teams_{year}")
    wdc   = xl.parse(f"WDC_{year}")
    wcc   = xl.parse(f"WCC_{year}")

    grand_prix = {}

    for code in gp_map.keys():
        if code in xl.sheet_names:
            grand_prix[code] = _parse_grand_prix_sheet(xl, code)
        else:
            grand_prix[code] = {"qualifying":None, "race_drivers":None, "race_teams":None}

    return {
        "teams": teams,
        "wdc": wdc,
        "wcc": wcc,
        "gp_code_to_name": gp_map,
        "gp_codes": list(gp_map.keys()),
        "grand_prix": grand_prix
    }
