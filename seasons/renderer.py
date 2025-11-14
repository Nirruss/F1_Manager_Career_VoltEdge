import streamlit as st
import pandas as pd
import numpy as np
import re


# ---------- Палитра команд ----------
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


def normalize_str(x):
    if not isinstance(x, str):
        return x
    return (
        x.replace("\xa0", " ")
         .replace("\u200b", "")
         .replace("\ufeff", "")
         .strip()
    )


def normalize_cols(df):
    df = df.copy()
    df.columns = [normalize_str(c) for c in df.columns]
    return df


def find_column(df, keywords):
    for col in df.columns:
        if any(k in str(col).lower() for k in keywords):
            return col
    return None


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


def colorize_table(df):
    if df is None or df.empty:
        return df
    df = normalize_cols(df)
    df = df.copy()

    team_col = find_column(df, ["команда", "team"])
    if team_col:
        raw = df[team_col].astype(str).apply(normalize_str)
        df["__team__"] = raw.map(TEAM_MAP).fillna(raw)
        df["__color__"] = df["__team__"].map(TEAM_COLORS).fillna("#FFFFFF")
    else:
        df["__color__"] = "#FFFFFF"

    df = df.reset_index(drop=True)
    colors = df["__color__"]

    view = df.drop(columns=["__color__", "__team__"], errors="ignore")

    def style_row(row):
        bg = colors.iloc[row.name]
        fg = get_text_color(bg)
        return [f"background-color:{bg};color:{fg}" for _ in row]

    return (
        view.style
        .apply(style_row, axis=1)
        .hide(axis="index")
    )


def lap_to_ms(s):
    if not isinstance(s, str):
        return None
    s = normalize_str(s).lower()
    if any(x in s for x in ["dnf", "dsq", "выб", "круг", "+1"]):
        return None
    s = s.replace(",", ".")
    m = re.match(r"(\d+):(\d{2})[.:](\d{3})$", s)
    if not m:
        return None
    minutes, seconds, ms = map(int, m.groups())
    return (minutes * 60 + seconds) * 1000 + ms


def best_lap_mask(series):
    ms_values = series.astype(str).apply(lap_to_ms)
    valid = ms_values.dropna()
    if valid.empty:
        return pd.Series([False]*len(series), index=series.index)
    best = valid.min()
    return ms_values == best


def build_pilot_team_map(teams):
    teams = normalize_cols(teams)
    team_col = find_column(teams, ["команда", "team"])
    if not team_col:
        return {}
    pilot_cols = [c for c in teams.columns if "пилот" in c.lower()]
    mapping = {}
    for _, row in teams.iterrows():
        team = normalize_str(row[team_col])
        for col in pilot_cols:
            p = row[col]
            if isinstance(p, str) and p.strip():
                mapping[normalize_str(p)] = team
    return mapping


def render_season(season_name, gp_name,
                  qualifying, race_drivers, race_teams,
                  wdc, wcc, teams):

    st.header(f"{gp_name} — сезон {season_name}")

    tab1, tab2, tab3, tab4 = st.tabs([
        "Гран-при", "WDC", "WCC", "Команды"
    ])

    with tab1:
        st.subheader("Квалификация")
        st.write(colorize_table(qualifying))

        st.subheader("Гонка — пилоты")
        df = normalize_cols(race_drivers.copy())
        lap_col = find_column(df, ["лучший", "best", "lap"])
        if lap_col:
            mask = best_lap_mask(df[lap_col])
            styled = colorize_table(df)

            def highlight(col):
                if col.name != lap_col:
                    return [""] * len(col)
                return [
                    "background-color:#8847BD;color:white;font-weight:bold" if mask.iloc[i] else ""
                    for i in range(len(col))
                ]

            styled = styled.apply(highlight, axis=0)
            st.write(styled)
        else:
            st.write(colorize_table(df))

        st.subheader("Гонка — команды")
        st.write(colorize_table(race_teams))

    with tab2:
        st.subheader("WDC")
        wdc = normalize_cols(wdc.copy())
        pilot_col = find_column(wdc, ["пилот"])
        mapper = build_pilot_team_map(teams)
        if pilot_col:
            wdc["Команда"] = wdc[pilot_col].astype(str).apply(lambda x: mapper.get(normalize_str(x)))
        st.write(colorize_table(wdc))

    with tab3:
        st.subheader("WCC")
        st.write(colorize_table(wcc))

    with tab4:
        st.subheader("Составы команд")
        st.write(colorize_table(teams))
