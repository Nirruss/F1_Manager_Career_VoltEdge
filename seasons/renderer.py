import streamlit as st
import pandas as pd

from seasons.utils import (
    colorize_table,
    normalize_cols,
    build_pilot_team_map,
    parse_lap_time,
    find_column,
)


# ======================================================
# НОРМАЛИЗАЦИЯ ТОЛЬКО ЗАГОЛОВКОВ!
# ======================================================
def normalize_df(df: pd.DataFrame):
    if df is None or df.empty:
        return df

    df = df.copy()

    # Заголовки → красиво, но НЕ ломаем регистр данных
    new_cols = []
    for c in df.columns:
        if isinstance(c, str):
            base = normalize_cols(c)
            new_cols.append(base.title())   # "пилот" → "Пилот"
        else:
            new_cols.append(str(c))
    df.columns = new_cols

    # Данные НЕ трогаем регистр
    for col in df.columns:
        df[col] = df[col].apply(
            lambda x: x.strip() if isinstance(x, str) else x
        )

    return df



# ======================================================
# РЕНДЕР СЕЗОНА
# ======================================================
def render_season(season_name, race_code, data):
    st.title(f"{race_code} — сезон {season_name}")

    teams = normalize_df(data["teams"])
    wdc   = normalize_df(data["wdc"])
    wcc   = normalize_df(data["wcc"])

    pilot_to_team = build_pilot_team_map(teams)

    gp_data = data["grand_prix"].get(race_code, {})
    qualifying   = gp_data.get("qualifying")
    race_drivers = gp_data.get("race_drivers")
    race_teams   = gp_data.get("race_teams")

    tab_gp, tab_wdc, tab_wcc, tab_teams = st.tabs(["Гран-при", "WDC", "WCC", "Команды"])

    # ======================================================
    # ГРАН-ПРИ
    # ======================================================
    with tab_gp:
        st.subheader("Квалификация")
        if qualifying is not None:
            st.write(colorize_table(normalize_df(qualifying)))
        else:
            st.warning("Нет данных квалификации")

        # --- Гонка пилоты ---
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

        # --- Гонка команды ---
        st.subheader("Гонка — команды")
        if race_teams is not None:
            st.write(colorize_table(normalize_df(race_teams)))
        else:
            st.warning("Нет данных о командах гонки")


    # ======================================================
    # WDC
    # ======================================================
    with tab_wdc:
        st.subheader(f"WDC {season_name}")

        wdc = wdc.copy()

        # Чистим числа
        for col in wdc.columns:
            if col in ["Пилот", "Команда"]:
                continue

            def try_cast(v):
                if pd.isna(v): return pd.NA
                if isinstance(v, str) and v.upper() == "DNF": return v
                try: return int(float(v))
                except: return v

            wdc[col] = wdc[col].apply(try_cast)

        pilot_col = find_column(wdc, ["пилот", "pilot"])
        if pilot_col:
            wdc["Команда"] = wdc[pilot_col].map(lambda x: pilot_to_team.get(x, ""))

        st.write(colorize_table(wdc))


    # ======================================================
    # WCC
    # ======================================================
    with tab_wcc:
        st.subheader(f"WCC {season_name}")

        wcc = wcc.copy()
        for col in wcc.columns:
            if col == "Команда":
                continue

            def try_cast(v):
                if pd.isna(v): return pd.NA
                if isinstance(v, str) and v.upper() == "DNF": return v
                try: return int(float(v))
                except: return v

            wcc[col] = wcc[col].apply(try_cast)

        st.write(colorize_table(wcc))


    # ======================================================
    # Команды
    # ======================================================
    with tab_teams:
        st.subheader("Составы команд")
        st.write(colorize_table(teams))
