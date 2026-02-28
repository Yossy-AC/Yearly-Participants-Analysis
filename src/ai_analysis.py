import anthropic
import pandas as pd

MODEL = "claude-sonnet-4-6"


def _build_prompt(summary_dict: dict) -> str:
    lines = [
        "あなたは教育機関の受講者数データを分析するアシスタントです。",
        "以下のデータをもとに、日本語で分析してください。\n",
    ]
    for title, content in summary_dict.items():
        lines.append(f"## {title}\n{content}\n")
    lines.append(
        "上記データについて、以下の3点を回答してください：\n\n"
        "1. **全体サマリー**: 受講者数の全体的な傾向を2〜3文で説明してください。\n"
        "2. **増減の要因分析**: 前年比で大きく変動した項目を取り上げ、考えられる要因を説明してください。\n"
        "3. **次年度の予測**: トレンドをもとに来年度の見通しを述べてください。\n"
    )
    return "\n".join(lines)


def build_summary_dict(df: pd.DataFrame) -> dict:
    from src.analysis import (
        annual_total, by_grade_year, by_classroom_year,
        by_course_year, monthly_seasonality, yoy_change,
    )
    summary = {}

    ann = annual_total(df)
    summary["年度別合計受講者数"] = ann.to_string(index=False)

    mon = monthly_seasonality(df)
    pivot_mon = mon.pivot_table(
        index="month", columns="year", values="participants", aggfunc="sum"
    )
    summary["月別受講者数（年度×月）"] = pivot_mon.to_string()

    try:
        yoy_grade = yoy_change(by_grade_year(df))
        summary["学年別前年比増減"] = yoy_grade.to_string()
    except Exception:
        pass

    try:
        yoy_cls = yoy_change(by_classroom_year(df))
        summary["教室別前年比増減"] = yoy_cls.to_string()
    except Exception:
        pass

    try:
        yoy_course = yoy_change(by_course_year(df))
        latest_year_col = yoy_course.columns[-3]
        top_courses = yoy_course.nlargest(20, latest_year_col)
        summary["講座別前年比増減（上位20件）"] = top_courses.to_string()
    except Exception:
        pass

    return summary


def run_analysis(api_key: str, df: pd.DataFrame) -> str:
    summary_dict = build_summary_dict(df)
    prompt = _build_prompt(summary_dict)

    client = anthropic.Anthropic(api_key=api_key)
    message = client.messages.create(
        model=MODEL,
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text
