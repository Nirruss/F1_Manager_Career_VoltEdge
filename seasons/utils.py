import pandas as pd
import numpy as np
import re

def normalize_cols(s):
    if not isinstance(s, str):
        return s

    # убираем ВСЕ типы пробелов
    s = re.sub(r"\p{Z}+", " ", s)
    s = s.replace("\u200b", "")   # zero-width space
    s = s.replace("\xa0", " ")    # NBSP
    s = s.replace("\u2009", " ")  # thin space
    s = s.replace("\u2007", " ")  # figure space
    s = s.replace("\u202F", " ")  # narrow no-break space

    return s.strip().lower()


def normalize_team_name(s: str):
    s = normalize_cols(s)
    # чтобы было прям безопасно — убираем двойные пробелы
    s = re.sub(r"\s+", " ", s)
    return s


def find_column(df, keywords):
    """
    Ищет колонку по ключевым словам в НАЗВАНИЯХ столбцов.
    Возвращает оригинальное имя столбца или None.
    """
    norm = {}

    # нормализуем названия колонок в строку
    for col in df.columns:
        if isinstance(col, str):
            n = normalize_cols(col)
        else:
            # на всякий случай: числа, None и т.п.
            n = str(col).strip().lower()
        norm[col] = n

    for col, n in norm.items():
        if not isinstance(n, str):
            continue
        for key in keywords:
            if key in n:
                return col

    return None



# ========================================
# ЦВЕТА КОМАНД
# ========================================
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
    "oracle red bull racing": "red bull",
    "mercedes-amg petronas formula one team": "mercedes",
    "scuderia ferrari hp": "ferrari",
    "mclaren formula 1 team": "mclaren",
    "aston martin aramco formula one team": "aston martin",
    "bwt alpine f1 team": "alpine",
    "visa cash app rb formula one team": "rb",
    "stake f1 team kick sauber": "kick sauber",
    "moneygram haas f1 team": "haas",
    "williams racing": "williams",
    "voltedge quantum racing": "voltedge",
}


# ========================================
# КОНТРАСТНЫЙ ТЕКСТ
# ========================================
def get_text_color(bg):
    try:
        r = int(bg[1:3], 16)
        g = int(bg[3:5], 16)
        b = int(bg[5:7], 16)
    except Exception:
        return "black"
    yiq = (r * 299 + g * 587 + b * 114) / 1000
    return "white" if yiq < 150 else "black"


# ========================================
# ОКРАСКА ТАБЛИЦ
# ========================================
def colorize_table(df: pd.DataFrame):
    if df is None or df.empty:
        return df

    df = df.copy()
    df = df.applymap(lambda x: str(x).replace("\xa0", " ").strip()
                     if isinstance(x, str) else x)

    team_col = find_column(df, ["команда", "team", "команды"])

    if team_col:
        # нормализуем ТОЛЬКО значение, НЕ заголовок
        normalized = df[team_col].astype(str).apply(normalize_cols)

        mapped = df[team_col].astype(str).apply(normalize_team_name).map(TEAM_MAP)


        df["__color__"] = mapped.map(TEAM_COLORS).fillna("#FFFFFF")
    else:
        df["__color__"] = "#FFFFFF"

    df = df.reset_index(drop=True)
    row_colors = df["__color__"]

    display_df = df.drop(columns=["__color__"], errors="ignore")

    def row_style(row):
        bg = row_colors.iloc[row.name]
        fg = get_text_color(bg)
        return [f"background-color:{bg}; color:{fg}" for _ in row]

    return display_df.style.apply(row_style, axis=1).hide(axis="index")


# ========================================
# РАЗБОР ЛУЧШЕГО КРУГА
# ========================================
def parse_lap_time(val):
    if not isinstance(val, str):
        return pd.NaT
    s = normalize_cols(val)
    if any(x in s for x in ["круг", "lap", "dnf", "выб"]):
        return pd.NaT
    try:
        return pd.to_timedelta(val)
    except Exception:
        return pd.NaT


