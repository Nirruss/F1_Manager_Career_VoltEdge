import pandas as pd
import numpy as np
import re

# =========================
# НОРМАЛИЗАЦИЯ ДЛЯ ПОИСКА
# =========================
def normalize_match(s):
    if not isinstance(s, str):
        s = str(s)
    s = (
        s.replace("\xa0", " ")
         .replace("\u200b", "")
         .replace("\r", " ")
         .replace("\n", " ")
         .strip()
    )
    return re.sub(r"\s+", " ", s).lower()


# =========================
# ПОИСК КОЛОНКИ
# =========================
def find_column(df, keys):
    for col in df.columns:
        cname = normalize_match(col)
        for key in keys:
            if key in cname:
                return col
    return None


# =========================
# КАРТА КОМАНД
# =========================
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
    "visa cash app rb formula one team": "rb",
    "stake f1 team kick sauber": "kick sauber",
    "moneygram haas f1 team": "haas",
    "williams racing": "williams",
    "bwt alpine f1 team": "alpine",
    "voltedge quantum racing": "voltedge",
}


def get_text_color(bg):
    try:
        r = int(bg[1:3], 16)
        g = int(bg[3:5], 16)
        b = int(bg[5:7], 16)
    except:
        return "black"

    yiq = (r*299 + g*587 + b*114)/1000
    return "white" if yiq < 150 else "black"


# =========================
# РАСКРАСКА ТАБЛИЦ
# =========================
def colorize_table(df: pd.DataFrame):
    df = df.copy()

    team_col = find_column(df, ["команда", "team"])

    if team_col:
        normalized = df[team_col].astype(str).apply(normalize_match)
        mapped = normalized.map(TEAM_MAP).fillna(normalized)
        df["__color__"] = mapped.map(TEAM_COLORS).fillna("#FFFFFF")
    else:
        df["__color__"] = "#FFFFFF"

    colors = df["__color__"]
    out = df.drop(columns=["__color__"], errors="ignore")

    def style_row(row):
        bg = colors.iloc[row.name]
        fg = get_text_color(bg)
        return [f"background-color:{bg}; color:{fg}" for _ in row]

    return out.style.apply(style_row, axis=1).hide(axis="index")


# =========================
# ПИЛОТ → КОМАНДА
# =========================
def build_pilot_team_map(teams_df):
    pilot_col = find_column(teams_df, ["pilot", "пилот"])
    team_col  = find_column(teams_df, ["команда", "team"])

    mapping = {}
    for _, row in teams_df.iterrows():
        p = str(row[pilot_col])
        t = normalize_match(str(row[team_col]))
        t = TEAM_MAP.get(t, t)
        mapping[p] = t
    return mapping


# =========================
# ЛУЧШИЙ КРУГ
# =========================
def parse_lap_time(v):
    if not isinstance(v, str):
        return pd.NaT
    s = normalize_match(v)
    if any(x in s for x in ["dnf", "lap", "выб"]):
        return pd.NaT
    try:
        return pd.to_timedelta(v)
    except:
        return pd.NaT


# =========================
# ПОЛНЫЙ ПАРСЕР СЕЗОНА
# =========================
def load_season_data(xls_path):
    xls = pd.ExcelFile(xls_path)
    season_year = xls_path.split("_")[-1].split(".")[0]

    # ---------- ЧТЕНИЕ GP LIST ----------
    gp_df = pd.read_excel(xls, f"GP_List_{season_year}")

    code_col = find_column(gp_df, ["код", "code"])
    name_col = find_column(gp_df, ["назв", "name"])

    gp_list = dict(zip(
        gp_df[code_col].astype(str).str.strip(),
        gp_df[name_col].astype(str).str.strip()
    ))

    # ---------- WDC / WCC / TEAMS ----------
    wdc = pd.read_excel(xls, f"WDC_{season_year}")
    wcc = pd.read_excel(xls, f"WCC_{season_year}")
    teams = pd.read_excel(xls, f"Teams_{season_year}")

    # ---------- ПАРСЕР ГРАН-ПРИ ----------
    grand_prix = {}

    for code in gp_list:
        if code not in xls.sheet_names:
            grand_prix[code] = {}
            continue

        df = pd.read_excel(xls, code, header=None)
        sections = {}
        key = None
        temp = []
        skip_header = False

        for _, row in df.iterrows():
            row_text = " ".join(
                normalize_match(str(x)) for x in row.values if pd.notna(x)
            )

            if row_text == "":
                continue

            if any(x in row_text for x in ["qualificat", "qualification", "qualify", "квалиф"]):
                if key and temp:
                    sections[key] = pd.DataFrame(temp)
                key = "qualifying"
                temp = []
                skip_header = True
                continue

            if "race_drivers" in row_text:
                if key and temp:
                    sections[key] = pd.DataFrame(temp)
                key = "race_drivers"
                temp = []
                skip_header = True
                continue

            if "race_teams" in row_text:
                if key and temp:
                    sections[key] = pd.DataFrame(temp)
                key = "race_teams"
                temp = []
                skip_header = True
                continue

            if skip_header:
                skip_header = False
                continue

            if key:
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
