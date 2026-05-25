from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


DATA_DIR = Path(__file__).parent / "data"
NAVY = "#123247"
TEAL = "#008C95"
GREEN = "#258761"
CORAL = "#CB5650"
AMBER = "#C98C25"
LIGHT_BLUE = "#94B6C2"
PALE_TEAL = "#D9EEEA"
DONUT_COLORS = [TEAL, NAVY, "#337C9C", AMBER, GREEN]


st.set_page_config(
    page_title="医療用医薬品 売上分析ダッシュボード",
    layout="wide",
)


@st.cache_data
def load_data() -> pd.DataFrame:
    fact = pd.read_csv(DATA_DIR / "fact_sales.csv")
    dates = pd.read_csv(DATA_DIR / "dim_date.csv", parse_dates=["Date"])
    products = pd.read_csv(DATA_DIR / "dim_product.csv")
    regions = pd.read_csv(DATA_DIR / "dim_region.csv")
    month_dates = dates.loc[dates["IsMonthStart"].astype(str).str.lower() == "true"]
    sales = fact.merge(month_dates, left_on="SalesDateKey", right_on="DateKey", how="left")
    sales = sales.merge(products, on="ProductKey", how="left")
    return sales.merge(regions, on="RegionKey", how="left")


def yen_billion(value: float) -> str:
    return f"{value / 100_000_000:.1f} 億円"


def percent_change(current: float, prior: float) -> float:
    return (current / prior - 1) * 100 if prior else 0.0


