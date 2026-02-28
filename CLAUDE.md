# 年次受講者数分析アプリ — 開発者向けドキュメント

このプロジェクトの構成、設計パターン、開発時の注意点をまとめています。

---

## プロジェクト構成

```
Yearly-Participants-Analysis/
├── app.py                  # Streamlit メインアプリ（9タブ構成）
├── src/
│   ├── __init__.py
│   ├── data_loader.py      # Excel読み込み・long形式変換・@st.cache_data
│   ├── analysis.py         # データ集計ロジック
│   ├── charts.py           # Plotlyグラフ生成
│   ├── normalizer.py       # 表記ゆれ検出・マッピング管理
│   └── ai_analysis.py      # Claude API連携・AI分析サマリー生成
├── data/
│   ├── course_aliases.json # 講座名正規化マッピング（初期値:{}）
│   └── README.md
├── requirements.txt
└── README.md
```

---

## コア概念

### データフロー

```
Excel (17列固定)
  ↓
load_excel()
  ↓
long形式 DataFrame (11列)
  ↓
apply_aliases()  ← 表記ゆれ正規化
  ↓
フィルター適用（サイドバー）
  ↓
analysis.py (集計) → charts.py (Plotly描画)
  ↓
Streamlit タブで表示
```

### Excel列構成（固定17列）

| # | 列 | 例 |
|----|----|----|
| 1-5 | grade, classroom, course_name, class_hours, instructor | 3, 1, "英語Ⅰ", "90分", "田中" |
| 6-17 | 4月〜2月（12ヶ月） | 25, 28, 30, ... |

### 処理後 DataFrame列（11列）

| 列名 | 型 | 説明 |
|------|----|----|
| year | int | 年度（Excelのシート名から抽出） |
| grade | Int64 | 学年（nullable） |
| classroom | Int64 | 教室番号（nullable） |
| course_name | str | 講座名 |
| class_hours | str | 授業時間 |
| instructor | str | 講師名 |
| month | Categorical | 月（MONTH_LABELSで順序付け） |
| participants | int | 受講者数 |
| genre | str \| None | 講座ジャンル（抽出） |
| subject | str \| None | 科目（抽出） |

### MONTH_LABELS定数

```python
["4月", "5月", "6月", "7月", "8月(夏期)", "9月",
 "10月", "11月", "12月", "冬期", "1月", "2月"]
```

---

## 分析関数 (`src/analysis.py`)

### 年度別集計

```python
annual_total(df) → pd.DataFrame
# 出力: year, participants (年度別合計)

by_grade_year(df) → pd.DataFrame
# 出力: ピボットテーブル（index=学年, columns=年度）

by_classroom_year(df) → pd.DataFrame
# 出力: ピボットテーブル（index=教室, columns=年度）

by_course_year(df) → pd.DataFrame
# 出力: ピボットテーブル（index=講座, columns=年度）

by_instructor_year(df) → pd.DataFrame
# 出力: ピボットテーブル（index=講師, columns=年度）
```

### 月別・推移分析

```python
monthly_seasonality(df) → pd.DataFrame
# 出力: year, month(Categorical), participants (年月別合計)

grade_trend(df) → pd.DataFrame
# 出力: grade, year, participants (学年別年度推移、long形式)

classroom_trend(df) → pd.DataFrame
# 出力: classroom, year, participants (教室別年度推移、long形式)

course_yoy(df, course_name) → pd.DataFrame
# 出力: 指定講座の年月別推移
```

### 前年比増減計算（新規）

```python
yoy_change(pivot_df) → pd.DataFrame
# 入力: by_grade_year() 等の出力（ピボットテーブル）
# 出力: 元のピボット + 「前年比」「増減率(%)」列を追加
# ※最新2年度を比較
```

### ヒートマップ

```python
instructor_monthly_heatmap(df) → pd.DataFrame
# 出力: ピボットテーブル（index=講師, columns=月）
```

---

## グラフ関数 (`src/charts.py`)

