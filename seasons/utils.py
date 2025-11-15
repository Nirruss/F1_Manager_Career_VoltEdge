import pandas as pd
import re


# ============================================================
# НОРМАЛИЗАЦИЯ ТЕКСТА (ТОЛЬКО ДЛЯ ПОИСКА!)
# ============================================================
def normalize_cols(s):
    if not isinstance(s, str):
        return ""
    return (
        s.replace("\xa0", " ")
         .replace("\u200b", "")
         .replace("\r", " ")
         .replace("\n", " ")
         .strip()
         .lower()
    )


# ============================================================
# ПОИСК КОЛОНОК
# ============================================================
def find_column(df, keywords):
    for col in df.columns:
        key = normalize_cols(col) if isinstance(col, str) else str(col).lower()
        for w in keywords:
            if w in key:
                return col
    return None


# ============================================================
# ЦВЕТА КОМАНД
# ============================================================
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
    "stake kick sauber": "kick sauber",
    "moneygram haas f1 team": "haas",
    "williams racing": "williams",
    "voltedge quantum racing": "voltedge",
}


# ============================================================
# КОНТРАСТ ТЕКСТА
# ============================================================
def get_text_color(bg):
    try:
        r = int(bg[1:3], 16)
        g = int(bg[3:5], 16)
        b = int(bg[5:7], 16)
    except Exception:
        return "black"

    yiq = (r * 299 + g * 587 + b * 114) / 1000
    return "white" if yiq < 150 else "black"


# ============================================================
# НОРМАЛИЗАЦИЯ КЛЮЧА ДЛЯ TEAM_MAP (ТОЛЬКО КЛЮЧ!)
# ============================================================
def normalize_team_key(name: str):
    if not isinstance(name, str):
        return ""
    return (
        name.replace("\xa0", " ")
            .replace("\u200b", "")
            .strip()
            .lower()
    )


# ============================================================
# COLORIZE TABLE (ОКРАШИВАНИЕ)
# ============================================================
def colorize_table(df: pd.DataFrame):
    if df is None or df.empty:
        return df

    df = df.copy()

    team_col = find_column(df, ["команда", "team"])
    if team_col:
        original_values = df[team_col].astype(str)

        # нормализуем ТОЛЬКО для поиска
        normalized = original_values.apply(normalize_team_key)

        mapped_name = normalized.map(TEAM_MAP).fillna(normalized)

        df["__color__"] = mapped_name.map(TEAM_COLORS).fillna("#FFFFFF")
    else:
        df["__color__"] = "#FFFFFF"

    row_colors = df["__color__"]
    display_df = df.drop(columns=["__color__"], errors="ignore")

    def style_row(row):
        bg = row_colors.iloc[row.name]
        fg = get_text_color(bg)
        return [f"background-color:{bg}; color:{fg}" for _ in row]

    return display_df.style.apply(style_row, axis=1).hide(axis="index")


# ============================================================
# ПАРСИНГ ВРЕМЕНИ КРУГА
# ============================================================
def parse_lap_time(val):
    if not isinstance(val, str):
        return pd.NaT
    s = normalize_cols(val)
    if any(w in s for w in ["dnf", "выб", "круг", "lap"]):
        return pd.NaT
    try:
        return pd.to_timedelta(val)
    except:
        return pd.NaT


# ============================================================
# ПИЛОТ → КОМАНДА
# ============================================================
def build_pilot_team_map(teams_df: pd.DataFrame):
    if teams_df is None or teams_df.empty:
        return {}

    df = teams_df.copy()

    pilot_col = find_column(df, ["пилот", "driver"])
    team_col = find_column(df, ["команда"])

    if not pilot_col or not team_col:
        return {}

    mapping = {}

    for _, row in df.iterrows():
        pilot = str(row[pilot_col]).strip()
        team_raw = str(row[team_col]).strip()
        key = normalize_team_key(team_raw)
        mapped = TEAM_MAP.get(key, team_raw)
        mapping[pilot] = mapped

    return mapping


# ============================================================
# ПАРСЕР СЕЗОНА
# ============================================================
def load_season_data(xls_path: str):

    xls = pd.ExcelFile(xls_path)
    season_year = xls_path.split("_")[-1].split(".")[0]

    gp_sheet = f"GP_List_{season_year}"
    gp_df = pd.read_excel(xls, gp_sheet)
    gp_df.columns = ["code", "name"]

    gp_list = dict(zip(
        gp_df["code"].astype(str).str.strip(),
        gp_df["name"].astype(str).str.strip()
    ))

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
                normalize_cols(str(x))
                for x in row.values
                if pd.notna(x)
            ).strip()

            if not row_text:
                continue

            if any(x in row_text for x in ["qualificat", "qualification", "qualify", "квалиф"]):
                if key and temp:
                    sections[key] = pd.DataFrame(temp)
                key = "qualifying"
                temp = []
                skip_header = True
                continue

            if "race_pilots" in row_text or "race drivers" in row_text:
                if key and temp:
                    sections[key] = pd.DataFrame(temp)
                key = "race_drivers"
                temp = []
                skip_header = True
                continue

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
