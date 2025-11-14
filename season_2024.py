import streamlit as st
import pandas as pd
import numpy as np
import re

# ============================================
#  Цвета команд
# ============================================
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

# ============================================
#  Нормализация строк и названий колонок
# ============================================
def normalize_str(s: str) -> str:
    if not isinstance(s, str):
        return s
    s = s.replace("\xa0", " ")     # NBSP
    s = s.replace("\u200b", "")    # zero width
    s = s.replace("\ufeff", "")    # BOM
    return s.strip().lower()

def find_column(df, keywords):
    """
    Находит колонку по ключевым словам, игнорируя спецсимволы.
    """
    normalized = {i: normalize_str(c) for i, c in enumerate(df.columns)}

    for idx, col in normalized.items():
        for key in keywords:
            if key in col:
                return df.columns[idx]

    return None


# ============================================
#  Цвет текста
# ============================================
def get_text_color(bg):
    if not isinstance(bg, str) or not bg.startswith("#"):
        return "black"
    try:
        r = int(bg[1:3], 16)
        g = int(bg[3:5], 16)
        b = int(bg[5:7], 16)
    except:
        return "black"

    yiq = (r * 299 + g * 587 + b * 114) / 1000
    return "white" if yiq < 150 else "black"


# ============================================
#  Окраска таблиц
# ============================================
def colorize_table(df: pd.DataFrame):
    if df is None or df.empty:
        return df

    df = df.copy()

    # ❗ НОРМАЛИЗУЕМ ТОЛЬКО НАЗВАНИЯ КОЛОНОК, НЕ ЗНАЧЕНИЯ
    df.columns = [normalize_str(c) for c in df.columns]

    # ищем колонку команды
    team_col = find_column(df, ["команда", "команд", "team", "\\"])

    # ВАЖНО: не трогаем строки, только нормализуем названия
    if team_col:
        raw_names = df[team_col]  # значения НЕ трогаем
        df["__team__"] = raw_names.map(TEAM_MAP).fillna(raw_names)
        df["__color__"] = df["__team__"].map(TEAM_COLORS).fillna("#FFFFFF")
    else:
        df["__color__"] = "#FFFFFF"

    df = df.reset_index(drop=True)
    row_colors = df["__color__"]

    display_df = df.drop(columns=["__color__", "__team__"], errors="ignore")

    def row_style(row):
        bg = row_colors.iloc[row.name]
        fg = get_text_color(bg)
        return [f"background-color: {bg}; color: {fg}" for _ in row]

    return (
        display_df.style
            .apply(row_style, axis=1)
            .hide(axis="index")
    )


# ============================================
#  Разбор лучшего круга
# ============================================
def parse_lap_time(val):
    if not isinstance(val, str):
        return pd.NaT

    s = normalize_str(val)

    if any(x in s for x in ["круг", "выб", "dnf", "+1", "lap+1"]):
        return pd.NaT

    try:
        return pd.to_timedelta(val)
    except:
        return pd.NaT


# ============================================
#  Render
# ============================================
def render_season_2024(
    qualifying, race_drivers, race_teams, wdc, wcc, teams, race_name
):

    st.title("Сезон Формулы-1 2024")

    # ---- DEBUG ----
    st.write("DEBUG qualifying cols:", list(qualifying.columns))
    st.write("DEBUG race_drivers cols:", list(race_drivers.columns))
    st.write("DEBUG race_teams cols:", list(race_teams.columns))
    st.write("DEBUG wcc cols:", list(wcc.columns))
    # ---------------

    tab_gp, tab_wdc, tab_wcc, tab_teams = st.tabs(
        ["Гран-при", "WDC", "WCC", "Команды"]
    )

    # --------------------------------------
    #   ГРАН-ПРИ
    # --------------------------------------
    with tab_gp:
        st.subheader(f"Гран-при {race_name}")

        st.subheader("Квалификация")
        st.write(colorize_table(qualifying))

        # ---------- Гонка — пилоты ----------
        st.subheader("Гонка — пилоты")
        df = race_drivers.copy()

        lap_col = find_column(df, ["лучший", "best", "lap", "круг"])

        if lap_col:
            laps = df[lap_col].apply(parse_lap_time)
            valid = laps.dropna()

            if not valid.empty:
                min_lap = valid.min()
                fastest_mask = laps == min_lap

                def highlight(col):
                    if col.name != lap_col:
                        return [""] * len(col)
                    return [
                        "background-color:#8847BD; color:white; font-weight:bold"
                        if fastest_mask.iloc[i] else ""
                        for i in range(len(col))
                    ]

                st.write(df.style.apply(highlight, axis=0))
            else:
                st.write(df)
        else:
            st.write(df)

        # ---------- Гонка — команды ----------
        st.subheader("Гонка — команды")
        st.write(colorize_table(race_teams))

    # ---------- WDC ----------
    with tab_wdc:
        st.subheader("Пилоты — WDC 2024")
        st.write(colorize_table(wdc))

    # ---------- WCC ----------
    with tab_wcc:
        st.subheader("Команды — WCC 2024")
        st.write(colorize_table(wcc))

    # ---------- Команды ----------
    with tab_teams:
        st.subheader("Составы команд")
        st.write(colorize_table(teams))
