import pandas as pd
import numpy as np
import re

# ========================================
# НОРМАЛИЗАЦИЯ ТЕКСТА
# ========================================
def normalize_cols(s):
    if not isinstance(s, str):
        return s
    return (
        s.replace("\xa0", " ")
         .replace("\n", " ")
         .strip()
         .lower()
    )


def find_column(df, keywords):
    norm = {col: normalize_cols(col) for col in df.columns}
    for col, n in norm.items():
        for key in keywords:
            if key in n:
                return col
    return None


# ========================================
# ЦВЕТА КОМАНД
# ========================================
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


# ========================================
# КОНТРАСТНЫЙ ТЕКСТ
# ========================================
def get_text_color(bg):
    try:
        r = int(bg[1:3], 16)
        g = int(bg[3:5], 16)
        b = int(bg[5:7], 16)
    except:
        return "black"
    yiq = (r * 299 + g * 587 + b * 114) / 1000
    return "white" if yiq < 150 else "black"


# ========================================
# ОКРАСКА ТАБЛИЦ
# ========================================
def colorize_table(df: pd.DataFrame):
    if df is None or df.empty:
        return df

    df = df.copy()
    df = df.applymap(lambda x: str(x).replace("\xa0", " ").strip()
                     if isinstance(x, str) else x)

    team_col = find_column(df, ["команда", "team"])

    if team_col:
        normalized = df[team_col].apply(lambda x: normalize_cols(str(x)))
        mapped = normalized.map(TEAM_MAP).fillna(normalized)
        df["__color__"] = mapped.map(TEAM_COLORS).fillna("#FFFFFF")
    else:
        df["__color__"] = "#FFFFFF"

    df = df.reset_index(drop=True)
    row_colors = df["__color__"]

    display_df = df.drop(columns=["__color__"], errors="ignore")

    def row_style(row):
        bg = row_colors.iloc[row.name]
        fg = get_text_color(bg)
        return [f"background-color:{bg}; color:{fg}" for _ in row]

    return display_df.style.apply(row_style, axis=1).hide(axis="index")


# ========================================
# РАЗБОР ЛУЧШЕГО КРУГА
# ========================================
def parse_lap_time(val):
    if not isinstance(val, str):
        return pd.NaT
    s = normalize_cols(val)
    if any(x in s for x in ["круг", "lap", "dnf", "выб"]):
        return pd.NaT
    try:
        return pd.to_timedelta(val)
    except:
        return pd.NaT


# ========================================
# КАРТА ПИЛОТ → КОМАНДА
# ========================================
def build_pilot_team_map(teams_df: pd.DataFrame):
    if teams_df is None or teams_df.empty:
        return {}

    teams_df = teams_df.copy()
    pilot_col = find_column(teams_df, ["пилот", "driver"])
    team_col = find_column(teams_df, ["команда"])

    if not pilot_col or not team_col:
        return {}

    mapping = {}
    for _, row in teams_df.iterrows():
        pilot = str(row[pilot_col]).strip()
        team_raw = normalize_cols(str(row[team_col]).strip())
        team = TEAM_MAP.get(team_raw, team_raw)
        mapping[pilot] = team
    return mapping


# ========================================
# ГЛАВНЫЙ ПАРСЕР СЕЗОНА — АДАПТИРОВАН ПОД ТВОЙ EXCEL
# ========================================
def load_season_data(xls_path: str):

    xls = pd.ExcelFile(xls_path)

    season_year = xls_path.split("_")[-1].split(".")[0]

    # ----- GP LIST -----
    gp_sheet = f"GP_List_{season_year}"
    gp_df = pd.read_excel(xls, gp_sheet)
    gp_df.columns = ["code", "name"]

    gp_list = dict(zip(
        gp_df["code"].astype(str).str.strip(),
        gp_df["name"].astype(str).str.strip()
    ))

    # ----- WDC / WCC -----
    wdc = pd.read_excel(xls, f"WDC_{season_year}")
    wcc = pd.read_excel(xls, f"WCC_{season_year}")

    # ----- TEAMS -----
    teams = pd.read_excel(xls, f"Teams_{season_year}")

    # ----- ГРАН-ПРИ -----
    grand_prix = {}

    for code in gp_list:
        if code not in xls.sheet_names:
            continue

        df = pd.read_excel(xls, code)

        sections = {}
        key = None
        temp = []

        for _, row in df.iterrows():
            c0 = str(row.iloc[0]).strip().lower()

            # пустые строки — пропускаем
            if c0 == "" or c0 == "nan":
                continue

            # ---------- QUALIFICATION ----------
            if c0.startswith("qualification"):
                if key and temp:
                    sections[key] = pd.DataFrame(temp)
                key = "qualifying"
                temp = []
                continue

            # ---------- RACE PILOTS ----------
            if c0.startswith("race_pilots") or c0.startswith("race pilots"):
                if key and temp:
                    sections[key] = pd.DataFrame(temp)
                key = "race_drivers"
                temp = []
                continue

            # ---------- RACE TEAMS ----------
            if c0.startswith("race_teams") or c0.startswith("race teams"):
                if key and temp:
                    sections[key] = pd.DataFrame(temp)
                key = "race_teams"
                temp = []
                continue

            # Внутри блока — копим строки
            if key is not None:
                temp.append(list(row))

        # закрываем последний блок
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
