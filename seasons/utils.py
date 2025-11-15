import pandas as pd
import numpy as np

# ===========================
# Цвета команд
# ===========================
TEAM_COLORS = {
    "Ferrari": "#DC0000",
    "Red Bull": "#1E41FF",
    "Mercedes": "#00D2BE",
    "McLaren": "#FF8700",
    "Aston Martin": "#006F62",
    "RB": "#B9DCFF",
    "Haas": "#B6BABD",
    "Williams": "#018CFF",
    "Kick Sauber": "#52E252",
    "Alpine": "#0090FF",
    "VoltEdge": "#F4EA00",
}

TEAM_MAP = {
    "Oracle Red Bull Racing": "Red Bull",
    "Mercedes-AMG PETRONAS Formula One Team": "Mercedes",
    "Scuderia Ferrari HP": "Ferrari",
    "McLaren Formula 1 Team": "McLaren",
    "Aston Martin Aramco Formula One Team": "Aston Martin",
    "BWT Alpine F1 Team": "Alpine",
    "Visa Cash App RB Formula One Team": "RB",
    "Stake F1 Team Kick Sauber": "Kick Sauber",
    "MoneyGram Haas F1 Team": "Haas",
    "Williams Racing": "Williams",
    "VoltEdge Quantum Racing": "VoltEdge",
}

# ===========================
# Нормализация строк/колонок
# ===========================
def normalize_df(df: pd.DataFrame):
    df = df.copy()
    df.columns = [str(c).replace("\xa0", " ").strip() for c in df.columns]
    df = df.applymap(lambda x: str(x).replace("\xa0", " ").strip()
                     if isinstance(x, str) else x)
    return df


# ===========================
# Поиск колонки по ключевым словам
# ===========================
def find_column(df, keywords):
    for col in df.columns:
        norm = col.lower().replace(" ", "")
        for key in keywords:
            if key in norm:
                return col
    return None


# ===========================
# Парсинг лучшего круга
# ===========================
def parse_lap(val):
    if not isinstance(val, str):
        return pd.NaT
    s = val.lower()
    if any(bad in s for bad in ["круг", "dnf", "выб"]):
        return pd.NaT
    try:
        return pd.to_timedelta(val)
    except:
        return pd.NaT


# ===========================
# Цвет текста под фон
# ===========================
def get_text_color(bg):
    if not isinstance(bg, str) or not bg.startswith("#"):
        return "black"
    r = int(bg[1:3], 16)
    g = int(bg[3:5], 16)
    b = int(bg[5:7], 16)
    yiq = (r*299 + g*587 + b*114) / 1000
    return "white" if yiq < 150 else "black"


# ===========================
# Окраска таблиц
# ===========================
def colorize(df):
    if df is None or df.empty:
        return df

    df = normalize_df(df)

    # ищем колонку команды
    team_col = find_column(df, ["команда", "team"])

    if team_col:
        df["__team__"] = df[team_col].map(TEAM_MAP).fillna(df[team_col])
        df["__color__"] = df["__team__"].map(TEAM_COLORS).fillna("#FFFFFF")
    else:
        df["__color__"] = "#FFFFFF"

    row_colors = df["__color__"]
    display_df = df.drop(columns=["__color__", "__team__"], errors="ignore")

    def style_row(row):
        bg = row_colors.iloc[row.name]
        fg = get_text_color(bg)
        return [f"background-color:{bg}; color:{fg}" for _ in row]

    return display_df.style.apply(style_row, axis=1)


# ===========================
# Построение маппинга Пилот→Команда
# ===========================
def build_pilot_team_map(teams_df):
    teams_df = normalize_df(teams_df)
    mapping = {}

    pilot_cols = [c for c in teams_df.columns if "илот" in c.lower()]

    for _, row in teams_df.iterrows():
        team_name = row["Команда"]
        for col in pilot_cols:
            pilot = row[col]
            if isinstance(pilot, str) and pilot.strip():
                mapping[pilot.strip()] = team_name

    return mapping


# ===========================
# Чтение Excel сезона
# ===========================
def load_season_data(path, year):
    xls = pd.ExcelFile(path)

    # ❗ теперь корректно
    gp_list = pd.read_excel(xls, f"GP_List_{year}")
    gp_list = normalize_df(gp_list)

    teams = pd.read_excel(xls, f"Teams_{year}")
    wdc = pd.read_excel(xls, f"WDC_{year}")
    wcc = pd.read_excel(xls, f"WCC_{year}")

    grand_prix = {}

    for sheet in xls.sheet_names:
        # листы гонок — все коды вроде 'BAH', 'MIA', 'SPA', 'JPN'
        if sheet.isupper() and "_" not in sheet and len(sheet) <= 4:
            gp = pd.read_excel(xls, sheet, header=None)
            grand_prix[sheet] = {"raw": gp}

    return {
        "teams": teams,
        "wdc": wdc,
        "wcc": wcc,
        "gp_list": gp_list,
        "grand_prix": grand_prix,
    }
