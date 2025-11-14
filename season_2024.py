import streamlit as st
import pandas as pd
import numpy as np


# ============================================================
#  Палитра команд
# ============================================================

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


# ============================================================
#  Утилиты нормализации
# ============================================================

def normalize_str(x):
    """Очищаем строки, но НЕ меняем регистр и НЕ lower()"""
    if not isinstance(x, str):
        return x
    return (
        x.replace("\xa0", " ")
         .replace("\u200b", "")
         .replace("\ufeff", "")
         .strip()
    )


def normalize_cols(df):
    """Нормализует только заголовки (названия колонок)"""
    df = df.copy()
    df.columns = [normalize_str(c) for c in df.columns]
    return df


def find_column(df, keywords):
    """Ищет колонку по набору фрагментов текста"""
    for col in df.columns:
        col_n = col.lower()
        if any(key in col_n for key in keywords):
            return col
    return None


# ============================================================
#  Цвет текста для контраста
# ============================================================

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


# ============================================================
#  Табличная раскраска по командам
# ============================================================

def colorize_table(df):
    if df is None or df.empty:
        return df

    df = df.copy()

    # нормализуем только заголовки
    df = normalize_cols(df)

    # Ищем колонку с командой
    team_col = find_column(df, ["команда", "team"])

    if team_col:
        team_names = df[team_col].astype(str).apply(normalize_str)
        df["__team__"] = team_names.map(TEAM_MAP).fillna(team_names)
        df["__color__"] = df["__team__"].map(TEAM_COLORS).fillna("#FFFFFF")
    else:
        df["__color__"] = "#FFFFFF"

    df = df.reset_index(drop=True)
    colors = df["__color__"]

    display_df = df.drop(columns=["__color__", "__team__"], errors="ignore")

    def row_style(row):
        bg = colors.iloc[row.name]
        fg = get_text_color(bg)
        return [f"background-color:{bg}; color:{fg}" for _ in row]

    return (
        display_df.style
        .apply(row_style, axis=1)
        .hide(axis="index")
    )


# ============================================================
#  Парсинг лучшего круга
# ============================================================

def parse_lap_time(val):
    if not isinstance(val, str):
        return pd.NaT
    s = normalize_str(val)
    s_low = s.lower()

    # не-круги
    if any(x in s_low for x in ["круг", "выб", "dnf", "+1", "lap+1"]):
        return pd.NaT

    try:
        return pd.to_timedelta(s)
    except:
        return pd.NaT


# ============================================================
#  Основной рендер сезона 2024
# ============================================================

def render_season_2024(
    qualifying, race_drivers, race_teams,
    wdc, wcc, teams, race_name
):

    st.title("Сезон Формулы-1 2024")

    tab_gp, tab_wdc, tab_wcc, tab_teams = st.tabs(
        ["Гран-при", "WDC", "WCC", "Команды"]
    )

    # ============================================================
    #  ГРАН-ПРИ
    # ============================================================

    with tab_gp:
        st.subheader(f"Гран-при {race_name}")

        # ------- Квалификация -------
        st.subheader("Квалификация")
        st.write(colorize_table(qualifying))

        # ------- Гонка — пилоты -------
        st.subheader("Гонка — пилоты")

        df = race_drivers.copy()
        df = normalize_cols(df)

        lap_col = find_column(df, ["лучший", "best", "lap"])

        if lap_col:
            laps = df[lap_col].apply(parse_lap_time)
            valid = laps.dropna()

            if not valid.empty:
                min_lap = valid.min()
                fastest_mask = laps == min_lap

                # командная раскраска
                styled = colorize_table(df)

                # подсветка лучшего круга поверх цвета команды
                def highlight(col):
                    if col.name != lap_col:
                        return [""] * len(col)
                    return [
                        "background-color:#8847BD; color:white; font-weight:bold"
                        if fastest_mask.iloc[i] else ""
                        for i in range(len(col))
                    ]

                styled = styled.apply(highlight, axis=0)

                st.write(styled)
            else:
                st.write(colorize_table(df))
        else:
            st.write(colorize_table(df))

        # ------- Гонка — команды -------
        st.subheader("Гонка — команды")
        st.write(colorize_table(race_teams))

    # ============================================================
    #  WDC
    # ============================================================

    with tab_wdc:
        st.subheader("Пилоты — WDC 2024")

        wdc = normalize_cols(wdc).copy()

        pilot_col = find_column(wdc, ["пилот", "гонки", "driver"])
        team_pilot_col = find_column(teams, ["пилот", "driver"])
        team_team_col = find_column(teams, ["команда", "team"])

        if pilot_col and team_pilot_col and team_team_col:
            pilot_to_team = dict(zip(teams[team_pilot_col], teams[team_team_col]))
            wdc["Команда"] = wdc[pilot_col].map(pilot_to_team)

        st.write(colorize_table(wdc))

    # ============================================================
    #  WCC
    # ============================================================

    with tab_wcc:
        st.subheader("Команды — WCC 2024")
        st.write(colorize_table(wcc))

    # ============================================================
    #  Команды
    # ============================================================

    with tab_teams:
        st.subheader("Составы команд")
        st.write(colorize_table(teams))
