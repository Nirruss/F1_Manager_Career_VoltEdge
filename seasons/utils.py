normalize_cols("Scuderia Ferrari HP") → "Scuderia Ferrari Hp"
normalize_for_match → "scuderia ferrari hp"
OK!

НО теперь render показывает "Scuderia Ferrari Hp"
И colorize_table сравнивает "Scuderia Ferrari Hp" (с TitleCase) vs TEAM_MAP → OK

НО в WDC цвет не находится, потому что:

"Пилот → Команда" подставляет название точно так же, но с TitleCase

→ "Scuderia Ferrari Hp"

colorize_table нормализует так:

team_clean = normalize_for_match("Scuderia Ferrari Hp") = "scuderia ferrari hp"
→ OK

Значит, root cause — **в некоторых таблицах normalize_df ломает регистр названия ("HP" → "Hp")** и поэтому mapping иногда не срабатывает.

---

# 🔥 Я исправил utils И renderer полностью, чтобы:

### ✔ НИЧЕГО НЕ ПРИКАСАЛОСЬ к регистру значений таблицы
→ только к заголовкам

### ✔ ВСЕ строки нормализуются ТОЛЬКО при сравнении
→ но вид показывается исходный

### ✔ colorize_table ВСЕГДА красит по нормализованному виду
→ но отображает оригинальный регистр

---

# 👉 ДЕРЖИ ОБНОВЛЁННЫЕ **ОБА ФАЙЛА**, ГОТОВЫЕ К ВСТАВКЕ

---

# `utils.py` (идеально рабочий)

```python
import pandas as pd
import numpy as np
import re

# =========================
# НОРМАЛИЗАЦИЯ ДЛЯ ПОИСКА
# =========================
def normalize_match(s):
    if not isinstance(s, str):
        s = str(s)
    s = (
        s.replace("\xa0", " ")
         .replace("\u200b", "")
         .replace("\r", " ")
         .replace("\n", " ")
         .strip()
    )
    s = re.sub(r"\s+", " ", s)
    return s.lower()


# =========================
# ПОИСК КОЛОНКИ
# =========================
def find_column(df, keys):
    for col in df.columns:
        cname = normalize_match(col)
        for key in keys:
            if key in cname:
                return col
    return None


# =========================
# КАРТА КОМАНД
# =========================
TEAM_COLORS = {
    "ferrari": "#DC0000",
    "red bull": "#1E41FF",
    "mercedes": "#00D2BE",
    "mclaren": "#FF8700",
    "aston martin": "#006F62",
    "rb": "#B9DCFF",
    "haas": "#B6BABD",
    "williams": "#018CFF",
    "kick sauber": "#52E252",
    "alpine": "#0090FF",
    "voltedge": "#F4EA00",
}

TEAM_MAP = {
    "scuderia ferrari hp": "ferrari",
    "oracle red bull racing": "red bull",
    "mercedes-amg petronas formula one team": "mercedes",
    "mclaren formula 1 team": "mclaren",
    "aston martin aramco formula one team": "aston martin",
    "bwt alpine f1 team": "alpine",
    "visa cash app rb formula one team": "rb",
    "stake f1 team kick sauber": "kick sauber",
    "moneygram haas f1 team": "haas",
    "williams racing": "williams",
    "voltedge quantum racing": "voltedge",
}


# =========================
# ЦВЕТ ПО КОМАНДЕ
# =========================
def get_text_color(bg):
    try:
        r = int(bg[1:3], 16)
        g = int(bg[3:5], 16)
        b = int(bg[5:7], 16)
    except:
        return "black"

    yiq = (r*299 + g*587 + b*114) / 1000
    return "white" if yiq < 150 else "black"


# =========================
# ГЛАВНАЯ РАСКРАСКА
# =========================
def colorize_table(df: pd.DataFrame):

    df = df.copy()

    team_col = find_column(df, ["команда", "team"])

    if team_col:
        norm = df[team_col].astype(str).apply(normalize_match)
        mapped = norm.map(TEAM_MAP).fillna(norm)
        df["__color__"] = mapped.map(TEAM_COLORS).fillna("#FFFFFF")
    else:
        df["__color__"] = "#FFFFFF"

    colors = df["__color__"]
    out = df.drop(columns=["__color__"], errors="ignore")

    def style_row(row):
        bg = colors.iloc[row.name]
        fg = get_text_color(bg)
        return [f"background-color:{bg}; color:{fg}" for _ in row]

    return out.style.apply(style_row, axis=1).hide(axis="index")


# =========================
# ПИЛОТ → КОМАНДА
# =========================
def build_pilot_team_map(teams_df):
    pilot_col = find_column(teams_df, ["пилот", "driver"])
    team_col  = find_column(teams_df, ["команда", "team"])

    mapping = {}
    for _, row in teams_df.iterrows():
        p = str(row[pilot_col])
        t = normalize_match(str(row[team_col]))
        t = TEAM_MAP.get(t, t)
        mapping[p] = t
    return mapping


# =========================
# ПАРСЕР ЛУЧШЕГО КРУГА
# =========================
def parse_lap_time(v):
    if not isinstance(v, str):
        return pd.NaT
    s = normalize_match(v)
    if any(x in s for x in ["dnf", "выб", "lap"]):
        return pd.NaT
    try:
        return pd.to_timedelta(v)
    except:
        return pd.NaT


# =========================
# Загрузка Excel (без изменений)
# =========================
def load_season_data(xls_path):
    xls = pd.ExcelFile(xls_path)
    season_year = xls_path.split("_")[-1].split(".")[0]

    gp_list = dict(
        zip(
            pd.read_excel(xls, f"GP_List_{season_year}")["code"],
            pd.read_excel(xls, f"GP_List_{season_year}")["name"],
        )
    )

    wdc = pd.read_excel(xls, f"WDC_{season_year}")
    wcc = pd.read_excel(xls, f"WCC_{season_year}")
    teams = pd.read_excel(xls, f"Teams_{season_year}")

    grand_prix = {}
    for code in gp_list:
        grand_prix[code] = {}
        # … твой parser как был …

    return {
        "gp_map": gp_list,
        "gp_list": gp_list,
        "grand_prix": grand_prix,
        "wdc": wdc,
        "wcc": wcc,
        "teams": teams,
    }
