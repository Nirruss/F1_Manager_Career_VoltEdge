import streamlit as st
import pandas as pd

from seasons.renderer import render_season
from seasons.utils import load_season_data

st.set_page_config(page_title="F1 Manager Dashboard", layout="wide")

# -------------------------
# Выбор сезона
# -------------------------
st.sidebar.title("Выбор сезона")
season_choice = st.sidebar.selectbox("Сезон", ["2024", "2025"])

excel_files = {
    "2024": "F1_Manager_2024.xlsx",
    "2025": "F1_Manager_2025.xlsx",
}

xls_path = excel_files[season_choice]

# Загружаем данные сезона
season_data = load_season_data(xls_path)
st.write("SEASON DATA KEYS:", season_data.keys())   # ОТЛАДКА

# gp_map = {"BAH": "Бахрейн", ...}
gp_map = season_data["gp_map"]

# -------------------------
# Выбор Гран-при
# -------------------------
race_name = st.sidebar.selectbox(
    "Выбор Гран-при",
    list(gp_map.values())
)

# Ищем КОД гонки по имени
race_code = next(code for code, name in gp_map.items() if name == race_name)

# -------------------------
# РЕНДЕРИНГ СТРАНИЦЫ
# -------------------------
render_season(
    season_name=season_choice,
    race_code=race_code,
    data=season_data
)
