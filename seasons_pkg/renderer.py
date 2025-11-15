import streamlit as st
import pandas as pd

from seasons_pkg.utils import (
    load_season_data,
    colorize_table,
    parse_lap_time,
    normalize_cols
)



def split_gp_blocks(df):
    df = df.dropna(how="all")
    headers = df.iloc[0].tolist()

    block_indices = [i for i, x in enumerate(headers) if isinstance(x, str) and x.strip() != ""]

    if len(block_indices) < 3:
        return None, None, None

    q_start = block_indices[0]
    r1_start = block_indices[1]
    r2_start = block_indices[2]

    qualifying = df.iloc[:, q_start:r1_start]
    race_drivers = df.iloc[:, r1_start:r2_start]
    race_teams = df.iloc[:, r2_start:]

    qualifying = qualifying.drop(0).reset_index(drop=True)
    race_drivers = race_drivers.drop(0).reset_index(drop=True)
    race_teams = race_teams.drop(0).reset_index(drop=True)

    return qualifying, race_drivers, race_teams


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
