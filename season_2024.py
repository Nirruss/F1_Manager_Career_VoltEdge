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
    "Alpine": "#EE12BA",
    "VoltEdge": "#CCCC00",
}

# =========================
#  Light/dark contrast
# =========================
def is_light_color(hex_color: str) -> bool:
    hex_color = hex_color.lstrip("#")
    r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    luminance = 0.299 * r + 0.587 * g + 0.114 * b
    return luminance > 160

# =========================
#  Team name normalization
# =========================
def normalize_team_name(name: str) -> str:
    if not isinstance(name, str):
        return ""

    n = name.lower().strip()
    n = n.replace("\n", "").replace("\r", "")
    n = n.replace(" ", "").replace("-", "").replace("_", "")

    repl = {
        "а": "a", "в": "b", "е": "e", "к": "k",
        "м": "m", "н": "h", "о": "o", "р": "p",
        "с": "c", "т": "t", "х": "x"
    }
    for r, l in repl.items():
        n = n.replace(r, l)

    detect = {
        "ferrari": "Ferrari",
        "redbull": "Red Bull",
        "mercedes": "Mercedes",
        "amg": "Mercedes",
        "mclaren": "McLaren",
        "astonmartin": "Aston Martin",
        "haas": "Haas",
        "williams": "Williams",
        "kicksauber": "Kick Sauber",
        "sauber": "Kick Sauber",
        "alpine": "Alpine",
        "volt": "VoltEdge",
        "voltedge": "VoltEdge",
        "visa": "RB",
        "cashapp": "RB",
        "rbf1": "RB",
        "rbteam": "RB",
    }

    for key, val in detect.items():
        if key in n:
            return val

    return ""

# =========================
#  Color styling
# =========================
def colorize_table(df: pd.DataFrame):
    team_col = None
    team_names = set(TEAM_COLORS.keys())

    for col in df.columns:
        normalized = df[col].astype(str).map(normalize_team_name)
        if normalized.isin(team_names).any():
            team_col = col
            df[col] = normalized
            break

    styler = df.style

    if team_col is None:
        return styler

    styles = pd.DataFrame("", index=df.index, columns=df.columns)

    for i, team in enumerate(df[team_col]):
        color = TEAM_COLORS.get(team, "#FFFFFF")
        text_color = "#000000" if is_light_color(color) else "#FFFFFF"
        styles.iloc[i] = [
            f"background-color: {color}; color: {text_color};"
        ] * len(df.columns)

    return df.style.apply(lambda _: styles, axis=None)

# =========================
#  Auto-split GP sheet
# =========================
def split_race_sheet(df: pd.DataFrame):
    s = df.astype(str)

    header_rows = []
    for idx in s.index:
        row = list(s.loc[idx, :])
        row = [x for x in row if x != "nan"]
        if not row:
            continue
        if row[0] == "Позиция":
            header_rows.append(idx)

    if len(header_rows) < 3:
        return None, None, None

    h_qual = header_rows[0]
    h_race_p = header_rows[1]
    h_race_t = header_rows[2]

    def read_block(start, end):
        return df.iloc[start + 1:end].dropna(how="all")

    quali = read_block(h_qual, h_race_p)
    race_p = read_block(h_race_p, h_race_t)
    race_t = df.iloc[h_race_t + 1:].dropna(how="all")

    return quali, race_p, race_t

# =========================
#  Render season 2024
# =========================
def render_season_2024(xls):
    st.header("📅 Сезон 2024")

    try:
        wdc = pd.read_excel(xls, "WDC_2024")
        wcc = pd.read_excel(xls, "WCC_2024")
        teams = pd.read_excel(xls, "Teams_2024")

        gp_df = pd.read_excel(xls, "GP_List_2024")
        gp_list = gp_df[gp_df.columns[0]].dropna().tolist()

        # === ПРАВИЛЬНЫЙ СЛОВАРЬ "Пилот → Команда"
        pilot_to_team = {}
        for _, row in teams.iterrows():
            team = row["Команда"]
            for col in ["Пилот 1", "Пилот 2", "Пилот 3"]:
                pilot = str(row[col]).strip()
                if pilot and pilot.lower() != "nan":
                    pilot_to_team[pilot] = team

    except Exception as e:
        st.error(f"Ошибка загрузки листов: {e}")
        return

    tab_gp, tab_wdc, tab_wcc, tab_teams = st.tabs([
        "🏁 Гонки",
        "👨‍✈️ WDC",
        "🏆 WCC",
        "🛠 Составы",
    ])

    # =========================
    #  ГОНКИ
    # =========================
    with tab_gp:
        st.subheader("Результаты гран-при")
        selected_gp = st.selectbox("Выберите гонку:", gp_list)

        try:
            df = pd.read_excel(xls, selected_gp, header=None)
        except:
            st.error(f"Лист '{selected_gp}' отсутствует")
            return

        quali, race_p, race_t = split_race_sheet(df)
        if quali is None:
            st.error("Не удалось распознать формат гонки.")
            return

        st.markdown("### 🏎️ Квалификация")
        quali = quali[~quali.iloc[:, 0].astype(str).str.contains("Race", na=False)]
        quali = quali.iloc[:, 0:3]
        quali.columns = ["Позиция", "Пилоты", "Команда"]
        st.write(colorize_table(quali))

        st.markdown("### 🏁 Гонка — пилоты")
        race_p = race_p[~race_p.iloc[:, 0].astype(str).str.contains("Race", na=False)]
        race_p = race_p.iloc[:, 0:6]
        race_p.columns = ["Позиция", "Пилоты", "Команда", "Лучший круг", "Отставание", "Очки"]
        st.write(colorize_table(race_p))

        st.markdown("### 🏆 Гонка — команды")
        race_t = race_t[~race_t.iloc[:, 0].astype(str).str.contains("Race", na=False)]
        race_t = race_t.iloc[:, 0:3]
        race_t.columns = ["Позиция", "Команда", "Очки"]
        st.write(colorize_table(race_t))

    # =========================
    #  WDC (окрашено через команду пилота)
    # =========================
    with tab_wdc:
        st.subheader("Пилоты — WDC 2024")

        possible_cols = ["Пилот", "Пилоты", "Пилоты\\Гонки", "Driver", "Name", "Pilot"]

        pilot_col = None
        for c in possible_cols:
            if c in wdc.columns:
                pilot_col = c
                break

        if pilot_col is None:
            st.error("Не найдена колонка с именами пилотов в WDC_2024.")
            return

        wdc_local = wdc.copy()
        wdc_local["Команда"] = wdc_local[pilot_col].map(pilot_to_team)

        st.write(colorize_table(wdc_local))

    # =========================
    #  WCC
    # =========================
    with tab_wcc:
        st.subheader("Команды — WCC 2024")
        st.write(colorize_table(wcc))

    # =========================
    #  TEAMS
    # =========================
    with tab_teams:
        st.subheader("Составы команд")
        st.write(colorize_table(teams))
