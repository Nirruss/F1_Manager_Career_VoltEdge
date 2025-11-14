import streamlit as st
import pandas as pd
import numpy as np

# =========================
#  Цвета команд (по коротким названиям)
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
    # твоя кастомная команда
    "VoltEdge": "#F4EA00",
}

# Мэппинг длинных названий из Excel → коротких, понятных словарю TEAM_COLORS
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


# =========================
#  Подбор цвета текста под цвет фона
# =========================
def get_text_color(bg: str) -> str:
    """
    Возвращает 'white' или 'black' в зависимости от яркости фона bg (#RRGGBB).
    """
    if not isinstance(bg, str) or not bg.startswith("#") or len(bg) != 7:
        return "black"
    try:
        r = int(bg[1:3], 16)
        g = int(bg[3:5], 16)
        b = int(bg[5:7], 16)
    except Exception:
        return "black"

    # формула YIQ — грубая оценка яркости
    yiq = (r * 299 + g * 587 + b * 114) / 1000
    # чем меньше значение, тем темнее фон
    return "white" if yiq < 140 else "black"


# =========================
#  Окраска таблиц командных данных
# =========================
def colorize_table(df: pd.DataFrame):
    if df is None or len(df) == 0:
        return df

    df = df.copy()

    # Нормализуем названия колонок
    df.columns = [str(c).strip() for c in df.columns]

    # Приводим названия команд к коротким и задаём цвет
    if "Команда" in df.columns:
        df["Команда"] = df["Команда"].map(TEAM_MAP).fillna(df["Команда"])
        df["color"] = df["Команда"].map(TEAM_COLORS).fillna("#FFFFFF")
    else:
        df["color"] = "#FFFFFF"

    styles = [
        dict(selector="th", props=[("background-color", "#222",), ("color", "white")]),
        dict(selector="td", props=[("padding", "6px")]),
    ]

    def row_style(row):
        bg = row["color"]
        fg = get_text_color(bg)
        return [f"background-color: {bg}; color: {fg}" for _ in row]

    return (
        df.style.apply(row_style, axis=1)
        .set_table_styles(styles)
        .hide(axis="index")
        .hide(columns=["color"])
    )


# =========================
#  Основной рендер сезона
# =========================
def render_season_2024(
    qualifying, race_drivers, race_teams, wdc, wcc, teams, race_name
):

    st.title("Сезон Формулы-1 2024")

    tabs = st.tabs(["Гран-при", "WDC", "WCC", "Команды"])
    tab_gp, tab_wdc, tab_wcc, tab_teams = tabs

    # ---------- Гран-при ----------
    with tab_gp:
        st.subheader(f"Гран-при {race_name}")

        # Квалификация — с цветами команд
        st.subheader("Квалификация")
        st.write(colorize_table(qualifying))

        # Гонка: пилоты — только фиолетовый лучший круг
        st.subheader("Гонка — пилоты")

        df = race_drivers.copy()
        df.columns = [str(c).strip() for c in df.columns]

        if "Лучший круг" in df.columns:
            try:
                times = pd.to_timedelta(df["Лучший круг"])
                min_time = times.min()

                def style_fastest(row):
                    try:
                        if pd.to_timedelta(row["Лучший круг"]) == min_time:
                            return [
                                "background-color: #8847BD; color: white"
                                for _ in row
                            ]
                        return [""] * len(row)
                    except Exception:
                        return [""] * len(row)

                st.write(df.style.apply(style_fastest, axis=1))
            except Exception:
                st.write(df)
        else:
            st.write(df)

        # Гонка: команды — с цветами команд
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

    # ---------- Составы ----------
    with tab_teams:
        st.subheader("Составы команд")
        st.write(colorize_table(teams))
