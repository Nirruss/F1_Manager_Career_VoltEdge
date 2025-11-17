import pandas as pd


def _fix_headers(cols):
    """
    Делает заголовки уникальными:
    - заменяет NaN на 'col_X'
    - добавляет суффиксы _2, _3 для дубликатов
    """
    new_cols = []
    used = {}

    for i, c in enumerate(cols):
        # заменяем nan / пустые значения
        if pd.isna(c) or str(c).strip() == "":
            c = f"col_{i}"

        c = str(c).strip()

        # если дубликат — делаем уникальным
        if c in used:
            used[c] += 1
            c = f"{c}_{used[c]}"
        else:
            used[c] = 1

        new_cols.append(c)

    return new_cols


def _extract_block(df: pd.DataFrame, start: int, end: int):
    """
    Вырезает блок таблицы между start и end.
    Первая строка блока — это заголовки.
    Остальные строки — данные.
    """
    block = df.iloc[start+1:end].reset_index(drop=True)

    if block.empty:
        return None

    header = block.iloc[0]
    data = block.iloc[1:].reset_index(drop=True)

    # ФИКС: делаем заголовки уникальными
    data.columns = _fix_headers(header)

    data = data.dropna(how="all")
    data = data.dropna(axis=1, how="all")

    return data if not data.empty else None


def _parse_grand_prix_sheet(xl: pd.ExcelFile, code: str):
    df = xl.parse(code, header=None)

    q_start = rp_start = rt_start = None

    # ищем строки начала секций по A-колонке
    for i, row in df.iterrows():
        cell = str(row.iloc[0]).strip().lower()

        if cell == "qualification":
            q_start = i
        elif cell == "race_pilots":
            rp_start = i
        elif cell == "race_teams":
            rt_start = i

    last = len(df)

    q_end = rp_start if rp_start else last
    rp_end = rt_start if rt_start else last
    rt_end = last

    return {
        "qualifying":   _extract_block(df, q_start, q_end) if q_start is not None else None,
        "race_drivers": _extract_block(df, rp_start, rp_end) if rp_start is not None else None,
        "race_teams":   _extract_block(df, rt_start, rt_end) if rt_start is not None else None,
    }


def load_season(filename: str):
    xl = pd.ExcelFile(filename)
    year = filename[-9:-5]

    gp_list = xl.parse(f"GP_List_{year}")
    gp_map = dict(zip(gp_list["Код"], gp_list["Название"]))

    teams = xl.parse(f"Teams_{year}")
    wdc   = xl.parse(f"WDC_{year}")
    wcc   = xl.parse(f"WCC_{year}")

    grand_prix = {}

    for code in gp_map:
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

        "grand_prix": grand_prix,
    }
