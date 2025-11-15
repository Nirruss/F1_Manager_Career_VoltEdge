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
    s = re.sub(r"\s+", " ", s)
    return s.lower()


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
    "scuderia ferrari hp": "ferrari",
    "oracle red bull racing": "red bull",
    "mercedes-amg petronas formula one team": "mercedes",
    "mclaren formula 1 team": "mclaren",
    "aston martin aramco formula one team": "aston martin",
    "bwt alpine f1 team": "alpine",
    "visa cash app rb formula one team": "rb",
    "stake f1 team kick sauber": "kick sauber",
    "moneygram haas f1 team": "haas",
    "williams racing": "williams",
    "voltedge quantum racing": "voltedge",
}


# =========================
# ПРОВЕРКА КОНТРАСТА
# =========================
def get_text_color(bg):
    try:
        r = int(bg[1:3], 16)
        g = int(bg[3:5], 16)
        b = int(bg[5:7], 16)
    except:
        return "black"

    yiq = (r*299 + g*587 + b*114) / 1000
    return "white" if yiq < 150 else "black"


# =========================
# РАСКРАСКА ТАБЛИЦ
# =========================
def colorize_table(df: pd.DataFrame):
    df = df.copy()

    team_col = find_column(df, ["команда", "team"])

    if team_col:
        norm = df[team_col].astype(str).apply(normalize_match)
        mapped = norm.map(TEAM_MAP).fillna(norm)
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
    pilot_col = find_column(teams_df, ["пилот", "driver"])
    team_col  = find_column(teams_df, ["команда", "team"])

    mapping = {}
    for _, row in teams_df.iterrows():
        p = str(row[pilot_col])
        t = normalize_match(str(row[team_col]))
        t = TEAM_MAP.get(t, t)
        mapping[p] = t
    return mapping


# =========================
# ПАРСЕР ЛУЧШЕГО КРУГА
# =========================
def parse_lap_time(v):
    if not isinstance(v, str):
        return pd.NaT
    s = normalize_match(v)
    if any(x in s for x in ["dnf", "выб", "lap"]):
        return pd.NaT
    try:
        return pd.to_timedelta(v)
    except:
        return pd.NaT


# =========================
# ГЛАВНАЯ ФУНКЦИЯ ЗАГРУЗКИ СЕЗОНА
# =========================
def load_season_data(xls_path):
    xls = pd.ExcelFile(xls_path)
    season_year = xls_path.split("_")[-1].split(".")[0]

    # -------- ЧТЕНИЕ GP_LIST --------
    gp_df = pd.read_excel(xls, f"GP_List_{season_year}")

    # Чем бы ни назвались колонки → ищем по смыслу
    code_col = find_column(gp_df, ["код", "code"])
    name_col = find_column(gp_df, ["назв", "name"])

    gp_list = dict(zip(
        gp_df[code_col].astype(str).str.strip(),
        gp_df[name_col].astype(str).str.strip(),
    ))

    # -------- Остальные листы --------
    wdc = pd.read_excel(xls, f"WDC_{season_year}")
    wcc = pd.read_excel(xls, f"WCC_{season_year}")
    teams = pd.read_excel(xls, f"Teams_{season_year}")

    # -------- Парсер гонок оставляем как у тебя --------
    grand_prix = {}
    for code in gp_list:
        grand_prix[code] = {}

    return {
        "gp_map": gp_list,
        "gp_list": gp_list,
        "grand_prix": grand_prix,
        "wdc": wdc,
        "wcc": wcc,
        "teams": teams,
    }
