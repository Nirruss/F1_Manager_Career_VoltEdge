import streamlit as st

from seasons.loader import load_season
from seasons.renderer import render_season

st.set_page_config(page_title="F1 Manager Dashboard", layout="wide")

st.title("🏎️ F1 Manager Career Dashboard")

# список доступных сезонов
AVAILABLE_SEASONS = ["2024", "2025"]

season = st.sidebar.selectbox("Выбери сезон", AVAILABLE_SEASONS)

data = load_season(season)

if "error" in data:
    st.error(data["error"])
    st.stop()

# список ГП по выбранному сезону
gp_list = data["gp_list"]
gp_names = gp_list["Название"].tolist()

selected_gp = st.sidebar.selectbox("Выбери Гран-при", gp_names)

# код листов для выбранного ГП
gp_code = gp_list.loc[gp_list["Название"] == selected_gp, "Код"].iloc[0]

# Загрузить конкретную гонку
race_data = data["load_gp"](gp_code)

# Рендерим
render_season(
    season_name=season,
    gp_name=selected_gp,
    qualifying=race_data["qualifying"],
    race_drivers=race_data["race_drivers"],
    race_teams=race_data["race_teams"],
    wdc=data["wdc"],
    wcc=data["wcc"],
    teams=data["teams"]
)
