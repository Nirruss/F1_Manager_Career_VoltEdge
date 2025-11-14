import streamlit as st
import pandas as pd
import numpy as np
import re


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
#  Нормализация строк и поиск колонок
# ============================================================

def normalize_str(x: str) -> str:
    """Чистим мусорные символы, не меняя регистр."""
    if not isinstance(x, str):
        return x
    return (
        x.replace("\xa0", " ")   # NBSP
         .replace("\u200b", "")  # zero-width
         .replace("\ufeff", "")  # BOM
         .strip()
    )


def normalize_cols(df: pd.DataFrame) -> pd.DataFrame:
    """Нормализуем только заголовки, данные не трогаем."""
    df = df.copy()
    df.columns = [normalize_str(c) for c in df.columns]
    return df


def find_column(df: pd.DataFrame, keywords) -> str | None:
    """Ищем колонку по набору подстрок (регистр игнорируем)."""
    for col in df.columns:
        low = str(col).lower()
        if any(k in low for k in keywords):
            return col
    return None


# ============================================================
#  Цвет текста под фон
# ============================================================

def get_text_color(bg: str) -> str:
    if not isinstance(bg, str) or not bg.startswith("#"):
        return "black"
    try:
        r = int(bg[1:3], 16)
        g = int(bg[3:5], 16)
        b = int(bg[5:7], 16)
    except Exception:
        return "black"

    yiq = (r * 299 + g * 587 + b * 114) / 1000
    return "white" if yiq < 150 else "black"


# ============================================================
#  Общая раскраска таблиц по командам
# ============================================================

def colorize_table(df: pd.DataFrame):
    if df is None or df.empty:
        return df

    df = normalize_cols(df)
    df = df.copy()

    # Пытаемся найти столбец с командой
    team_col = find_column(df, ["команда", "команд", "team"])

    if team_col:
        team_raw = df[team_col].astype(str).apply(normalize_str)
        df["__team__"] = team_raw.map(TEAM_MAP).fillna(team_raw)
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


# ============================================================
#  Парсер и маска лучшего круга (новая система)
# ============================================================

def lap_to_ms(s: str) -> int | None:
    """
    Превращаем строку вида '1:33.256' или '1:33,256' в миллисекунды.
    Если не похоже на время круга — возвращаем None.
    """
    if not isinstance(s, str):
        return None

    s_clean = normalize_str(s).lower()

    # Отбрасываем "+1 круг", DNF и т.п.
    if any(x in s_clean for x in ["круг", "выб", "dnf", "dns", "dsq", "+1"]):
        return None

    s_clean = s_clean.replace(",", ".")

    m = re.match(r"^(\d+):(\d{2})[.:](\d{3})$", s_clean)
    if not m:
        return None

    minutes = int(m.group(1))
    seconds = int(m.group(2))
    millis = int(m.group(3))
    total_ms = (minutes * 60 + seconds) * 1000 + millis
    return total_ms


def best_lap_mask(series: pd.Series) -> pd.Series:
    """Возвращает булеву маску строк с лучшим кругом."""
    vals = series.astype(str)
    ms_values = vals.apply(lap_to_ms)

    if ms_values.dropna().empty:
        return pd.Series([False] * len(series), index=series.index)

    min_ms = ms_values.dropna().min()
    return ms_values == min_ms


# ============================================================
#  Построение словаря пилот → команда из таблицы teams
# ============================================================

def build_pilot_team_map(teams: pd.DataFrame) -> dict:
    """
    В teams обычно формат:
    'Команда' | 'Пилот 1' | 'Пилот 2' | 'Пилот 3' | ...
    Собираем mapping: pilot_name -> team_name
    """
    teams = normalize_cols(teams)
    team_col = find_column(teams, ["команда", "team"])
    if not team_col:
        return {}

    pilot_cols = [
        col for col in teams.columns
        if any(k in str(col).lower() for k in ["пилот", "driver"])
    ]

    mapping = {}
    for _, row in teams.iterrows():
        team_name = normalize_str(row[team_col])
        for col in pilot_cols:
            name = row[col]
            if isinstance(name, str) and name.strip():
                key = normalize_str(name)
                mapping[key] = team_name

    return mapping


# ============================================================
#  Основной рендер сезона 2024
# ============================================================

def render_season_2024(
    qualifying: pd.DataFrame,
    race_drivers: pd.DataFrame,
    race_teams: pd.DataFrame,
    wdc: pd.DataFrame,
    wcc: pd.DataFrame,
    teams: pd.DataFrame,
    race_name: str,
):

    st.title("Сезон Формулы-1 2024")

    tab_gp, tab_wdc, tab_wcc, tab_teams = st.tabs(
        ["Гран-при", "WDC", "WCC", "Команды"]
    )

    # --------------------------------------------------------
    #  Вкладка: Гран-при
    # --------------------------------------------------------
    with tab_gp:
        st.subheader(f"Гран-при {race_name}")

        # Квалификация
        st.subheader("Квалификация")
        st.write(colorize_table(qualifying))

        # Гонка — пилоты
        st.subheader("Гонка — пилоты")

        df_rd = race_drivers.copy()
        df_rd = normalize_cols(df_rd)

        lap_col = find_column(df_rd, ["лучший", "best", "lap", "круг"])

        if lap_col:
            mask = best_lap_mask(df_rd[lap_col])

            # базовый командный колорит
            styled = colorize_table(df_rd)

            # подсвечиваем ЛИШЬ ячейку лучшего круга
            def highlight_best(col):
                if col.name != lap_col:
                    return [""] * len(col)
                return [
                    "background-color: #8847BD; color: white; font-weight: bold"
                    if mask.iloc[i] else ""
                    for i in range(len(col))
                ]

            styled = styled.apply(highlight_best, axis=0)
            st.write(styled)
        else:
            st.write(colorize_table(df_rd))

        # Гонка — команды
        st.subheader("Гонка — команды")
        st.write(colorize_table(race_teams))

    # --------------------------------------------------------
    #  Вкладка: WDC
    # --------------------------------------------------------
    with tab_wdc:
        st.subheader("Пилоты — WDC 2024")

        wdc_df = wdc.copy()
        wdc_df = normalize_cols(wdc_df)

        # Столбец с именем пилота в WDC
        pilot_col = find_column(wdc_df, ["пилот", "гонки", "driver"])
        # Строим глобальный словарь pilot -> team
        pilot_team_map = build_pilot_team_map(teams)

        if pilot_col and pilot_team_map:
            def map_team(name):
                key = normalize_str(name)
                return pilot_team_map.get(key, None)

            wdc_df["Команда"] = wdc_df[pilot_col].astype(str).apply(map_team)

        st.write(colorize_table(wdc_df))

    # --------------------------------------------------------
    #  Вкладка: WCC
    # --------------------------------------------------------
    with tab_wcc:
        st.subheader("Команды — WCC 2024")
        st.write(colorize_table(wcc))

    # --------------------------------------------------------
    #  Вкладка: составы команд
    # --------------------------------------------------------
    with tab_teams:
        st.subheader("Составы команд")
        st.write(colorize_table(teams))
