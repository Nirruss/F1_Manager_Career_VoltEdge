import pandas as pd
import numpy as np
import re

# ======================================================
# НОРМАЛИЗАЦИЯ ТЕКСТА (идеальная)
# ======================================================
def normalize_cols(s):
    if not isinstance(s, str):
        return s

    s = (
        s.replace("\xa0", " ")      # non-breaking space
         .replace("\u200b", "")     # zero-width space
         .replace("\r", " ")
         .replace("\n", " ")
         .strip()
    )

    # Убираем двойные пробелы
    s = re.sub(r"\s+", " ", s)

    return s


def normalize_for_match(s):
    """Полная нормализация — для поиска."""
    if not isinstance(s, str):
        s = str(s)

    s = normalize_cols(s)
    return s.lower().strip()


# ======================================================
# ПОИСК КОЛОНКИ (улучшенный, с большим словарём)
# ======================================================
def find_column(df, keywords):
    """
    Возвращает исходное имя колонки, если её нормализованное имя
    содержит одно из ключевых слов.
    """

    for col in df.columns:
        cname = normalize_for_match(col)

        for key in keywords:
            if key in cname:
                return col

    return None


# ======================================================
# ЦВЕТА КОМАНД
# ======================================================
TEAM_COLORS = {
    "ferrari": "#DC0000",
    "red bull": "#1E41FF",
    "mercedes": "#00D2BE",
    "mclaren": "#FF8700",
    "aston martin": "#006F62",
    "rb": "#B9DCFF",
    "haas": "#B6BABD",
    "williams": "#018CFF",
    "kick sauber": "#52E252",
    "alpine": "#0090FF",
    "voltedge": "#F4EA00",
}

TEAM_MAP = {
    "oracle red bull racing": "red bull",
    "mercedes-amg petronas formula one team": "mercedes",
    "scuderia ferrari hp": "ferrari",
    "mclaren formula 1 team": "mclaren",
    "aston martin aramco formula one team": "aston martin",
    "bwt alpine f1 team": "alpine",
    "visa cash app rb formula one team": "rb",
    "stake f1 team kick sauber": "kick sauber",
    "moneygram haas f1 team": "haas",
    "williams racing": "williams",
    "voltedge quantum racing": "voltedge",
}


# ======================================================
# КОНТРАСТНЫЙ ТЕКСТ
# ======================================================
def get_text_color(bg):
    try:
        r = int(bg[1:3], 16)
        g = int(bg[3:5], 16)
        b = int(bg[5:7], 16)
    except:
        return "black"

    yiq = (r * 299 + g * 587 + b * 114) / 1000
    return "white" if yiq < 150 else "black"


# ======================================================
# ОКРАСКА ТАБЛИЦ(исправленная)
# ======================================================
def colorize_table(df: pd.DataFrame):
    if df is None or df.empty:
        return df

    df = df.copy()

    # Чистим строки
    for col in df.columns:
        df[col] = df[col].apply(
            lambda x: normalize_cols(x) if isinstance(x, str) else x
        )

    # Ищем колонку команды в сотне вариантов
    team_col = find_column(
        df,
        [
            "команда",
            "team",
            "конструктор",
            "constructor",
            "car",
            "team name",
            "constructor name",
        ],
    )

    # красим строки
    if team_col:
        team_clean = df[team_col].astype(str).apply(normalize_for_match)

        mapped = team_clean.map(TEAM_MAP).fillna(team_clean)
        df["__color__"] = mapped.map(TEAM_COLORS).fillna("#FFFFFF")
    else:
        df["__color__"] = "#FFFFFF"

    rows = df["__color__"]
    out = df.drop(columns=["__color__"], errors="ignore")

    def style_row(row):
        bg = rows.iloc[row.name]
        fg = get_text_color(bg)
        return [f"background-color:{bg}; color:{fg}" for _ in row]

    return out.style.apply(style_row, axis=1).hide(axis="index")


# ======================================================
# ЛУЧШИЙ КРУГ
# ======================================================
def parse_lap_time(val):
    if not isinstance(val, str):
        return pd.NaT

    s = normalize_for_match(val)
    if any(x in s for x in ["dnf", "выб", "круг", "lap"]):
        return pd.NaT

    try:
        return pd.to_timedelta(val)
    except:
        return pd.NaT


# ======================================================
# ПИЛОТ → КОМАНДА
# ======================================================
def build_pilot_team_map(teams_df: pd.DataFrame):

    if teams_df is None or teams_df.empty:
        return {}

    pilot_col = find_column(teams_df, ["пилот", "driver"])
    team_col = find_column(teams_df, ["команда", "team"])

    if not pilot_col or not team_col:
        return {}

    mapping = {}
    for _, row in teams_df.iterrows():
        pilot = normalize_cols(str(row[pilot_col]))
        team_raw = normalize_for_match(str(row[team_col]))
        team = TEAM_MAP.get(team_raw, team_raw)
        mapping[pilot] = team

    return mapping


# ======================================================
# ПАРСЕР СЕЗОНА
# ======================================================
def load_season_data(xls_path: str):

    xls = pd.ExcelFile(xls_path)
    season_year = xls_path.split("_")[-1].split(".")[0]

    gp_sheet = f"GP_List_{season_year}"
    gp_df = pd.read_excel(xls, gp_sheet)
    gp_df.columns = ["code", "name"]

    gp_list = dict(
        zip(
            gp_df["code"].astype(str).str.strip(),
            gp_df["name"].astype(str).str.strip()
        )
    )

    wdc = pd.read_excel(xls, f"WDC_{season_year}")
    wcc = pd.read_excel(xls, f"WCC_{season_year}")
    teams = pd.read_excel(xls, f"Teams_{season_year}")

    grand_prix = {}

    for code in gp_list:
        if code not in xls.sheet_names:
            continue

        df = pd.read_excel(xls, code, header=None)

        sections = {}
        key = None
        temp = []
        skip_header = False

        for _, row in df.iterrows():

            row_text = " ".join(
                normalize_for_match(str(x))
                for x in row.values
                if pd.notna(x)
            )

            if row_text == "" or row_text == "nan":
                continue

            # QUALIFY
            if any(x in row_text for x in ["qualificat", "qualification", "qualify"]):
                if key and temp:
                    sections[key] = pd.DataFrame(temp)
                key = "qualifying"
                temp = []
                skip_header = True
                continue

            # RACE DRIVERS
            if "race_pilots" in row_text or "race drivers" in row_text:
                if key and temp:
                    sections[key] = pd.DataFrame(temp)
                key = "race_drivers"
                temp = []
                skip_header = True
                continue

            # RACE TEAMS
            if "race_teams" in row_text or "race teams" in row_text:
                if key and temp:
                    sections[key] = pd.DataFrame(temp)
                key = "race_teams"
                temp = []
                skip_header = True
                continue

            if skip_header:
                skip_header = False
                continue

            if key is not None:
                temp.append(list(row))

        if key and temp:
            sections[key] = pd.DataFrame(temp)

        grand_prix[code] = sections

    return {
        "gp_map": gp_list,
        "gp_list": gp_list,
        "grand_prix": grand_prix,
        "wdc": wdc,
        "wcc": wcc,
        "teams": teams,
    }
