import pandas as pd


def _extract_block(df: pd.DataFrame, start: int | None, end: int | None):
    """
    Вырезает кусок df между строками start и end (не включая start),
    первую строку блока делает заголовками.
    """
    if start is None:
        return None

    if end is None:
        end = len(df)

    # блок после строки-заголовка секции
    block = df.iloc[start + 1:end].reset_index(drop=True)
    if block.empty:
        return None

    # первая строка блока — шапка
    header = block.iloc[0]
    data = block.iloc[1:].reset_index(drop=True)
    data.columns = header

    # выкинем полностью пустые строки
    data = data.dropna(how="all")
    if data.empty:
        return None

    return data


def _parse_grand_prix_sheet(xl: pd.ExcelFile, code: str) -> dict:
    """
    Парсит лист одного Гран-при (BAH, AUS, ...) в три таблицы:
    Qualification, Race_Pilots, Race_Teams.
    """
    # читаем как есть, без заголовков
    raw = xl.parse(code, header=None)

    q_start = rp_start = rt_start = None

    # ищем строки, где написано "Qualification", "Race_Pilots", "Race_Teams"
    for i, row in raw.iterrows():
        # склеиваем непустые ячейки строки в одну строку текста
        cells = [str(x) for x in row if pd.notna(x)]
        if not cells:
            continue
        text = " ".join(cells).strip().lower()

        if "qualification" in text and q_start is None:
            q_start = i
        elif "race_pilots" in text and rp_start is None:
            rp_start = i
        elif "race_teams" in text and rt_start is None:
            rt_start = i

    # определяем границы блоков
    q_end = rp_start if rp_start is not None else rt_start
    rp_end = rt_start
    rt_end = None  # до конца листа

    qualifying   = _extract_block(raw, q_start, q_end)
    race_drivers = _extract_block(raw, rp_start, rp_end)
    race_teams   = _extract_block(raw, rt_start, rt_end)

    return {
        "qualifying": qualifying,
        "race_drivers": race_drivers,
        "race_teams": race_teams,
    }


def load_season(filename: str):
    xl = pd.ExcelFile(filename)

    # год из имени файла, например ..._2024.xlsx -> "2024"
    year = filename[-9:-5]

    # список ГП
    gp_list = xl.parse(f"GP_List_{year}")
    gp_map = dict(zip(gp_list["Код"], gp_list["Название"]))

    # базовые таблицы
    teams = xl.parse(f"Teams_{year}")
    wdc   = xl.parse(f"WDC_{year}")
    wcc   = xl.parse(f"WCC_{year}")

    grand_prix: dict[str, dict] = {}

    # для каждого Гран-при режем лист на 3 таблицы
    for code in gp_map.keys():
        if code in xl.sheet_names:
            grand_prix[code] = _parse_grand_prix_sheet(xl, code)
        else:
            grand_prix[code] = {
                "qualifying": None,
                "race_drivers": None,
                "race_teams": None,
            }

    return {
        "teams": teams,
        "wdc": wdc,
        "wcc": wcc,
        "gp_codes": list(gp_map.keys()),
        "gp_names": list(gp_map.values()),
        "gp_code_to_name": gp_map,
        "grand_prix": grand_prix,
    }