# ========================================
# КАРТА ПИЛОТ → КОМАНДА
# ========================================
def build_pilot_team_map(teams_df: pd.DataFrame):
    if teams_df is None or teams_df.empty:
        return {}

    teams_df = teams_df.copy()
    pilot_col = find_column(teams_df, ["пилот", "driver"])
    team_col = find_column(teams_df, ["команда"])

    if not pilot_col or not team_col:
        return {}

    mapping = {}
    for _, row in teams_df.iterrows():
        pilot = str(row[pilot_col]).strip()
        team_raw = normalize_cols(str(row[team_col]).strip())
        team = TEAM_MAP.get(team_raw, team_raw)
        mapping[pilot] = team
    return mapping


# ========================================
# ПАРСЕР СЕЗОНА
# ========================================
def load_season_data(xls_path: str):

    xls = pd.ExcelFile(xls_path)
    season_year = xls_path.split("_")[-1].split(".")[0]

    # ----- GP LIST -----
    gp_sheet = f"GP_List_{season_year}"
    gp_df = pd.read_excel(xls, gp_sheet)
    gp_df.columns = ["code", "name"]

    gp_list = dict(zip(
        gp_df["code"].astype(str).str.strip(),
        gp_df["name"].astype(str).str.strip()
    ))

    # ----- WDC / WCC -----
    wdc = pd.read_excel(xls, f"WDC_{season_year}")
    wcc = pd.read_excel(xls, f"WCC_{season_year}")

    # ----- TEAMS -----
    teams = pd.read_excel(xls, f"Teams_{season_year}")

    # ----- ГРАН-ПРИ -----
    grand_prix = {}

    for code in gp_list:
        if code not in xls.sheet_names:
            continue

        # читаем целиком без заголовков
        df = pd.read_excel(xls, code, header=None)

        sections = {}
        key = None
        temp = []
        skip_header = False

        # --- основной проход по строкам ---
        for _, row in df.iterrows():
            row_text = " ".join(
                normalize_cols(str(x)) for x in row.values if pd.notna(x)
            ).strip()

            if row_text == "" or row_text == "nan":
                continue

            # -------- Блок QUALIFICATION (по ключевому слову) --------
            if any(x in row_text for x in [
                "qualificat",       # в т.ч. обрезанный заголовок
                "qualification",
                "qualify",
                "квалиф",
            ]):
                if key and temp:
                    sections[key] = pd.DataFrame(temp)
                key = "qualifying"
                temp = []
                skip_header = True
                continue

            # -------- Блок RACE DRIVERS --------
            if "race_pilots" in row_text or "race drivers" in row_text:
                if key and temp:
                    sections[key] = pd.DataFrame(temp)
                key = "race_drivers"
                temp = []
                skip_header = True
                continue

            # -------- Блок RACE TEAMS --------
            if "race_teams" in row_text or "race teams" in row_text:
                if key and temp:
                    sections[key] = pd.DataFrame(temp)
                key = "race_teams"
                temp = []
                skip_header = True
                continue

            # пропускаем строку-шапку сразу после объявления блока
            if skip_header:
                skip_header = False
                continue

            # копим строки внутри текущего блока
            if key is not None:
                temp.append(list(row))

        # закрываем последний блок
        if key and temp:
            sections[key] = pd.DataFrame(temp)

        # ---------- ФОЛБЭК: если квалификация не нашлась ----------
        if "qualifying" not in sections:
            qual_header_idx = None
            race_pilots_row_idx = None

            for idx, row in df.iterrows():
                norm_cells = [normalize_cols(str(x)) for x in row.values if pd.notna(x)]
                joined = " ".join(norm_cells)

                # первая шапка с "позиция" — считаем её шапкой квалификации
                if qual_header_idx is None and any(
                    ("позиция" in c) or ("position" in c) for c in norm_cells
                ):
                    qual_header_idx = idx
                    continue

                # первая строка с race_pilots — начало блока гонки пилотов
                if qual_header_idx is not None and (
                    "race_pilots" in joined or "race drivers" in joined
                ):
                    race_pilots_row_idx = idx
                    break

            if qual_header_idx is not None and race_pilots_row_idx is not None:
                qual_df = df.iloc[qual_header_idx + 1: race_pilots_row_idx].reset_index(drop=True)
                sections["qualifying"] = qual_df

        grand_prix[code] = sections

    return {
        "gp_map": gp_list,
        "gp_list": gp_list,
        "grand_prix": grand_prix,
        "wdc": wdc,
        "wcc": wcc,
        "teams": teams,
    }
