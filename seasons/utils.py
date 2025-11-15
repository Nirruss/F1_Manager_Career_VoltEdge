import pandas as pd
import re

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

def normalize_df(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    df = df.applymap(lambda x: str(x).replace("\xa0", " ").strip()
                     if isinstance(x, str) else x)
    return df


def get_text_color(bg):
    if not isinstance(bg, str) or not bg.startswith("#"):
        return "black"
    r = int(bg[1:3], 16)
    g = int(bg[3:5], 16)
    b = int(bg[5:7], 16)
    yiq = (r*299 + g*587 + b*114) / 1000
    return "white" if yiq < 150 else "black"


def colorize(df: pd.DataFrame):
    df = normalize_df(df)

    # ищем колонку команды
    team_col = None
    for c in df.columns:
        if "Команда" in c or "Teams" in c or "Гонки" in c:
            team_col = c
            break

    if team_col:
        df["_team"] = df[team_col].map(TEAM_MAP).fillna(df[team_col])
        df["_color"] = df["_team"].map(TEAM_COLORS).fillna("#FFFFFF")
    else:
        df["_color"] = "#FFFFFF"

    df = df.reset_index(drop=True)
    row_colors = df["_color"]

    df_disp = df.drop(columns=["_color", "_team"], errors="ignore")

    def row_style(row):
        bg = row_colors.iloc[row.name]
        fg = get_text_color(bg)
        return [f"background-color:{bg};color:{fg}" for _ in row]

    return df_disp.style.apply(row_style, axis=1)


def parse_lap(val):
    if not isinstance(val, str):
        return pd.NaT
    s = val.lower().strip()
    if any(x in s for x in ["круг", "выб", "dnf"]):
        return pd.NaT
    try:
        return pd.to_timedelta(val)
    except:
        return pd.NaT
