import streamlit as st
import pandas as pd

from seasons.utils import (
    colorize_table,
    normalize_cols,
    build_pilot_team_map,
    parse_lap_time,
    find_column,
)

# =====================================================
#        НОРМАЛИЗАЦИЯ ДАННЫХ + ЧИСТКА ОЧКОВ
# =====================================================
def normalize_df(df: pd.DataFrame):
    if df is None or df.empty:
        return df
    df = df.copy()
    # Заглавные колонки
    df.columns = [normalize_cols(c).title() for c in df.columns]

    # Чистим строки
    df = df.applymap(lambda x: normalize_cols(x) if isinstance(x, str) else x)
    return df


def clean_points_table(df: pd.DataFrame):
    """Превращает '', 'DNF', 'dnf' → NA, а числа → int."""
    if df is None or df.empty:
        return df

    df = df.copy()

    for col in df.columns:
        if df[col].dtype == object:
            df[col] = (
                df[col]
                .astype(str)
                .str.strip()
                .replace({"": pd.NA, "dnf": pd.NA, "DNF": pd.NA})
            )

            # пробуем сделать числами, но не ломаем строки
            df[col] = pd.to_numeric(df[col], errors="ignore")

    return df


# =====================================================
#                 ГЛАВНЫЙ РЕНДЕРЕР
# =====================================================
def render_season(season_name, race_code, data):
    st.title(f"{race_code} — сезон {season_name}")

    # --- БАЗОВЫЕ ТАБЛИЦЫ ---
    teams = normalize_df(data["teams"])
    wdc   = clean_points_table(normalize_df(data["wdc"]))
    wcc   = clean_points_table(normalize_df(data["wcc"]))

    # карта пилот → команда
    pilot_to_team = build_pilot_team_map(teams)

    # --- ГРАН-ПРИ ---
    gp_data = data["grand_prix"].get(race_code, {})
    qualifying   = gp_data.get("qualifying")
    race_drivers = gp_data.get("race_drivers")
    race_teams   = gp_data.get("race_teams")

    tab_gp, tab_wdc, tab_wcc, tab_teams = st.tabs(
        ["Гран-при", "WDC", "WCC", "Команды"]
    )

    # =====================================================
    #                        ГРАН-ПРИ
    # =====================================================
    with tab_gp:
        st.subheader("Квалификация")
        st.write(colorize_table(normalize_df(qualifying))
                 if qualifying is not None else st.warning("Нет данных"))

        # -------- ГОНКА — ПИЛОТЫ --------
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
            st.warning("Нет данных")

        # -------- ГОНКА — КОМАНДЫ --------
        st.subheader("Гонка — команды")
        st.write(colorize_table(normalize_df(race_teams))
                 if race_teams is not None else st.warning("Нет данных"))

    # =====================================================
    #                        WDC
    # =====================================================
    with tab_wdc:
        st.subheader(f"WDC {season_name}")

        wdc = wdc.copy()

        # приводим числа
        num_cols = wdc.select_dtypes(include=["float", "int", "Int64"]).columns
        wdc[num_cols] = wdc[num_cols].astype("Int64")

        # добавляем команду для колорита
        pilot_col = find_column(wdc, ["пилот", "driver"])
        if pilot_col:
            wdc["Команда"] = wdc[pilot_col].map(pilot_to_team)

        st.write(colorize_table(wdc))

    # =====================================================
    #                        WCC
    # =====================================================
    with tab_wcc:
        st.subheader(f"WCC {season_name}")

        wcc = wcc.copy()
        num_cols = wcc.select_dtypes(include=["float", "int", "Int64"]).columns
        wcc[num_cols] = wcc[num_cols].astype("Int64")

        st.write(colorize_table(wcc))

    # =====================================================
    #                        КОМАНДЫ
    # =====================================================
    with tab_teams:
        st.subheader("Составы команд")
        st.write(colorize_table(teams))
