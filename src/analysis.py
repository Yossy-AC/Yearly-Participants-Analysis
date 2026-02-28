import pandas as pd

from src.data_loader import MONTH_LABELS


def annual_total(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby("year", as_index=False)["participants"]
        .sum()
        .sort_values("year")
    )


def by_course_year(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby(["course_name", "year"], as_index=False)["participants"]
        .sum()
        .pivot(index="course_name", columns="year", values="participants")
        .fillna(0)
        .astype(int)
    )


def by_classroom_year(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby(["classroom", "year"], as_index=False)["participants"]
        .sum()
        .pivot(index="classroom", columns="year", values="participants")
        .fillna(0)
        .astype(int)
    )


def by_instructor_year(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby(["instructor", "year"], as_index=False)["participants"]
        .sum()
        .pivot(index="instructor", columns="year", values="participants")
        .fillna(0)
        .astype(int)
    )


def monthly_seasonality(df: pd.DataFrame) -> pd.DataFrame:
    result = (
        df.groupby(["year", "month"], as_index=False)["participants"]
        .sum()
    )
    result["month"] = pd.Categorical(result["month"], categories=MONTH_LABELS, ordered=True)
    return result.sort_values(["year", "month"])


def course_yoy(df: pd.DataFrame, course_name: str) -> pd.DataFrame:
    subset = df[df["course_name"] == course_name]
    return (
        subset.groupby(["year", "month"], as_index=False)["participants"]
        .sum()
        .sort_values(["year", "month"])
    )


def instructor_monthly_heatmap(df: pd.DataFrame) -> pd.DataFrame:
    result = (
        df.groupby(["instructor", "month"], as_index=False)["participants"]
        .sum()
        .pivot(index="instructor", columns="month", values="participants")
        .fillna(0)
        .astype(int)
    )
    ordered_cols = [m for m in MONTH_LABELS if m in result.columns]
    return result[ordered_cols]


def top_courses(df: pd.DataFrame, n: int = 20) -> pd.DataFrame:
    return (
        df.groupby("course_name", as_index=False)["participants"]
        .sum()
        .sort_values("participants", ascending=False)
        .head(n)
    )


def top_classrooms(df: pd.DataFrame, n: int = 20) -> pd.DataFrame:
    return (
        df.groupby("classroom", as_index=False)["participants"]
        .sum()
        .sort_values("participants", ascending=False)
        .head(n)
    )


def by_grade_year(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby(["grade", "year"], as_index=False)["participants"]
        .sum()
        .pivot(index="grade", columns="year", values="participants")
        .fillna(0)
        .astype(int)
    )


def grade_trend(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby(["grade", "year"], as_index=False)["participants"]
        .sum()
        .sort_values(["year", "grade"])
    )


def classroom_trend(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby(["classroom", "year"], as_index=False)["participants"]
        .sum()
        .sort_values(["year", "classroom"])
    )


def yoy_change(pivot_df: pd.DataFrame) -> pd.DataFrame:
    """年度ピボットテーブルから前年比増減を計算する。

    入力: by_grade_year() 等の出力（index=項目名, columns=年度, values=受講者数）
    出力: 元のピボット + 「前年比」「増減率(%)」列を追加したDataFrame
    最新2年度を比較する。
    """
    years = sorted(pivot_df.columns.tolist())
    result = pivot_df.copy()
    if len(years) >= 2:
        cur, prev = years[-1], years[-2]
        result["前年比"] = (result[cur] - result[prev]).astype(int)
        result["増減率(%)"] = (
            result["前年比"] / result[prev].replace(0, float("nan")) * 100
        ).round(1)
    return result
