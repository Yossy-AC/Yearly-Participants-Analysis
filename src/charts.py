import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from src.data_loader import MONTH_LABELS

_MONTH_ORDER = MONTH_LABELS


def annual_total_chart(df_annual: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    fig.add_bar(
        x=df_annual["year"].astype(str),
        y=df_annual["participants"],
        name="受講者数",
        marker_color="#4C72B0",
    )
    fig.add_scatter(
        x=df_annual["year"].astype(str),
        y=df_annual["participants"],
        mode="lines+markers",
        name="推移",
        line=dict(color="#DD8452", width=2),
        marker=dict(size=8),
    )
    fig.update_layout(
        title="年度別合計受講者数",
        xaxis_title="年度",
        yaxis_title="受講者数（人）",
        legend=dict(orientation="h", y=1.05),
        hovermode="x unified",
    )
    fig.update_xaxes(type="category")
    return fig


def course_ranking_chart(df_top: pd.DataFrame) -> go.Figure:
    fig = px.bar(
        df_top.sort_values("participants"),
        x="participants",
        y="course_name",
        orientation="h",
        labels={"participants": "受講者数（人）", "course_name": "講座名"},
        title="講座別受講者数ランキング",
        color="participants",
        color_continuous_scale="Blues",
    )
    fig.update_layout(coloraxis_showscale=False, yaxis_title="")
    return fig


def classroom_ranking_chart(df_top: pd.DataFrame) -> go.Figure:
    fig = px.bar(
        df_top.sort_values("participants"),
        x="participants",
        y="classroom",
        orientation="h",
        labels={"participants": "受講者数（人）", "classroom": "教室"},
        title="教室別受講者数ランキング",
        color="participants",
        color_continuous_scale="Greens",
    )
    fig.update_layout(coloraxis_showscale=False, yaxis_title="")
    return fig


def course_yoy_chart(df_yoy: pd.DataFrame, course_name: str) -> go.Figure:
    df_yoy = df_yoy.copy()
    df_yoy["year"] = df_yoy["year"].astype(str)
    fig = px.bar(
        df_yoy,
        x="month",
        y="participants",
        color="year",
        barmode="group",
        category_orders={"month": _MONTH_ORDER},
        labels={"participants": "受講者数（人）", "month": "月", "year": "年度"},
        title=f"「{course_name}」の年次比較",
        color_discrete_sequence=px.colors.qualitative.Set2,
    )
    fig.update_layout(hovermode="x unified")
    return fig


def monthly_seasonality_chart(df_monthly: pd.DataFrame) -> go.Figure:
    df_monthly = df_monthly.copy()
    df_monthly["year"] = df_monthly["year"].astype(str)
    fig = px.line(
        df_monthly,
        x="month",
        y="participants",
        color="year",
        markers=True,
        category_orders={"month": _MONTH_ORDER},
        labels={"participants": "受講者数（人）", "month": "月", "year": "年度"},
        title="月別受講者数の季節性",
        color_discrete_sequence=px.colors.qualitative.Set1,
    )
    fig.update_layout(hovermode="x unified")
    return fig


def instructor_bar_chart(df_pivot: pd.DataFrame) -> go.Figure:
    years = [str(c) for c in df_pivot.columns]
    fig = go.Figure()
    for year in years:
        fig.add_bar(
            name=str(year),
            x=df_pivot.index.tolist(),
            y=df_pivot[int(year)].tolist() if int(year) in df_pivot.columns else df_pivot[year].tolist(),
        )
    fig.update_layout(
        barmode="group",
        title="講師別担当受講者数（年次比較）",
        xaxis_title="講師",
        yaxis_title="受講者数（人）",
        hovermode="x unified",
    )
    return fig


def instructor_heatmap_chart(df_heat: pd.DataFrame) -> go.Figure:
    fig = px.imshow(
        df_heat,
        labels=dict(x="月", y="講師", color="受講者数"),
        title="講師×月 受講者数ヒートマップ",
        color_continuous_scale="YlOrRd",
        aspect="auto",
    )
    fig.update_xaxes(side="top")
    return fig


def grade_trend_chart(df_trend: pd.DataFrame) -> go.Figure:
    df_trend = df_trend.copy()
    df_trend["grade"] = df_trend["grade"].astype(str)
    df_trend["year"] = df_trend["year"].astype(str)
    fig = px.bar(
        df_trend,
        x="grade",
        y="participants",
        color="year",
        barmode="group",
        labels={"participants": "受講者数（人）", "grade": "学年", "year": "年度"},
        title="学年別受講者数（年度比較）",
        color_discrete_sequence=px.colors.qualitative.Set2,
    )
    fig.update_layout(hovermode="x unified")
    fig.update_xaxes(type="category")
    return fig


def classroom_trend_chart(df_trend: pd.DataFrame) -> go.Figure:
    df_trend = df_trend.copy()
    df_trend["classroom"] = df_trend["classroom"].astype(str)
    df_trend["year"] = df_trend["year"].astype(str)
    fig = px.bar(
        df_trend,
        x="classroom",
        y="participants",
        color="year",
        barmode="group",
        labels={"participants": "受講者数（人）", "classroom": "教室", "year": "年度"},
        title="教室別受講者数（年度比較）",
        color_discrete_sequence=px.colors.qualitative.Pastel,
    )
    fig.update_layout(hovermode="x unified")
    fig.update_xaxes(type="category")
    return fig


def classroom_trend_line_chart(df_trend: pd.DataFrame) -> go.Figure:
    df_trend = df_trend.copy()
    df_trend["classroom"] = df_trend["classroom"].astype(str)
    df_trend["year"] = df_trend["year"].astype(int)
    fig = px.line(
        df_trend,
        x="year",
        y="participants",
        color="classroom",
        markers=True,
        labels={"participants": "受講者数（人）", "year": "年度", "classroom": "教室"},
        title="教室別受講者数（経年推移）",
        color_discrete_sequence=px.colors.qualitative.Set2,
    )
    fig.update_layout(hovermode="x unified")
    fig.update_xaxes(type="category")
    return fig


def annual_trend_by_month_chart(df_monthly: pd.DataFrame) -> go.Figure:
    pivot = df_monthly.pivot_table(
        index="month", columns="year", values="participants", aggfunc="sum"
    ).reindex(_MONTH_ORDER)
    fig = go.Figure()
    for year in pivot.columns:
        fig.add_scatter(
            x=pivot.index.tolist(),
            y=pivot[year].tolist(),
            mode="lines+markers",
            name=str(year),
        )
    fig.update_layout(
        title="年度別月次推移（重ね合わせ）",
        xaxis_title="月",
        yaxis_title="受講者数（人）",
        hovermode="x unified",
    )
    return fig
