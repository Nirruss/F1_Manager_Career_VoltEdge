import streamlit as st
import pandas as pd

from season_2024 import render_season_2024

st.set_page_config(page_title="F1 Manager Dashboard", layout="wide")

st.title("🏎️ F1 Manager Dashboard — Сезон 2024")

# Загружаем Excel
excel_file = "F1_Manager_2024.xlsx"

try:
    xls = pd.ExcelFile(excel_file)
except:
    st.error("❌ Не найден файл F1_Manager_2024.xlsx. Помести его рядом с app.py.")
    st.stop()

# Получаем список Гран-при (все листы кроме WDC/WCC/Teams/GP_List)
exclude = {"Teams_2024", "WDC_2024", "WCC_2024", "GP_List_2024"}
gp_list = [s for s in xls.sheet_names if s not in exclude]

selected_gp = st.selectbox("Выбери этап:", gp_list)

# Загружаем выбранный лист
df = pd.read_excel(excel_file, sheet_name=selected_gp, header=None)

# =========================
# Функция поиска блока таблицы по её заголовку
# =========================
def extract_table(df, marker):
    start = df[df.eq(marker).any(axis=1)].index[0] + 1
    header = df.iloc[start].tolist()
    end = start + 1

    # ищем конец таблицы (пока не пустая строка)
    while end < len(df) and not df.iloc[end].isna().all():
        end += 1

    data = df.iloc[start + 1 : end]
    data.columns = header
    data = data.dropna(how="all")
    return data


# Извлекаем 3 таблицы
qualifying = extract_table(df, "Qualification")
race_drivers = extract_table(df, "Race_Pilots")
race_teams = extract_table(df, "Race_Teams")

# Загружаем WDC / WCC / команды
wdc = pd.read_excel(excel_file, sheet_name="WDC_2024")
wcc = pd.read_excel(excel_file, sheet_name="WCC_2024")
teams = pd.read_excel(excel_file, sheet_name="Teams_2024")

# Рендерим сезон
render_season_2024(
    qualifying,
    race_drivers,
    race_teams,
    wdc,
    wcc,
    teams,
    selected_gp
)

st.markdown("---")
st.caption("© Dashboard обновляется автоматически по данным таблицы.")
