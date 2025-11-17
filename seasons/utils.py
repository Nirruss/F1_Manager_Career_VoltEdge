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

    # форматируем числа красиво
    def format_int_like(x):
        # NaN / пустые
        if pd.isna(x):
            return ""
        # уже целое
        if isinstance(x, (int, np.integer)):
            return str(x)
        # число с плавающей точкой
        if isinstance(x, (float, np.floating)):
            v = float(x)
            # если это на самом деле целое (25.0, 7.0 и т.п.)
            if abs(v - round(v)) < 1e-9:
                return str(int(round(v)))
            else:
                # на всякий случай для нецелых (если где-то появятся)
                return f"{v:.3f}".rstrip("0").rstrip(".")
        # строки типа "DNF" и всё остальное оставляем как есть
        return x

    styler = out.style.apply(style_row, axis=1).hide(axis="index")
    styler = styler.format(format_int_like)

    return styler



# =========================
# ПИЛОТ → КОМАНДА
# =========================
def build_pilot_team_map(teams_df):
    # колонка с названием команды
    team_col = find_column(teams_df, ["команда", "team"])
    if team_col is None:
        return {}

    # все колонки, в которых есть слово "пилот" / "pilot"
    pilot_cols = []
    for col in teams_df.columns:
        cname = normalize_match(col)
        if "пилот" in cname or "pilot" in cname:
            pilot_cols.append(col)

    mapping = {}
    for _, row in teams_df.iterrows():
        team_raw = str(row[team_col])
        team_norm = normalize_match(team_raw)
        team_key = TEAM_MAP.get(team_norm, team_norm)

        for col in pilot_cols:
            name = row[col]
            if pd.isna(name):
                continue
            mapping[str(name)] = team_key

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
    """
    Унифицированный загрузчик сезона.
    Берём корректный парсер из loader.load_season,
    но возвращаем структуру, которую ожидает app.py.
    """
    try:
        from .loader import load_season
    except ImportError:
        from loader import load_season

    parsed = load_season(xls_path)

    # -----------------------------
    # Приводим к формату, который ждёт app.py
    # -----------------------------
    season_data = {
        "teams": parsed["teams"],
        "wdc": parsed["wdc"],
        "wcc": parsed["wcc"],

        # старый app.py ожидает gp_map и gp_list
        "gp_map": parsed["gp_code_to_name"],     # словарь: CODE -> NAME
        "gp_list": parsed["gp_codes"],           # список кодов гонок

        # основной блок с разрезанными таблицами
        "grand_prix": parsed["grand_prix"],
    }

    return season_data