| 関数 | 入力 | 出力グラフ |
|------|------|----------|
| `annual_total_chart(df_annual)` | `annual_total()` | 棒グラフ＋折れ線 |
| `monthly_seasonality_chart(df_monthly)` | `monthly_seasonality()` | 折れ線（年度別） |
| `annual_trend_by_month_chart(df_monthly)` | `monthly_seasonality()` | 折れ線（月別、重ね合わせ） |
| `grade_trend_chart(df_trend)` | `grade_trend()` | 棒グラフ（年度別グループ） |
| `classroom_trend_chart(df_trend)` | `classroom_trend()` | 棒グラフ（年度別グループ） |
| `course_yoy_chart(df_yoy, name)` | `course_yoy()` | 棒グラフ（月別グループ） |
| `instructor_bar_chart(df_pivot)` | `by_instructor_year()` | 棒グラフ（年度別グループ） |
| `instructor_heatmap_chart(df_heat)` | `instructor_monthly_heatmap()` | ヒートマップ |

---

## タブ構成詳細 (`app.py`)

### タブ1: メイン（📊）

**KPIカード（4つ）**:
- 年度選択（selectbox × 2: 表示年度、比較年度）
- 総受講者数（delta付き）
- 講座数
- 月平均受講者数
- 講座平均受講者数

**サマリーグラフ（2×2グリッド）**:
- 左上: `annual_total_chart()`
- 右上: `annual_trend_by_month_chart()`
- 左下: `grade_trend_chart()`
- 右下: `classroom_trend_chart()`

### タブ2: 経年推移（📈）

- `annual_total_chart()`
- 年度別合計テーブル

### タブ3: 年間推移（🗓️）

- `monthly_seasonality_chart()`
- `annual_trend_by_month_chart()`
- 月別データテーブル

### タブ4〜7: 分析タブ共通パターン

各タブ（学年別・教室別・講座別・担当別）は以下の構造:

```
┌─────────────────────────┐
│ st.metric × N           │  ← render_yoy_metrics()
│ （上位項目の前年比delta） │
├─────────────────────────┤
│ 年度比較グラフ            │  ← grade_trend_chart() 等
├─────────────────────────┤
│ 前年比増減テーブル        │  ← yoy_change() + st.dataframe()
│ （色付き）               │
└─────────────────────────┘
```

**タブ4: 学年別**
- `render_yoy_metrics(by_grade_year())`
- `grade_trend_chart()`
- `yoy_change(by_grade_year())`

**タブ5: 教室別**
- `render_yoy_metrics(by_classroom_year())`
- `classroom_trend_chart()`
- `yoy_change(by_classroom_year())`

**タブ6: 講座別**
- `render_yoy_metrics(by_course_year())`
- `course_yoy_chart()` (selectbox でドリルダウン)
- `yoy_change(by_course_year())`

**タブ7: 担当別**
- `render_yoy_metrics(by_instructor_year())`
- `instructor_bar_chart()`
- `instructor_heatmap_chart()`
- `yoy_change(by_instructor_year())`

### タブ8: データエクスポート（📥）

クロス集計表 + CSV ダウンロード:
- フィルター適用済み全データ
- 学年×年度（`by_grade_year()`）
- 教室×年度（`by_classroom_year()`）
- 講座×年度（`by_course_year()`）
- 担当×年度（`by_instructor_year()`）
- 月別×年度

### タブ9: AI分析（🤖）

`src/ai_analysis.py` による Claude API 連携:

```
┌─────────────────────────────────────────┐
│ APIキー未設定時: 警告 + secrets.toml 案内  │
├─────────────────────────────────────────┤
│ 「AI分析を実行」ボタン                    │
│  → build_summary_dict(df) でサマリー生成  │
│  → Claude API (claude-sonnet-4-6) 呼び出し│
│  → st.session_state["ai_result"] に保存  │
├─────────────────────────────────────────┤
│ 結果をMarkdown表示                       │
│ （全体サマリー・増減要因・次年度予測）     │
└─────────────────────────────────────────┘
```

