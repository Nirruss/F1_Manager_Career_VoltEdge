import streamlit as st
import pandas as pd

from seasons.utils import (
    colorize_table,
    normalize_match,
    build_pilot_team_map,
    parse_lap_time,
    find_column,
)

def normalize_df(df):
    df = df.copy()

    new_cols = []
    for c in df.columns:
        c = str(c).strip()
        c = c.replace("\\", "/")      # заменяем проблемный обратный слэш
        c = c.replace("  ", " ")      # двойные пробелы
        c = c.replace("\n", " ")
        c = c.replace("\r", " ")
        c = c.replace("\xa0", " ")
        c = c.strip()
        new_cols.append(c)

    df.columns = new_cols
    return df


def render_season(season_name, race_code, data):

    st.title(f"{race_code} — сезон {season_name}")

    teams = normalize_df(data["teams"])
    wdc   = normalize_df(data["wdc"])
    wcc   = normalize_df(data["wcc"])

    pilot_to_team = build_pilot_team_map(teams)

    gp = data["grand_prix"].get(race_code, {})

    qualifying   = gp.get("qualifying")
    race_drivers = gp.get("race_drivers")
    race_teams   = gp.get("race_teams")

    tab_gp, tab_wdc, tab_wcc, tab_team = st.tabs(["Гран-при","WDC","WCC","Команды"])

    # ==== ГРАН-ПРИ ====
    with tab_gp:
        st.subheader("Квалификация")
        if qualifying is not None:
            st.write(colorize_table(normalize_df(qualifying)))
        else:
            st.warning("Нет данных")

        st.subheader("Гонка — пилоты")
        if race_drivers is not None:
            race = normalize_df(race_drivers)
            lapcol = find_column(race, ["лучший","best","lap"])

            if lapcol:
                parsed = race[lapcol].apply(parse_lap_time)
                best = parsed.dropna().min()

                def sty(col):
                    if col.name != lapcol:
                        return [""]*len(col)
                    return [
                        "background-color:#8847BD; color:white; font-weight:bold"
                        if parse_lap_time(x)==best else ""
                        for x in col
                    ]

                st.write(race.style.apply(sty, axis=0))
            else:
                st.write(race)

        st.subheader("Гонка — команды")
        if race_teams is not None:
            st.write(colorize_table(normalize_df(race_teams)))

    # ==== WDC ====
    with tab_wdc:
        st.subheader(f"WDC {season_name}")

        w = wdc.copy()

        pilot_col = find_column(w,["пилот","driver"])
        if pilot_col:
            w["Команда"] = w[pilot_col].map(
                lambda x: pilot_to_team.get(str(x), "")
            )

        st.write(colorize_table(w))

    # ==== WCC ====
    with tab_wcc:
        st.subheader(f"WCC {season_name}")
        st.write(colorize_table(wcc))

    # ==== Teams ====
    with tab_team:
        st.subheader("Составы команд")
        st.write(colorize_table(teams))
