import streamlit as st
import pandas as pd
import numpy as np

# =========================
#  Цвета команд (короткие имена)
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
    "VoltEdge": "#F4EA00",  # твоя кастомная команда
}

# Мэппинг длинных официальных названий → коротких
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
#  Цвет текста под цвет фона
# =========================
def get_text_color(bg: str) -> str:
    if not isinstance(bg, str) or not bg.startswith("#") or len(bg) != 7:
        return "black"
    try:
        r = int(bg[1:3], 16)
        g = int(bg[3:5], 16)
        b = int(bg[5:7], 16)
    except Exception:
        return "black"

    yiq = (r * 299 + g * 587 + b * 114) / 1000
    return "white" if yiq < 140 else "black"


# =========================
#  Окраска таблиц
# =========================
def colorize_table(df: pd.DataFrame):
    if df is None or len(df) == 0:
        return df

    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]

    # Ищем колонку, где хранится команда (Команда, Команды\Гонки, etc)
    team_col = None
    for col in df.columns:
        if "Команда" in str(col):
            team_col = col
            break

    if team_col is not None:
        df["__team__"] = df[team_col].map(TEAM_MAP).fillna(df[team_col])
        df["__color__"] = df["__team__"].map(TEAM_COLORS).fillna("#FFFFFF")
    else:
        df["__color__"] = "#FFFFFF"

    # Сбрасываем индексы, чтобы стили и данные совпали
    df = df.reset_index(drop=True)
    row_colors = df["__color__"].copy()
    display_df = df.drop(columns=["__color__"])

    def row_style(row):
        idx = row.name
        bg = row_colors.iloc[idx]
        fg = get_text_color(bg)
        return [f"background-color: {bg}; color: {fg}" for _ in row]

    styles = [
        dict(selector="th", props=[("background-color", "#222"), ("color", "white")]),
        dict(selector="td", props=[("padding", "6px")]),
    ]

    return (
        display_df.style
        .apply(row_style, axis=1)
        .set_table_styles(styles)
        .hide(axis="index")
    )


# =========================
#  Безопасный парсер лучшего круга
# =========================
def parse_lap_time(val):
    try:
        # Обрезаем всякую ерунду типа '+1 круг', 'выбыл' и т.п.
        if isinstance(val, str) and ("круг" in val.lower() or "DNF" in val or "выб" in val.lower()):
            return pd.NaT
        return pd.to_timedelta(val)
    except Exception:
        return pd.NaT


# =========================
#  Основной рендер сезона
# =========================
def render_season_2024(
    qualifying, race_drivers, race_teams, wdc, wcc, teams, race_name
):

    st.title("Сезон Формулы-1 2024")

    tab_gp, tab_wdc, tab_wcc, tab_teams = st.tabs(
        ["Гран-при", "WDC", "WCC", "Команды"]
    )

    # ---------- Гран-при ----------
    with tab_gp:
        st.subheader(f"Гран-при {race_name}")

        # Квалификация — с цветами команд
        st.subheader("Квалификация")
        st.write(colorize_table(qualifying))

        # Гонка — пилоты (фиолетовый лучший круг)
        st.subheader("Гонка — пилоты")

        df = race_drivers.copy()
        df.columns = [str(c).strip() for c in df.columns]

        if "Лучший круг" in df.columns:
            times = df["Лучший круг"].apply(parse_lap_time)
            min_time = times.min()

            def style_fastest(row):
                try:
                    t = parse_lap_time(row["Лучший круг"])
                    if pd.notna(t) and t == min_time:
                        return [
                            "background-color: #8847BD; color: white; font-weight: bold"
                            for _ in row
                        ]
                    return [""] * len(row)
                except Exception:
                    return [""] * len(row)

            df = df.reset_index(drop=True)
            st.write(df.style.apply(style_fastest, axis=1))
        else:
            st.write(df)

        # Гонка — команды (с цветами)
        st.subheader("Гонка — команды")
        st.write(colorize_table(race_teams))

    # ---------- WDC ----------
    with tab_wdc:
        st.subheader("Пилоты — WDC 2024")
        # здесь нет колонки с командой → цвет будет белый, но числа уже int
        st.write(colorize_table(wdc))

    # ---------- WCC ----------
    with tab_wcc:
        st.subheader("Команды — WCC 2024")
        # есть колонка 'Команды\Гонки' → будет цвет по командам
        st.write(colorize_table(wcc))

    # ---------- Составы ----------
    with tab_teams:
        st.subheader("Составы команд")
        st.write(colorize_table(teams))
