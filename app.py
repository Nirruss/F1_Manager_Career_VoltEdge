import streamlit as st
import pandas as pd

from season_2024 import render_season_2024

st.set_page_config(page_title="F1 Manager Dashboard", layout="wide")

st.title("🏎️ F1 Manager Dashboard — Сезон 2024")

# =========================
#  Загрузка Excel
# =========================
excel_file = "F1_Manager_2024.xlsx"

try:
    xls = pd.ExcelFile(excel_file)
except Exception:
    st.error("❌ Не найден файл F1_Manager_2024.xlsx. Помести его рядом с app.py.")
    st.stop()

# =========================
#  Список этапов (листы, кроме служебных)
# =========================
exclude = {"Teams_2024", "WDC_2024", "WCC_2024", "GP_List_2024"}
gp_list = [s for s in xls.sheet_names if s not in exclude]

selected_gp = st.selectbox("Выбери этап:", gp_list)

# Загружаем выбранный лист как «сырой» DataFrame без шапки
df = pd.read_excel(excel_file, sheet_name=selected_gp, header=None)


# =========================
#  Вспомогательная функция: достать таблицу по маркеру
#  (Qualification / Race_Pilots / Race_Teams)
# =========================
def extract_table(df_raw: pd.DataFrame, marker: str) -> pd.DataFrame:
    # Находим строку, где стоит маркер (например, "Qualification")
    start_marker = df_raw[df_raw.eq(marker).any(axis=1)].index[0]

    # Через одну строку после маркера — заголовки
    header_row = start_marker + 1
    header = df_raw.iloc[header_row].tolist()

    # Данные начинаются ещё через одну строку
    data_start = header_row + 1
    data_end = data_start

    # Ищем конец таблицы: первая полностью пустая строка
    while data_end < len(df_raw) and not df_raw.iloc[data_end].isna().all():
        data_end += 1

    # Формируем итоговую таблицу
    data = df_raw.iloc[data_start:data_end].copy()
    data.columns = header
    data = data.dropna(how="all")

    return data


# =========================
#  Извлечение трёх таблиц по гонке
# =========================
qualifying = extract_table(df, "Qualification")
race_drivers = extract_table(df, "Race_Pilots")
race_teams = extract_table(df, "Race_Teams")

# =========================
#  Общие таблицы сезона
# =========================
wdc = pd.read_excel(excel_file, sheet_name="WDC_2024")
wcc = pd.read_excel(excel_file, sheet_name="WCC_2024")
teams = pd.read_excel(excel_file, sheet_name="Teams_2024")

# =========================
#  Рендер страницы сезона
# =========================
render_season_2024(
    qualifying,
    race_drivers,
    race_teams,
    wdc,
    wcc,
    teams,
    selected_gp,
)

st.markdown("---")
st.caption("© Dashboard обновляется автоматически по данным таблицы.")
