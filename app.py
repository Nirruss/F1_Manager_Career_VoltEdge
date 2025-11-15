import streamlit as st
import pandas as pd

from seasons.renderer import render_season
from seasons.utils import load_season_data

# ---------------------------------------------
# Конфигурация страницы
# ---------------------------------------------
st.set_page_config(page_title="F1 Manager Dashboard", layout="wide")

# ---------------------------------------------
# Выбор сезона
# ---------------------------------------------
st.sidebar.title("Выбор сезона")
season_choice = st.sidebar.selectbox("Сезон", ["2024", "2025"])

excel_files = {
    "2024": "F1_Manager_2024.xlsx",
    "2025": "F1_Manager_2025.xlsx"
}

xls_path = excel_files[season_choice]

# Загружаем сезон
season_data = load_season_data(xls_path)

# ---------------------------------------------
# Выбор Гран-при
# ---------------------------------------------
gp_list = season_data.get("gp_list", {})

if not gp_list:
    st.error("Не удалось загрузить список Гран-при. Проверь файл Excel.")
    st.stop()

# список названий ГП
race_name = st.sidebar.selectbox("Выбор Гран-при", list(gp_list.values()))

# код ГП по названию
race_code = next(code for code, name in gp_list.items() if name == race_name)

# ---------------------------------------------
# РЕНДЕР ПОДСТРАНИЦ
# ---------------------------------------------
render_season(
    season_name=season_choice,
    race_code=race_code,
    data=season_data
)