def kpi_card(label: str, value: str, detail: str, tone: str, accent: str) -> None:
    st.markdown(
        f"""
        <div class="kpi-card {tone}" style="--accent:{accent};">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value}</div>
            <div class="kpi-detail">{detail}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def chart_layout(fig: go.Figure, height: int = 300) -> go.Figure:
    fig.update_layout(
        height=height,
        margin=dict(l=18, r=18, t=51, b=18),
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(family="Noto Sans JP, sans-serif", color=NAVY, size=12),
        title_font=dict(size=15, color=NAVY, family="Noto Sans JP, sans-serif"),
        legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="right", x=1),
        hoverlabel=dict(bgcolor="white", bordercolor="#D9E6E8"),
    )
    fig.update_xaxes(showgrid=False, linecolor="#DDE6E8")
    fig.update_yaxes(gridcolor="#E9EFF1", zeroline=False)
    return fig


st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;500;700&family=Shippori+Mincho:wght@500;600&display=swap');
    [data-testid="stHeader"] {
        background: transparent;
        height: 0;
    }
    [data-testid="stHeader"] > div {
        display: none;
    }
    .stApp {
        background:
            radial-gradient(circle at 92% 2%, rgba(0,140,149,.11), transparent 26rem),
            linear-gradient(180deg, #F2F8F7 0%, #F6F8F8 36%, #F3F6F6 100%);
    }
    .block-container { padding: .2rem 2.25rem 1.4rem; max-width: 1500px; }
    section[data-testid="stSidebar"] div:first-child {
        top: 0;
        height: 100vh;
    }
    .hero {
        position: relative;
        overflow: hidden;
        min-height: 111px;
        padding: 1.12rem 1.55rem 1rem;
        margin-bottom: .85rem;
        border-radius: 18px;
        background: linear-gradient(108deg, #102F43 0%, #174B59 60%, #087E84 100%);
        box-shadow: 0 13px 28px rgba(18,50,71,.13);
    }
    .hero:after {
        content: "";
        position: absolute;
        right: -58px;
        top: -90px;
        height: 240px;
        width: 240px;
        border: 1px solid rgba(255,255,255,.18);
        border-radius: 50%;
        box-shadow: 0 0 0 38px rgba(255,255,255,.045), 0 0 0 76px rgba(255,255,255,.035);
    }
    .hero-eyebrow {
        color: #94D8D2;
        letter-spacing: .19em;
        font-size: .68rem;
        font-weight: 700;
        margin-bottom: .33rem;
    }
    .hero-title {
        position: relative;
        z-index: 1;
        color: white;
        font-family: "Shippori Mincho", serif;
        font-size: 1.72rem;
        letter-spacing: .04em;
        margin-bottom: .32rem;
    }
    .hero-subtitle { position: relative; z-index: 1; color: #CBDFE1; font-size: .85rem; }
    .filter-label {
        color: #67808A;
        font-size: .68rem;
        font-weight: 700;
        letter-spacing: .17em;
        margin: .4rem 0 -.5rem .1rem;
    }
    [data-testid="stHorizontalBlock"]:has(.kpi-card) { gap: .95rem; }
    .kpi-card {
        --accent: #008C95;
        position: relative;
        background: white;
        border: 1px solid #E0EAEA;
        border-radius: 15px;
        padding: .82rem 1rem .76rem 1.12rem;
        margin: .4rem 0 .6rem;
        box-shadow: 0 3px 15px rgba(18,50,71,.045);
    }
    .kpi-card:before {
        content: "";
        position: absolute;
        height: calc(100% - 1.5rem);
        width: 4px;
        left: 0;
        top: .75rem;
        border-radius: 4px;
        background: var(--accent);
    }
    .kpi-label { color: #718891; letter-spacing: .08em; font-size: .71rem; font-weight: 700; }
    .kpi-value { color: #123247; font-size: 1.64rem; font-weight: 700; margin: .2rem 0 .12rem; }
    .kpi-detail { color: #607883; font-size: .78rem; font-weight: 500; }
    .positive .kpi-detail { color: #258761; }
    .warning .kpi-detail { color: #C07728; }
    .negative .kpi-detail { color: #CB5650; }
    [data-testid="stSelectbox"] label, [data-testid="stMultiSelect"] label {
        color: #526B75;
        font-weight: 500;
        font-size: .82rem;
    }
    [data-baseweb="select"] > div {
        background: rgba(255,255,255,.88);
        border-color: #DCE7E8;
        border-radius: 10px;
    }
    div[data-testid="stPlotlyChart"] {
        background: white;
        border: 1px solid #E0EAEA;
        border-radius: 15px;
        padding: .05rem .18rem;
        box-shadow: 0 3px 15px rgba(18,50,71,.042);
    }
    [data-testid="stCaptionContainer"] { color: #789098; padding-top: .2rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

if not DATA_DIR.exists():
    st.error("データがありません。先に `python generate_sales_data.py` を実行してください。")
    st.stop()

sales = load_data()
fiscal_years = sorted(sales["FiscalYear"].dropna().astype(int).unique(), reverse=True)

st.markdown(
    """
    <div class="hero">
        <div class="hero-eyebrow">MEDNOVA PHARMA &nbsp; / &nbsp; COMMERCIAL INTELLIGENCE</div>
        <div class="hero-title">医療用医薬品 売上分析ダッシュボード</div>
        <div class="hero-subtitle">Monthly Performance Overview | 実績・計画・前年比を製品 / 地域 / 治療領域で分析</div>
    </div>
    <div class="filter-label">ANALYSIS FILTERS</div>
    """,
    unsafe_allow_html=True,
)

filter_cols = st.columns([1.0, 1.2, 1.3, 1.1])
with filter_cols[0]:
    selected_fy = st.selectbox("年度（4月始まり）", fiscal_years, format_func=lambda value: f"FY{value}")
with filter_cols[1]:
    area_options = sorted(sales["TherapeuticArea"].unique())
    selected_areas = st.multiselect("治療領域", area_options, placeholder="すべて")
with filter_cols[2]:
    product_source = sales[sales["TherapeuticArea"].isin(selected_areas)] if selected_areas else sales
    products_available = product_source["ProductName"].unique()
    selected_products = st.multiselect("製品", sorted(products_available), placeholder="すべて")
with filter_cols[3]:
    selected_regions = st.multiselect("地域", sales["RegionName"].unique(), placeholder="すべて")


def apply_common_filters(dataframe: pd.DataFrame) -> pd.DataFrame:
    result = dataframe
    if selected_areas:
        result = result[result["TherapeuticArea"].isin(selected_areas)]
    if selected_products:
        result = result[result["ProductName"].isin(selected_products)]
    if selected_regions:
        result = result[result["RegionName"].isin(selected_regions)]
    return result


filtered = apply_common_filters(sales)
current = filtered[filtered["FiscalYear"] == selected_fy].copy()
prior = filtered[filtered["FiscalYear"] == selected_fy - 1].copy()
actual = current["SalesAmountJPY"].sum()
budget = current["BudgetAmountJPY"].sum()
prior_actual = prior["SalesAmountJPY"].sum()
attainment = actual / budget * 100 if budget else 0
yoy = percent_change(actual, prior_actual)
units = current["UnitQuantity"].sum()

kpi_cols = st.columns(4)
with kpi_cols[0]:
    kpi_card("NET SALES", yen_billion(actual), f"{yoy:+.1f}% 前年比", "positive" if yoy >= 0 else "negative", TEAL)
with kpi_cols[1]:
    kpi_card(
        "PLAN ATTAINMENT",
        f"{attainment:.1f}%",
        f"{attainment - 100:+.1f} pt vs plan",
        "positive" if attainment >= 100 else "warning",
        GREEN if attainment >= 100 else AMBER,
    )
with kpi_cols[2]:
    kpi_card(
        "YEAR ON YEAR",
        f"{yoy:+.1f}%",
        f"{yen_billion(abs(actual - prior_actual))} {'増加' if yoy >= 0 else '減少'}",
        "positive" if yoy >= 0 else "negative",
        GREEN if yoy >= 0 else CORAL,
    )
with kpi_cols[3]:
    kpi_card("SALES VOLUME", f"{units:,} 箱", "年度累計 出荷数量", "", "#337C9C")

monthly = (
    current.groupby(["FiscalMonthNumber", "MonthNameJP"], as_index=False)[["SalesAmountJPY", "BudgetAmountJPY"]]
    .sum()
    .sort_values("FiscalMonthNumber")
)
prior_monthly = (
    prior.groupby("FiscalMonthNumber", as_index=False)["SalesAmountJPY"]
    .sum()
    .rename(columns={"SalesAmountJPY": "PriorSalesAmountJPY"})
)
monthly = monthly.merge(prior_monthly, on="FiscalMonthNumber", how="left")
monthly["Actual"] = monthly["SalesAmountJPY"] / 100_000_000
monthly["Budget"] = monthly["BudgetAmountJPY"] / 100_000_000
monthly["Prior"] = monthly["PriorSalesAmountJPY"] / 100_000_000

top_left, top_right = st.columns([1.65, 1])
with top_left:
    trend = go.Figure()
    trend.add_bar(x=monthly["MonthNameJP"], y=monthly["Actual"], name="実績", marker_color=TEAL)
    trend.add_trace(
        go.Scatter(x=monthly["MonthNameJP"], y=monthly["Budget"], name="計画", line=dict(color=AMBER, width=2.3))
    )
    trend.add_trace(
        go.Scatter(x=monthly["MonthNameJP"], y=monthly["Prior"], name="前年", line=dict(color=LIGHT_BLUE, width=2))
    )
    trend.update_layout(title="月次売上 実績 vs 計画 vs 前年", yaxis_title="売上（億円）", barmode="group")
    st.plotly_chart(chart_layout(trend, 315), use_container_width=True)

with top_right:
    product_sales = current.groupby("ProductName", as_index=False)["SalesAmountJPY"].sum()
    prior_product = prior.groupby("ProductName", as_index=False)["SalesAmountJPY"].sum()
    product_sales = product_sales.merge(prior_product, on="ProductName", how="left", suffixes=("", "_Prior"))
    product_sales["前年比"] = (
        product_sales["SalesAmountJPY"] / product_sales["SalesAmountJPY_Prior"].replace(0, pd.NA) - 1
    ) * 100
    product_sales["売上（億円）"] = product_sales["SalesAmountJPY"] / 100_000_000
    product_sales = product_sales.sort_values("売上（億円）", ascending=True)
    product_chart = px.bar(
        product_sales,
        x="売上（億円）",
        y="ProductName",
        orientation="h",
        title="製品別売上ランキング",
        color="前年比",
        color_continuous_scale=[CORAL, "#EBEFF0", GREEN],
        color_continuous_midpoint=0,
    )
    product_chart.update_layout(coloraxis_colorbar=dict(title="前年比%"))
    st.plotly_chart(chart_layout(product_chart, 315), use_container_width=True)

bottom_left, bottom_right = st.columns([1, 1])
with bottom_left:
    region = current.groupby(["RegionName", "RegionSortOrder"], as_index=False)[
        ["SalesAmountJPY", "BudgetAmountJPY"]
    ].sum()
    region["達成率"] = region["SalesAmountJPY"] / region["BudgetAmountJPY"] * 100
    region = region.sort_values("達成率")
    region_chart = px.bar(
        region,
        x="達成率",
        y="RegionName",
        orientation="h",
        title="地域別 計画達成率",
        color="達成率",
        color_continuous_scale=[CORAL, "#EBDCB8", GREEN],
        color_continuous_midpoint=100,
    )
    region_chart.add_vline(x=100, line_dash="dot", line_color=NAVY)
    region_chart.update_layout(coloraxis_showscale=False, xaxis_ticksuffix="%")
    st.plotly_chart(chart_layout(region_chart, 290), use_container_width=True)

with bottom_right:
    area = current.groupby("TherapeuticArea", as_index=False)["SalesAmountJPY"].sum()
    area["売上（億円）"] = area["SalesAmountJPY"] / 100_000_000
    area = area.sort_values("売上（億円）", ascending=False)
    area_chart = go.Figure(
        go.Pie(
            labels=area["TherapeuticArea"],
            values=area["売上（億円）"],
            hole=0.65,
            domain=dict(x=[0.0, 0.70], y=[0.0, 1.0]),
            sort=False,
            direction="clockwise",
            marker=dict(colors=DONUT_COLORS, line=dict(color="white", width=3)),
            textinfo="percent",
            textfont=dict(size=12, color="white"),
            hovertemplate="<b>%{label}</b><br>売上: %{value:.1f} 億円<br>構成比: %{percent}<extra></extra>",
        )
    )
    area_chart.update_layout(
        title="治療領域別 売上構成",
        showlegend=True,
        annotations=[
            dict(
                text=f"<span style='font-size:12px;color:#69828B'>TOTAL SALES</span><br>"
                f"<b>{actual / 100_000_000:.1f}</b><span style='font-size:12px'> 億円</span>",
                x=0.35,
                y=0.5,
                font=dict(size=22, color=NAVY, family="Noto Sans JP, sans-serif"),
                showarrow=False,
            )
        ],
    )
    area_chart = chart_layout(area_chart, 290)
    area_chart.update_layout(legend=dict(orientation="v", yanchor="middle", y=0.48, xanchor="left", x=1.01))
    st.plotly_chart(area_chart, use_container_width=True)

st.caption("※ 本画面は架空の製品・売上データを使用したPower BI実装検討用モックアップです。")
