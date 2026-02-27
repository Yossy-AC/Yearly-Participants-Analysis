import pandas as pd
import streamlit as st

from src import analysis, charts
from src.data_loader import load_excel
from src.normalizer import apply_aliases, load_aliases

st.set_page_config(
    page_title="年次受講者数分析",
    page_icon="📊",
    layout="wide",
)

st.markdown(
    """
    <style>
    [role="dialog"] [data-testid="stFileUploadDropzone"] small {
        display: none !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def _set_filter(key, value):
    st.session_state[key] = value


# ────────────────────────────────────────────
# セッション状態の初期化
# ────────────────────────────────────────────
if "aliases" not in st.session_state:
    st.session_state.aliases = load_aliases()

# ────────────────────────────────────────────
# サイドバー
# ────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 📊 年次受講者数分析")
    st.divider()

    # ファイルアップロード
    if "uploaded_file" not in st.session_state:
        st.session_state.uploaded_file = None

    if st.session_state.uploaded_file is None:
        with st.expander("📁 ファイルアップロード", expanded=True):
            uploaded = st.file_uploader(
                label="",
                type=["xlsx", "xls"],
                help="シート名に年度（例：2025年度）を含むExcelファイルを選択してください。",
            )
            if uploaded is not None:
                st.session_state.uploaded_file = uploaded
                st.rerun()
    else:
        st.markdown("<p style='font-size: 14px;'>✅ File Loaded</p>", unsafe_allow_html=True)
        if st.button("📁 別のファイルをアップロード"):
            st.session_state.uploaded_file = None
            st.cache_data.clear()
            st.rerun()
        uploaded = st.session_state.uploaded_file

    if uploaded is None:
        st.stop()

    try:
        df_raw = load_excel(uploaded)
    except Exception as e:
        st.error(f"ファイルの読み込みに失敗しました。\n\n詳細: {e}")
        st.stop()

    if df_raw.empty:
        st.warning("データが見つかりませんでした。シート名に年度（例：2025年度）が含まれているか確認してください。")
        st.stop()

    df_raw = apply_aliases(df_raw, st.session_state.aliases)

    all_years = sorted(df_raw["year"].unique().tolist())
    all_grades = sorted(df_raw["grade"].dropna().unique().astype(int).tolist())
    all_classrooms = sorted(df_raw["classroom"].dropna().unique().astype(int).tolist())
    all_genres = sorted([x for x in df_raw["genre"].unique() if pd.notna(x)])
    all_subjects = sorted([x for x in df_raw["subject"].unique() if pd.notna(x)])
    all_instructors = sorted(df_raw["instructor"].dropna().unique().tolist())
    all_times = sorted([str(x) if pd.notna(x) else "空白" for x in df_raw["class_hours"].unique()])

    st.markdown("**フィルター設定**")

    # ヘルパー関数：チェックボックス列を描画
    def render_checkbox_filter(label, items, session_key, num_cols=4):
        st.markdown(f"**{label}**")
        cols = st.columns(num_cols)

        for i in range(len(items)):
            cb_key = f"cb_{session_key}_{i}"
            if cb_key not in st.session_state:
                st.session_state[cb_key] = True

        for i, item in enumerate(items):
            col = cols[i % num_cols]
            cb_key = f"cb_{session_key}_{i}"
            col.checkbox(str(item), key=cb_key)

        def select_all():
            for i in range(len(items)):
                st.session_state[f"cb_{session_key}_{i}"] = True

        st.button("全選択", key=f"btn_all_{session_key}", on_click=select_all)

        selected = [items[i] for i in range(len(items)) if st.session_state.get(f"cb_{session_key}_{i}", False)]
        return selected

    sel_years = render_checkbox_filter("年度", all_years, "filter_years", num_cols=3)
    sel_grades = render_checkbox_filter("学年", all_grades, "filter_grades", num_cols=4)
    sel_classrooms = render_checkbox_filter("教室", all_classrooms, "filter_classrooms", num_cols=3)
    sel_times = render_checkbox_filter("時間", all_times, "filter_times", num_cols=3)
    sel_genres = render_checkbox_filter("講座ジャンル", all_genres, "filter_genres", num_cols=2)
    sel_subjects = render_checkbox_filter("科目", all_subjects, "filter_subjects", num_cols=2)
    sel_instructors = render_checkbox_filter("担当講師", all_instructors, "filter_instructors", num_cols=2)

# フィルター選択チェック
if not any([sel_years, sel_grades, sel_classrooms, sel_genres, sel_subjects, sel_instructors, sel_times]):
    st.info("✋ 1つ以上のフィルターを選択してください。")
    st.stop()

# フィルター適用
df = df_raw.copy()
if sel_years:
    df = df[df["year"].isin(sel_years)]
if sel_grades:
    df = df[df["grade"].isin(sel_grades)]
if sel_classrooms:
    df = df[df["classroom"].isin(sel_classrooms)]
if sel_genres:
    df = df[df["genre"].isin(sel_genres)]
if sel_subjects:
    df = df[df["subject"].isin(sel_subjects)]
if sel_instructors:
    df = df[df["instructor"].isin(sel_instructors)]
if sel_times:
    time_filter = [None if t == "空白" else t for t in sel_times]
    df = df[df["class_hours"].isin(time_filter) | ((df["class_hours"].isna()) & ("空白" in sel_times))]

if df.empty:
    st.warning("フィルター条件に一致するデータがありません。")
    st.stop()

# ────────────────────────────────────────────
# ヘルパー：分析タブ共通の前年比 metric 表示
# ────────────────────────────────────────────
def render_yoy_metrics(pivot_df, max_items=8):
    """ピボットテーブルから上位項目の st.metric を表示する。"""
    years = sorted(pivot_df.columns.tolist())
    if len(years) < 2:
        return
    cur, prev = years[-1], years[-2]
    st.caption(f"📊 {cur}年度の上位{max_items}項目（下の数値は{prev}年度との比較）")
    # 最新年度の上位項目を選択
    top = pivot_df.nlargest(max_items, cur)
    cols = st.columns(min(len(top), 4))
    for i, (name, row) in enumerate(top.iterrows()):
        col = cols[i % len(cols)]
        cur_val = int(row[cur])
        prev_val = int(row[prev])
        delta = cur_val - prev_val
        pct = (delta / prev_val * 100) if prev_val != 0 else None
        delta_str = f"{delta:+,} 人"
        if pct is not None:
            delta_str += f" ({pct:+.1f}%)"
        col.metric(str(name), f"{cur_val:,} 人", delta=delta_str)


# ────────────────────────────────────────────
# タブ構成
# ────────────────────────────────────────────
tab_main, tab_annual, tab_monthly, tab_grade, tab_classroom, tab_course, tab_instructor, tab_export = st.tabs([
    "📊 メイン",
    "📈 経年推移",
    "🗓️ 年間推移",
    "🎓 学年別",
    "🏫 教室別",
    "📚 講座別",
    "👩‍🏫 担当別",
    "📥 データエクスポート",
])

# ══════════════════════════════════════════
# タブ1: メイン
# ══════════════════════════════════════════
with tab_main:
    st.header("メイン")

    df_annual = analysis.annual_total(df)
    available_years = sorted(df_annual["year"].tolist())

    col_sel1, col_sel2 = st.columns(2)
    with col_sel1:
        year_current = st.selectbox(
            "表示年度", available_years,
            index=len(available_years) - 1, key="dash_year_current"
        )
    with col_sel2:
        compare_options = [y for y in available_years if y != year_current]
        year_compare = st.selectbox(
            "比較年度", compare_options,
            index=max(0, len(compare_options) - 1) if compare_options else 0,
            key="dash_year_compare"
        ) if compare_options else None

    st.caption(f"📊 下の数値は{year_compare}年度との比較です（該当データがない場合は表示されません）")

    # KPI計算
    df_cur = df[df["year"] == year_current]
    cur_total = int(df_cur["participants"].sum())
    cur_courses = df_cur["course_name"].nunique()
    cur_months = df_cur["month"].nunique()
    cur_avg_month = int(cur_total / cur_months) if cur_months > 0 else 0
    cur_avg_course = int(cur_total / cur_courses) if cur_courses > 0 else 0

    delta_total = None
    delta_pct = None
    if year_compare is not None:
        df_cmp = df[df["year"] == year_compare]
        cmp_total = int(df_cmp["participants"].sum())
        if cmp_total > 0:
            delta_total = cur_total - cmp_total
            delta_pct = (delta_total / cmp_total) * 100

    col1, col2, col3, col4 = st.columns(4)
    col1.metric(
        f"{year_current}年度 総受講者数",
        f"{cur_total:,} 人",
        delta=f"{delta_total:+,} 人 ({delta_pct:+.1f}%)" if delta_total is not None else None,
    )
    col2.metric("講座数", f"{cur_courses} 講座")
    col3.metric("月平均受講者数", f"{cur_avg_month:,} 人")
    col4.metric("講座平均受講者数", f"{cur_avg_course:,} 人")

    st.markdown("---")

    # サマリーグラフ 2×2
    col_g1, col_g2 = st.columns(2)
    with col_g1:
        st.plotly_chart(charts.annual_total_chart(df_annual), use_container_width=True, key="main_annual")
    with col_g2:
        df_monthly_main = analysis.monthly_seasonality(df)
        st.plotly_chart(charts.annual_trend_by_month_chart(df_monthly_main), use_container_width=True, key="main_monthly")

    col_g3, col_g4 = st.columns(2)
    with col_g3:
        df_grade_main = analysis.grade_trend(df)
        st.plotly_chart(charts.grade_trend_chart(df_grade_main), use_container_width=True, key="main_grade")
    with col_g4:
        df_cls_main = analysis.classroom_trend(df)
        st.plotly_chart(charts.classroom_trend_chart(df_cls_main), use_container_width=True, key="main_classroom")

# ══════════════════════════════════════════
# タブ2: 経年推移
# ══════════════════════════════════════════
with tab_annual:
    st.header("経年推移")

    df_annual = analysis.annual_total(df)
    st.plotly_chart(charts.annual_total_chart(df_annual), use_container_width=True, key="annual_chart")

    st.markdown("---")
    st.subheader("年度別合計テーブル")
    st.dataframe(
        df_annual.rename(columns={"year": "年度", "participants": "受講者数（人）"}),
        use_container_width=True, hide_index=True,
    )

# ══════════════════════════════════════════
# タブ3: 年間推移
# ══════════════════════════════════════════
with tab_monthly:
    st.header("年間推移")

    df_monthly = analysis.monthly_seasonality(df)
    st.plotly_chart(charts.monthly_seasonality_chart(df_monthly), use_container_width=True, key="monthly_season")

    st.markdown("---")
    st.subheader("月別データ（表）")
    pivot_monthly = df_monthly.pivot_table(
        index="month", columns="year", values="participants", aggfunc="sum"
    )
    st.dataframe(pivot_monthly, use_container_width=True)

# ══════════════════════════════════════════
# タブ4: 学年別
# ══════════════════════════════════════════
with tab_grade:
    st.header("学年別")

    try:
        pivot_grade = analysis.by_grade_year(df)
        render_yoy_metrics(pivot_grade)

        st.markdown("---")
        df_grade_trend = analysis.grade_trend(df)
        st.plotly_chart(charts.grade_trend_chart(df_grade_trend), use_container_width=True, key="grade_chart")

        st.markdown("---")
        st.subheader("学年×年度 前年比増減")
        st.dataframe(analysis.yoy_change(pivot_grade), use_container_width=True)
    except Exception:
        st.info("学年データが不足しています。")

# ══════════════════════════════════════════
# タブ5: 教室別
# ══════════════════════════════════════════
with tab_classroom:
    st.header("教室別")

    try:
        pivot_cls = analysis.by_classroom_year(df)
        render_yoy_metrics(pivot_cls)

        st.markdown("---")
        df_cls_trend = analysis.classroom_trend(df)
        st.plotly_chart(charts.classroom_trend_line_chart(df_cls_trend), use_container_width=True, key="classroom_trend_line")

        st.markdown("---")
        st.plotly_chart(charts.classroom_trend_chart(df_cls_trend), use_container_width=True, key="classroom_chart")

        st.markdown("---")
        st.subheader("教室×年度 前年比増減")
        st.dataframe(analysis.yoy_change(pivot_cls), use_container_width=True)
    except Exception:
        st.info("教室データが不足しています。")

# ══════════════════════════════════════════
# タブ6: 講座別
# ══════════════════════════════════════════
with tab_course:
    st.header("講座別")

    try:
        pivot_course = analysis.by_course_year(df)
        render_yoy_metrics(pivot_course)

        st.markdown("---")
        st.subheader("講座別 年次比較（ドリルダウン）")
        all_course_names = sorted(df["course_name"].unique().tolist())
        selected_course = st.selectbox("講座を選択", all_course_names, key="course_select")

        if selected_course:
            df_yoy = analysis.course_yoy(df, selected_course)
            st.plotly_chart(charts.course_yoy_chart(df_yoy, selected_course), use_container_width=True, key="course_yoy_chart")

        st.markdown("---")
        st.subheader("講座×年度 前年比増減")
        st.dataframe(analysis.yoy_change(pivot_course), use_container_width=True)
    except Exception:
        st.info("講座データが不足しています。")

# ══════════════════════════════════════════
# タブ7: 担当別
# ══════════════════════════════════════════
with tab_instructor:
    st.header("担当別")

    try:
        pivot_inst = analysis.by_instructor_year(df)
        render_yoy_metrics(pivot_inst)

        st.markdown("---")
        st.plotly_chart(charts.instructor_bar_chart(pivot_inst), use_container_width=True, key="instructor_bar")

        st.markdown("---")
        st.subheader("講師×月 受講者数ヒートマップ")
        df_heat = analysis.instructor_monthly_heatmap(df)
        if not df_heat.empty:
            st.plotly_chart(charts.instructor_heatmap_chart(df_heat), use_container_width=True, key="instructor_heat")
        else:
            st.info("ヒートマップの表示に十分なデータがありません。")

        st.markdown("---")
        st.subheader("担当×年度 前年比増減")
        st.dataframe(analysis.yoy_change(pivot_inst), use_container_width=True)
    except Exception:
        st.info("講師データが不足しています。")

# ══════════════════════════════════════════
# タブ8: データエクスポート
# ══════════════════════════════════════════
with tab_export:
    st.header("データエクスポート")

    st.subheader("フィルター適用済みデータ（全体）")
    st.download_button(
        "📥 CSVダウンロード（全データ）",
        data=df.to_csv(index=False).encode("utf-8-sig"),
        file_name="filtered_data.csv",
        mime="text/csv",
        key="dl_all_data",
    )

    st.markdown("---")

    export_configs = [
        ("学年×年度", analysis.by_grade_year, "grade_year_crosstab.csv"),
        ("教室×年度", analysis.by_classroom_year, "classroom_year_crosstab.csv"),
        ("講座×年度", analysis.by_course_year, "course_year_crosstab.csv"),
        ("担当×年度", analysis.by_instructor_year, "instructor_year_crosstab.csv"),
    ]

    for title, fn, filename in export_configs:
        st.subheader(f"{title} クロス集計")
        try:
            pivot = fn(df)
            st.dataframe(pivot, use_container_width=True)
            st.download_button(
                f"📥 CSVダウンロード（{title}）",
                data=pivot.to_csv().encode("utf-8-sig"),
                file_name=filename,
                mime="text/csv",
                key=f"dl_{filename}",
            )
        except Exception:
            st.info(f"{title}の集計に十分なデータがありません。")
        st.markdown("---")

    st.subheader("月別×年度 クロス集計")
    try:
        df_monthly_exp = analysis.monthly_seasonality(df)
        pivot_monthly_exp = df_monthly_exp.pivot_table(
            index="month", columns="year", values="participants", aggfunc="sum"
        )
        st.dataframe(pivot_monthly_exp, use_container_width=True)
        st.download_button(
            "📥 CSVダウンロード（月別×年度）",
            data=pivot_monthly_exp.to_csv().encode("utf-8-sig"),
            file_name="monthly_year_crosstab.csv",
            mime="text/csv",
            key="dl_monthly_year",
        )
    except Exception:
        st.info("月別集計に十分なデータがありません。")
