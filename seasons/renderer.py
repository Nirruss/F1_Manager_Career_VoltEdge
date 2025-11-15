import streamlit as st
import pandas as pd
from .utils import colorize, normalize_df, parse_lap

def render_season(season_name, race_name, data):
    st.title(f"Сезон Формулы-1 {season_name}")

    # ----------------------------
    #  НАХОДИМ КОД ГРАН-ПРИ
    # ----------------------------
    gp_code = None
    for code, name in data["gp_code_to_name"].items():
        if name == race_name:
            gp_code = code
            break

    tab_gp, tab_wdc, tab_wcc, tab_teams = st.tabs(
        ["Гран-при", "WDC", "WCC", "Команды"]
    )

    # ===================================================
    #                 Г Р А Н - П Р И
    # ===================================================
    with tab_gp:
        st.subheader(f"{race_name} — {season_name}")

        race_df = data["races"].get(gp_code)
        if race_df is None:
            st.warning("Нет данных по этой гонке")
            return

        race_df = normalize_df(race_df)

        # ----------------------------
        #  Блок квалификации
        # ----------------------------
        if "Пилоты" in race_df.columns and "Команда" in race_df.columns and "Лучший круг" not in race_df.columns:
            st.subheader("Квалификация")
            st.write(colorize(race_df))

        # ----------------------------
        #  Блок гонки — Пилоты
        # ----------------------------
        if "Лучший круг" in race_df.columns:
            st.subheader("Гонка — пилоты")

            laps = race_df["Лучший круг"].apply(parse_lap)
            valid = laps.dropna()

            if not valid.empty:
                best = valid.min()
                mask = laps == best

                def highlight_fastest(col):
                    if col.name != "Лучший круг":
                        return [""] * len(col)
                    return [
                        "background-color:#8847BD;color:white;font-weight:bold"
                        if mask.iloc[i] else ""
                        for i in range(len(col))
                    ]

                st.write(race_df.style.apply(highlight_fastest, axis=0))
            else:
                st.write(race_df)

        # ----------------------------
        #  Блок гонки — Команды
        # ----------------------------
        if "Очки" in race_df.columns and "Команда" in race_df.columns:
            st.subheader("Гонка — команды")
            st.write(colorize(race_df))

    # ===================================================
    #                      W D C
    # ===================================================
    with tab_wdc:
        st.subheader(f"WDC {season_name}")

        wdc = normalize_df(data["wdc"]).copy()

        # Правка: очки делаем Int64
        num_cols = wdc.select_dtypes(include=["float"]).columns
        wdc[num_cols] = wdc[num_cols].astype("Int64")

        # красим по командам пилотов из Teams
        teams = normalize_df(data["teams"])
        pilot_to_team = dict(zip(teams["Пилоты"], teams["Команда"]))
        wdc["Команда"] = wdc["Пилоты\\Гонки"].map(pilot_to_team)

        st.write(colorize(wdc.drop(columns=["Команда"])))


    # ===================================================
    #                      W C C
    # ===================================================
    with tab_wcc:
        st.subheader(f"WCC {season_name}")
        st.write(colorize(data["wcc"]))


    # ===================================================
    #                  С О С Т А В Ы
    # ===================================================
    with tab_teams:
        st.subheader("Составы команд")
        st.write(colorize(data["teams"]))
