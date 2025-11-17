import pandas as pd


def extract_block(df, start, end):
    """
    Вырезает строки из df[start:end], делает первую строку заголовками.
    Используется для Qualification / Race_Pilots / Race_Teams.
    """
    if start is None or end is None:
        return None

    block = df.iloc[start+1:end].reset_index(drop=True)

    if block.empty:
        return None

    # первая строка блока — заголовки
    header = block.iloc[0]
    data = block[1:].reset_index(drop=True)
    data.columns = header

    return data


def load_season(filename: str):
    xl = pd.ExcelFile(filename)

    # список ГП
    gp_list = xl.parse("GP_List_" + filename[-9:-5])
    gp_map = dict(zip(gp_list["Код"], gp_list["Название"]))

    year = filename[-9:-5]

    # базовые таблицы
    teams = xl.parse(f"Teams_{year}")
    wdc   = xl.parse(f"WDC_{year}")
    wcc   = xl.parse(f"WCC_{year}")

    races = {}

    # читаем листы ГП (BAH, AUS, ...), каждый содержит внутри 3 таблицы
    for code in gp_map.keys():

        if code not in xl.sheet_names:
            races[code] = {
                "qualifying": None,
                "race_drivers": None,
                "race_teams": None,
            }
            continue

        # читаем как есть — без заголовков
        raw = xl.parse(code, header=None)

        q_start = rp_start = rt_start = None

        # ищем строки с заголовками секций
        for i, row in raw.iterrows():
            text = " ".join(str(x) for x in row if str(x).lower() != "nan").lower()

            if "qualification" in text:
                q_start = i
            elif "race_pilots" in text:
                rp_start = i
            elif "race_teams" in text:
                rt_start = i

        # если чего-то не нашли — пропускаем
        q_end  = rp_start if rp_start is not None else None
        rp_end = rt_start if rt_start is not None else None
        rt_end = len(raw)

        races[code] = {
            "qualifying":   extract_block(raw, q_start, q_end),
            "race_drivers": extract_block(raw, rp_start, rp_end),
            "race_teams":   extract_block(raw, rt_start, rt_end),
        }

    return {
        "teams": teams,
        "wdc": wdc,
        "wcc": wcc,
        "gp_codes": list(gp_map.keys()),
        "gp_names": list(gp_map.values()),
        "gp_code_to_name": gp_map,
        "races": races,
    }
