import streamlit as st
import pandas as pd
from seasons_pkg.renderer import render_season
from seasons.utils import load_season_data

st.set_page_config(page_title="F1 Manager Dashboard", layout="wide")

st.sidebar.title("Выбор сезона")
season_choice = st.sidebar.selectbox("Сезон", ["2024", "2025"])

excel_files = {
    "2024": "F1_Manager_2024.xlsx",
    "2025": "F1_Manager_2025.xlsx"
}

xls_path = excel_files[season_choice]

# ❗ передаём ГОД отдельно
season_data = load_season_data(xls_path, season_choice)

# список гонок
gp_list = season_data["gp_list"]
race_choice = st.sidebar.selectbox("Выбор Гран-при", gp_list["Название"])

gp_code = gp_list.set_index("Название").loc[race_choice, "Код"]

render_season(
    season_name=season_choice,
    race_code=gp_code,
    data=season_data
)