**APIキー設定方法**:
```toml
# .streamlit/secrets.toml
ANTHROPIC_API_KEY = "sk-ant-xxxxxxx"
```

---

## フィルター実装（サイドバー）

### チェックボックス形式

各フィルターは複数列レイアウトのチェックボックスで構成:

```python
def render_checkbox_filter(label, items, session_key, num_cols=4):
    # 初期化: cb_{session_key}_{i} キーを True に設定
    # チェックボックスレンダリング（複数列）
    # 「全選択」ボタン: on_click で全てを True に設定
    # 選ばれたアイテムをリスト化して返却
```

### Session State 管理

- **multiselect代わり**: `cb_{session_key}_{i}` キーで各チェックボックスを個別管理
- **初期状態**: 全て True（全選択状態）
- **全選択ボタン**: `on_click` コールバックで全 checkbox を True に設定

### フィルター順序

1. 年度
2. 学年
3. 教室
4. 時間
5. 講座ジャンル
6. 科目
7. 担当講師

### フィルター適用ロジック

```python
if sel_years:
    df = df[df["year"].isin(sel_years)]
if sel_grades:
    df = df[df["grade"].isin(sel_grades)]
# ... 以下同様

# フィルター結果が空の場合
if df.empty:
    st.warning("...")
    st.stop()
```

---

## ヘルパー関数

### `render_yoy_metrics(pivot_df, max_items=8)`

ピボットテーブルから上位項目の st.metric を前年比delta付きで表示。

- 最新2年度を比較
- 上位 N 件を選択（デフォルト8件）
- 4列グリッドで表示

---

## 開発時の注意点

### 1. Session State と Streamlit ウィジェット

**問題**: `if st.button(): st.session_state[key] = value` は API エラー

**解決**: `on_click` コールバック方式を使用
```python
def callback():
    st.session_state[key] = value

st.button("label", on_click=callback)
```

### 2. Plotly チャートの `key` パラメータ

同じ関数を複数タブで呼ぶ場合、`key` パラメータで一意なIDを付与:
```python
st.plotly_chart(fn(), use_container_width=True, key="unique_key_per_tab")
```

### 3. CSV エンコーディング

Windows互換性のため `encode("utf-8-sig")` を使用（BOM付き）。

### 4. カテゴリカル型の月

`monthly_seasonality()` の出力では `month` が Categorical 型で、MONTH_LABELS の順序で並ぶ。
Plotly での自動ソートを避けるため、`category_orders` パラメータで明示的に指定。

### 5. nullable 整数型

`grade` と `classroom` は `Int64`（nullable）。
グループ化後に `astype(int)` で通常の int に変換する場合がある。

### 6. AI分析タブの APIキー管理

`st.secrets.get("ANTHROPIC_API_KEY", "")` で取得。キー未設定時は分析ボタンを非表示にし、設定方法を案内する。

---

## デプロイメント

### ローカル実行

```bash
streamlit run app.py
# http://localhost:8501
```

### 依存パッケージ

[requirements.txt](requirements.txt) 参照

---

## AI分析モジュール (`src/ai_analysis.py`)

| 関数 | 説明 |
|------|------|
| `build_summary_dict(df)` | DataFrame から年度別・月別・学年別・教室別・講座別の集計テキストを生成 |
| `_build_prompt(summary_dict)` | サマリー辞書からClaudeへのプロンプトを組み立て |
| `run_analysis(api_key, df)` | APIを呼び出しMarkdownテキストを返却 |

**出力構造（3点）**:
1. 全体サマリー（2〜3文）
2. 増減の要因分析（前年比大幅変動項目）
3. 次年度の予測

---

## 今後の拡張予定

- 複数ファイル一括アップロード
- データベース連携（SQLite等）
- 高度なフィルター（年度範囲指定など）
- カスタムダッシュボード（ユーザー保存）
- AI分析: チャット形式での追加質問対応
