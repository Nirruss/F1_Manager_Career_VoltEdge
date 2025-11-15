import streamlit as st
import pandas as pd

from seasons.utils import (
    colorize_table,
    normalize_cols,
    build_pilot_team_map,
    parse_lap_time,
)

# универсальный нормализатор DataFrame
def normalize_df(df: pd.DataFrame):
    if df is None or df.empty:
        return df
    df = df.copy()
    df.columns = [normalize_cols(c) for c in df.columns]
    df = df.applymap(lambda x: normalize_cols(x) if isinstance(x, str) else x)
    return df


def render_season(season_name, race_code, data):
    st.title(f"{race_code} — сезон {season_name}")

    teams = normalize_df(data["teams"])
    wdc = normalize_df(data["wdc"])
    wcc = normalize_df(data["wcc"])

    pilot_to_team = build_pilot_team_map(teams)

    gp_df = data["grand_prix"][race_code]["qualifying"]
    qualifying, race_drivers, race_teams = split_gp_blocks(gp_df)

    tab_gp, tab_wdc, tab_wcc, tab_teams = st.tabs(["Гран-при", "WDC", "WCC", "Команды"])

    # ----------------- Гран-при -----------------
    with tab_gp:
        st.subheader("Квалификация")
        st.write(colorize(qualifying))

        st.subheader("Гонка — пилоты")

        race_drivers = normalize_df(race_drivers)

        lap_col = find_column(race_drivers, ["лучший", "best", "lap"])
        if lap_col:
            laps = race_drivers[lap_col].apply(parse_lap)
            valid = laps.dropna()

            if not valid.empty:
                best = valid.min()

                def style_fastest(col):
                    if col.name != lap_col:
                        return [""] * len(col)
                    return [
                        "background-color:#8847BD; color:white; font-weight:bold"
                        if parse_lap(x) == best else ""
                        for x in col
                    ]

                st.write(race_drivers.style.apply(style_fastest, axis=0))
            else:
                st.write(race_drivers)
        else:
            st.write(race_drivers)

        st.subheader("Гонка — команды")
        st.write(colorize(race_teams))

    # ----------------- WDC -----------------
    with tab_wdc:
        st.subheader(f"WDC {season_name}")

        wdc = wdc.copy()
        num_cols = wdc.select_dtypes(include=["float"]).columns
        wdc[num_cols] = wdc[num_cols].astype("Int64")

        pilot_col = find_column(wdc, ["пилот", "driver"])
        team_col = "Команда"

        wdc[team_col] = wdc[pilot_col].map(pilot_to_team)

        st.write(colorize(wdc.drop(columns=[team_col])))

    # ----------------- WCC -----------------
    with tab_wcc:
        st.subheader(f"WCC {season_name}")
        st.write(colorize(wcc))

    # ----------------- Команды -----------------
    with tab_teams:
        st.subheader("Составы команд")
        st.write(colorize(teams))
