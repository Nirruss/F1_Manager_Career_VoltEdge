import streamlit as st
import pandas as pd
import numpy as np

# =========================
#  Цвета команд
# =========================
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
}


# =========================
#  Окраска таблиц командных данных
# =========================
def colorize_table(df):
    if df is None or len(df) == 0:
        return df

    df = df.copy()

    # Нормализуем названия колонок (убираем пробелы, скрытые символы)
    df.columns = [str(c).strip() for c in df.columns]

    # Добавляем цвет команд
    if "Команда" in df.columns:
        df["color"] = df["Команда"].map(TEAM_COLORS).fillna("#FFFFFF")
    else:
        df["color"] = "#FFFFFF"

    styles = [
        dict(selector="th", props=[("background-color", "#222"), ("color", "white")]),
        dict(selector="td", props=[("padding", "6px")]),
    ]

    return df.style.apply(
        lambda row: [f"background-color: {row['color']}; color: black" for _ in row],
        axis=1
    ).set_table_styles(styles).hide(axis="index")


# =========================
#  Основной рендер сезона 2024
# =========================
def render_season_2024(
    qualifying, race_drivers, race_teams, wdc, wcc, teams, race_name
):

    st.title("Сезон Формулы-1 2024")

    tabs = st.tabs(["Гран-при", "WDC", "WCC", "Команды"])
    tab_gp, tab_wdc, tab_wcc, tab_teams = tabs

    # =========================
    #  Гран-при
    # =========================
    with tab_gp:
        st.subheader(f"Гран-при {race_name}")

        # -------------------------
        # Квалификация — раскрашена по командам
        # -------------------------
        st.subheader("Квалификация")
        st.write(colorize_table(qualifying))

        # -------------------------
        # Гонка: пилоты — БЕЗ раскраски команд, только фиолетовый лучший круг
        # -------------------------
        st.subheader("Гонка — пилоты")

        df = race_drivers.copy()
        df.columns = [str(c).strip() for c in df.columns]

        if "Лучший круг" in df.columns:
            try:
                times = pd.to_timedelta(df["Лучший круг"])
                min_time = times.min()

                def style_fastest(row):
                    try:
                        t = pd.to_timedelta(row["Лучший круг"])
                        if t == min_time:
                            return [
                                "background-color: #8847BD; color: white; font-weight: bold"
                                for _ in row
                            ]
                        else:
                            return [""] * len(row)
                    except:
                        return [""] * len(row)

                st.write(df.style.apply(style_fastest, axis=1))

            except Exception:
                st.write(df)
        else:
            st.write(df)

        # -------------------------
        # Гонка: команды — раскрашена по командам
        # -------------------------
        st.subheader("Гонка — команды")
        st.write(colorize_table(race_teams))

    # =========================
    #  WDC
    # =========================
    with tab_wdc:
        st.subheader("Пилоты — WDC 2024")
        st.write(colorize_table(wdc))

    # =========================
    #  WCC
    # =========================
    with tab_wcc:
        st.subheader("Команды — WCC 2024")
        st.write(colorize_table(wcc))

    # =========================
    #  Составы команд
    # =========================
    with tab_teams:
        st.subheader("Составы команд")
        st.write(colorize_table(teams))
