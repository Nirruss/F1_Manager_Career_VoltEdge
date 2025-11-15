import streamlit as st
import pandas as pd

from seasons.utils import (
    colorize_table,
    normalize_cols,
    build_pilot_team_map,
    parse_lap_time,
    find_column,
)

# ===== НОРМАЛИЗАЦИЯ DF =====
def normalize_df(df: pd.DataFrame):
    if df is None or df.empty:
        return df
    df = df.copy()
    df.columns = [normalize_cols(c).title() for c in df.columns]  # 🔥 заглавные!!!
    df = df.applymap(lambda x: normalize_cols(x) if isinstance(x, str) else x)
    return df


def render_season(season_name, race_code, data):
    st.title(f"{race_code} — сезон {season_name}")

    # --- БАЗОВЫЕ ТАБЛИЦЫ ---
    teams = normalize_df(data["teams"])
    wdc   = normalize_df(data["wdc"])
    wcc   = normalize_df(data["wcc"])

    # карта пилот → команда
    pilot_to_team = build_pilot_team_map(teams)

    # --- ГРАН-ПРИ ---
    gp_data = data["grand_prix"].get(race_code, {})
    qualifying   = gp_data.get("qualifying")
    race_drivers = gp_data.get("race_drivers")
    race_teams   = gp_data.get("race_teams")

    # вкладки
    tab_gp, tab_wdc, tab_wcc, tab_teams = st.tabs(
        ["Гран-при", "WDC", "WCC", "Команды"]
    )

    # ===================================================================
    #                        ГРАН-ПРИ
    # ===================================================================
    with tab_gp:
        st.subheader("Квалификация")
        if qualifying is not None:
            st.write(colorize_table(normalize_df(qualifying)))
        else:
            st.warning("Нет данных квалификации")

        # ===== Гонка — пилоты =====
        st.subheader("Гонка — пилоты")

        if race_drivers is not None:
            race_drivers = normalize_df(race_drivers)

            lap_col = find_column(race_drivers, ["лучший", "best", "lap"])

            if lap_col:
                parsed = race_drivers[lap_col].apply(parse_lap_time)
                valid = parsed.dropna()

                if not valid.empty:
                    best = valid.min()

                    def style_fastest(col):
                        if col.name != lap_col:
                            return [""] * len(col)
                        return [
                            "background-color:#8847BD; color:white; font-weight:bold"
                            if parse_lap_time(x) == best else ""
                            for x in col
                        ]

                    st.write(race_drivers.style.apply(style_fastest, axis=0))
                else:
                    st.write(race_drivers)
            else:
                st.write(race_drivers)
        else:
            st.warning("Нет данных о пилотах гонки")

        # ===== Гонка — команды =====
        st.subheader("Гонка — команды")

        if race_teams is not None:
            st.write(colorize_table(normalize_df(race_teams)))
        else:
            st.warning("Нет данных о командах гонки")

    # ===================================================================
    #                        WDC
    # ===================================================================
    with tab_wdc:
        st.subheader(f"WDC {season_name}")

        wdc = wdc.copy()

        # приведение float → int
        numeric = wdc.select_dtypes(include=["float", "float64"])
        for col in numeric:
            wdc[col] = wdc[col].astype("Int64")

        pilot_col = find_column(wdc, ["пилот", "driver"])
        if pilot_col:
            wdc["Команда"] = wdc[pilot_col].map(pilot_to_team)

        st.write(colorize_table(wdc))

    # ===================================================================
    #                        WCC
    # ===================================================================
    with tab_wcc:
        st.subheader(f"WCC {season_name}")

        # приведение очков к int
        wcc = wcc.copy()
        numeric = wcc.select_dtypes(include=["float"])
        for col in numeric:
            wcc[col] = wcc[col].astype("Int64")

        st.write(colorize_table(wcc))

    # ===================================================================
    #                        Команды
    # ===================================================================
    with tab_teams:
        st.subheader("Составы команд")
        st.write(colorize_table(teams))
