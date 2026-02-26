import re
import pandas as pd
import streamlit as st

MONTH_LABELS = [
    "4月", "5月", "6月", "7月", "8月(夏期)",
    "9月", "10月", "11月", "12月", "冬期",
    "1月", "2月",
]

COLUMN_NAMES = [
    "grade", "classroom", "course_name", "class_hours", "instructor",
    "4月", "5月", "6月", "7月", "8月(夏期)",
    "9月", "10月", "11月", "12月", "冬期",
    "1月", "2月",
]


def _extract_year(sheet_name: str) -> int | None:
    m = re.search(r"\d{4}", sheet_name)
    return int(m.group()) if m else None


def _extract_genre_and_subject(course_name: str) -> tuple[str | None, str | None]:
    """講座名から講座ジャンルと科目を抽出"""
    GENRES = ["ｱﾄﾞﾊﾞﾝｽ", "ﾊｲﾚﾍﾞﾙ", "ﾊｲﾌﾞﾘｯﾄﾞ", "共通ﾃｽﾄ"]
    SUBJECTS = ["英語", "数学", "国語"]

    course_str = str(course_name) if pd.notna(course_name) else ""

    genre = None
    for g in GENRES:
        if g in course_str:
            genre = g
            break

    subject = None
    for s in SUBJECTS:
        if s in course_str:
            subject = s
            break

    return genre, subject


@st.cache_data
def load_excel(file_path_or_bytes) -> pd.DataFrame:
    xl = pd.ExcelFile(file_path_or_bytes, engine="openpyxl")
    frames = []

    for sheet in xl.sheet_names:
        year = _extract_year(sheet)
        if year is None:
            continue

        df_raw = xl.parse(sheet, header=0)

        # 列数が仕様より少ない場合はスキップ
        if df_raw.shape[1] < len(COLUMN_NAMES):
            continue

        df_raw = df_raw.iloc[:, : len(COLUMN_NAMES)].copy()
        df_raw.columns = COLUMN_NAMES

        # 空行・ヘッダー行の除外
        df_raw = df_raw.dropna(subset=["course_name"])
        df_raw = df_raw[df_raw["course_name"].astype(str).str.strip() != ""]

        # 月列をlong形式に変換
        id_cols = ["grade", "classroom", "course_name", "class_hours", "instructor"]
        df_long = df_raw.melt(
            id_vars=id_cols,
            value_vars=MONTH_LABELS,
            var_name="month",
            value_name="participants",
        )

        df_long["year"] = year
        df_long["participants"] = (
            pd.to_numeric(df_long["participants"], errors="coerce").fillna(0).astype(int)
        )

        frames.append(df_long)

    if not frames:
        return pd.DataFrame(
            columns=["year", "grade", "classroom", "course_name",
                     "class_hours", "instructor", "month", "participants"]
        )

    result = pd.concat(frames, ignore_index=True)

    # 教室・学年を整数型に統一
    result["grade"] = pd.to_numeric(result["grade"], errors="coerce").astype("Int64")
    result["classroom"] = pd.to_numeric(result["classroom"], errors="coerce").astype("Int64")

    # 講座名から講座ジャンルと科目を抽出
    genres_subjects = result["course_name"].apply(_extract_genre_and_subject)
    result["genre"] = [x[0] for x in genres_subjects]
    result["subject"] = [x[1] for x in genres_subjects]

    result["month"] = pd.Categorical(result["month"], categories=MONTH_LABELS, ordered=True)
    result = result.sort_values(["year", "month"]).reset_index(drop=True)
    return result
