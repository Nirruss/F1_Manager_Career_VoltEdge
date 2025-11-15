import streamlit as st
import pandas as pd
from .utils import colorize, normalize_df, parse_lap

def render_season(season_name, race_name, data):
    st.title(f"Сезон Формулы-1 {season_name}")
    gp_code = None

    # найдём код по имени
    for code, name in data["gp_code_to_name"].items():
        if name == race_name:
            gp_code = code
            break

    tab_gp, tab_wdc, tab_wcc, tab_teams = st.tabs(
        ["Гран-при", "WDC", "WCC", "Команды"]
    )

    # ========== ГРАН-ПРИ ==========

    with tab_gp:
        st.subheader(f"{race_name} — {season_name}")

        race_df = data["races"].get(gp_code)

        if race_df is None:
            st.warning("Данные не найдены")
            return

        race_df = normalize_df(race_df)

        # разделяем по секциям
        if "Лучший круг" in race_df.columns:
            # гонка пилоты
            df = race_df.copy()
            laps = df["Лучший круг"].apply(parse_lap)
            valid = laps.dropna()

            if not valid.empty:
                best = valid.min()
                mask = laps == best

                def hl(col):
                    if col.name != "Лучший круг":
                        return [""] * len(col)
                    return [
                        "background-color:#8847BD;color:white;font-weight:bold"
                        if mask.iloc[i] else ""
                        for i in range(len(col))
                    ]

                st.subheader("Гонка — пилоты")
                st.write(df.style.apply(hl, axis=0))
        else:
            st.subheader("Гонка — пилоты")
            st.write(race_df)

        # гонка — команды (если есть)
        st.subheader("Гонка — команды")
        st.write(colorize(race_df))

    # ========== WDC ==========
    with tab_wdc:
        st.subheader(f"WDC {season_name}")
        st.write(colorize(data["wdc"]))

    # ========== WCC ==========
    with tab_wcc:
        st.subheader(f"WCC {season_name}")
        st.write(colorize(data["wcc"]))

    # ========== TEAMS ==========
    with tab_teams:
        st.subheader(f"Составы {season_name}")
        st.write(colorize(data["teams"]))
