import streamlit as st
import pandas as pd

from season_2024 import render_season_2024, colorize_table

st.set_page_config(page_title="F1 Manager Dashboard", layout="wide")

st.title("🏎️ F1 Manager Dashboard — Сезон 2024")

# Загружаем Excel
excel_file = "F1_Manager_2024.xlsx"

try:
    xls = pd.ExcelFile(excel_file)
except:
    st.error("❌ Не найден файл F1_Manager_2024.xlsx. Помести его рядом с app.py.")
    st.stop()

# Рендерим сезон
render_season_2024(xls)

st.markdown("---")
st.caption("© Dashboard обновляется автоматически по данным таблицы.")
