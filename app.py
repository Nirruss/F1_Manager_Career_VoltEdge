import streamlit as st
from seasons.loader import load_season
from seasons.renderer import render_season

st.set_page_config(layout="wide")

# =========================
#  ЗАГРУЗКА СЕЗОНОВ
# =========================
SEASONS = {
    "2024": "F1_Manager_2024.xlsx",
    "2025": "F1_Manager_2025.xlsx",
}

st.sidebar.title("Выбор сезона")
season_choice = st.sidebar.selectbox("Выбери сезон", list(SEASONS.keys()))

season_data = load_season(SEASONS[season_choice])

st.sidebar.title("Выбор Гран-при")
gp_choice = st.sidebar.selectbox("Выбери Гран-при", season_data["gp_names"])

# РЕНДЕР
render_season(
    season_name=season_choice,
    race_name=gp_choice,
    data=season_data,
)
