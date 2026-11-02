"""家庭財務實驗室：繁體中文 Streamlit 示範應用程式。"""

from datetime import date, datetime
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st

from demo_data import DEMO_BUDGET, DEMO_HOLDINGS
from finance import calculate_budget, calculate_portfolio, project_cash_flow


st.set_page_config(page_title="家庭財務實驗室", page_icon="🏡", layout="centered")
st.markdown("""
<style>
  .block-container { max-width: 980px; padding-top: 4.5rem; padding-bottom: 3rem; }
  .hero { padding: 1.6rem; border-radius: 20px; color: #f8fafc;
    background: linear-gradient(125deg, #102b46, #176b73); margin-bottom: 1rem; }
  .hero h1 { font-size: clamp(1.65rem, 5vw, 2.3rem); color: #fff; padding: .3rem 0; }
  .hero p { margin: 0; color: #d9eeed; line-height: 1.7; }
  .badge { font-size: .8rem; letter-spacing: .08em; color: #c4eee0; }
  [data-baseweb="tab-list"] { overflow-x: auto; gap: 1rem; }
  [data-baseweb="tab"] { white-space: nowrap; }
  @media (max-width: 640px) {
    .block-container { padding-left: 1rem; padding-right: 1rem; }
    .hero { padding: 1.2rem; }
    [data-testid="stMetricValue"] { font-size: 1.55rem; }
  }
</style>
<div class="hero">
  <div class="badge">虛構數據 · 港元本位 · 第一版</div>
  <h1>家庭財務實驗室</h1>
  <p>從今天的收支，看見未來五年的現金流。<br>一起掌握家庭預算與投資組合。</p>
</div>
""", unsafe_allow_html=True)
st.caption("所有收支、持倉、股價與匯率均為虛構示範，並非即時報價或投資建議。")


def money(amount: float) -> str:
    return f"HK$ {amount:,.0f}"


def percent(rate: float | None) -> str:
    return "不適用" if rate is None else f"{rate:.1%}"


def metrics(items: list[tuple[str, str]]) -> None:
    """每行最多兩張指標卡，小螢幕由 Streamlit 自動改為直排。"""
    for offset in range(0, len(items), 2):
        for column, (label, value) in zip(st.columns(2), items[offset:offset + 2]):
            column.metric(label, value, border=True)


def csv_bytes(frame: pd.DataFrame) -> bytes:
    return frame.to_csv(index=False).encode("utf-8-sig")


overview_tab, budget_tab, forecast_tab, stocks_tab = st.tabs(
    ["財務總覽", "家庭收支", "60 個月預測", "股票持倉"]
)

# 先讀取編輯器與假設，再於各分頁渲染結果；任何修改會在同一次重跑反映。
with budget_tab:
    st.subheader("每月家庭收支")
    budget_metrics = st.container()
    st.caption("金額為每月港元。可修改、新增或刪除項目；表格較寬時可左右滑動。")
    edited_budget = st.data_editor(
        pd.DataFrame(DEMO_BUDGET),
        key="budget_editor",
        num_rows="dynamic",
        hide_index=True,
        width="stretch",
        column_config={
            "kind": st.column_config.SelectboxColumn("類型", options=["收入", "支出"], required=True),
            "category": st.column_config.TextColumn("收支項目", required=True),
            "amount": st.column_config.NumberColumn("每月金額（港元）", min_value=0.0, max_value=1e12, step=100.0, format="%.2f", required=True),
        },
    )
    budget_details = st.container()

with forecast_tab:
    st.subheader("未來 60 個月現金流")
    with st.expander("調整預測假設", expanded=True):
        left, right = st.columns(2)
        initial_cash = left.number_input("起始現金（港元）", min_value=0.0, max_value=1e12, value=120000.0, step=10000.0, key="initial_cash")
        start_month = right.date_input("開始月份（按所選月份首日計算）", value=datetime.now(ZoneInfo("Asia/Hong_Kong")).date().replace(day=1), min_value=date(2000, 1, 1), max_value=date(2100, 12, 31), key="start_month")
        income_growth = left.number_input("收入年增長率（%）", min_value=-20.0, max_value=20.0, value=2.0, step=0.5, key="income_growth")
        expense_growth = right.number_input("支出年增長率（%）", min_value=-20.0, max_value=20.0, value=3.0, step=0.5, key="expense_growth")
        cash_return = left.number_input("現金年回報率（%）", min_value=0.0, max_value=20.0, value=1.0, step=0.1, key="cash_return")
        st.caption("收支取自「家庭收支」。首 12 個月維持基礎金額，其後每 12 個月調整一次。")
    forecast_results = st.container()

with stocks_tab:
    st.subheader("股票持倉及未實現盈虧")
    stock_metrics = st.container()
    usd_hkd = st.number_input("美元兌港元示範匯率（1 美元 = 港元）", min_value=0.01, max_value=100.0, value=7.8, step=0.01, key="usd_hkd")
    st.caption("每股成本及股價以該股票幣別輸入。支援小數股；清倉可刪除該列。所有價格均為手動示範值。")
    edited_holdings = st.data_editor(
        pd.DataFrame(DEMO_HOLDINGS),
        key="holdings_editor",
        num_rows="dynamic",
        hide_index=True,
        width="stretch",
        column_config={
            "symbol": st.column_config.TextColumn("股票代號", required=True),
            "name": st.column_config.TextColumn("示範名稱", required=True),
            "currency": st.column_config.SelectboxColumn("幣別", options=["HKD", "USD"], required=True),
            "quantity": st.column_config.NumberColumn("股數", min_value=0.0, max_value=1e9, step=1.0, required=True),
            "avg_cost": st.column_config.NumberColumn("每股成本", min_value=0.0, max_value=1e12, format="%.2f", required=True),
            "price": st.column_config.NumberColumn("示範股價", min_value=0.0, max_value=1e12, format="%.2f", required=True),
        },
    )
    stock_details = st.container()

budget = None
portfolio = None
try:
    budget = calculate_budget(edited_budget.to_dict("records"))
except ValueError as error:
    budget_details.error(str(error))

try:
    positions, portfolio = calculate_portfolio(edited_holdings.to_dict("records"), usd_hkd)
except ValueError as error:
    stock_details.error(str(error))

if budget is not None:
    with budget_metrics:
        metrics([("每月收入", money(budget.income)), ("每月支出", money(budget.expenses)),
                 ("每月結餘", money(budget.surplus)), ("儲蓄率", percent(budget.savings_rate))])
    with budget_details:
        if budget.surplus < 0:
            st.warning("每月支出超過收入，現金儲備將逐步減少。")
        expense_rows = edited_budget[edited_budget["kind"] == "支出"]
        if budget.expenses > 0:
            st.markdown("#### 支出分佈")
            expense_chart = expense_rows.groupby("category", as_index=False)["amount"].sum().rename(columns={"category": "項目", "amount": "每月支出（港元）"})
            st.bar_chart(expense_chart, x="項目", y="每月支出（港元）", horizontal=True, color="#168b88")
        else:
            st.info("目前沒有支出；儲備可支應月數不適用。")
        st.download_button("下載每月收支 CSV", csv_bytes(edited_budget.rename(columns={"kind": "類型", "category": "收支項目", "amount": "每月金額（港元）"})), file_name="家庭收支.csv", mime="text/csv")

    with forecast_results:
        projection = project_cash_flow(
            initial_cash=initial_cash, monthly_income=budget.income,
            monthly_expenses=budget.expenses, start_month=start_month,
            annual_income_growth=income_growth / 100,
            annual_expense_growth=expense_growth / 100,
            annual_cash_return=cash_return / 100,
        )
        frame = pd.DataFrame(projection).rename(columns={
            "month": "月份", "opening_cash": "期初現金", "income": "收入",
            "expenses": "支出", "net_flow": "收支結餘", "interest": "現金利息",
            "closing_cash": "期末現金",
        })
        metrics([("第 60 個月期末現金", money(projection[-1]["closing_cash"])),
                 ("60 個月最低期末現金", money(min(p["closing_cash"] for p in projection)))])
        first_deficit = next((p for p in projection if p["closing_cash"] < 0), None)
        if first_deficit:
            st.warning(f"預計於 {first_deficit['month']:%Y-%m} 首次出現期末現金不足。負數代表資金缺口，未計借貸利息。")
        else:
            st.success("此情境下，60 個月內未出現期末現金不足。")
        chart_frame = frame[["月份", "期末現金"]].copy()
        chart_frame["月份"] = pd.to_datetime(chart_frame["月份"])
        chart_frame["六個月基本支出儲備"] = budget.expenses * 6
        st.line_chart(chart_frame, x="月份", y=["期末現金", "六個月基本支出儲備"], color=["#168b88", "#d98b39"], y_label="港元")
        with st.expander("計算方式與限制"):
            st.markdown("""
            - 月回報率 = `(1 + 現金年回報率)^(1/12) − 1`。
            - 月利息 = `max(期初現金, 0) × 月回報率`，收支在月底入賬。
            - 期末現金 = `期初現金 + 收入 − 支出 + 月利息`。
            - 第 13、25、37、49 個月按各自年增長率調整收支。
            - 橙線是目前每月支出的六倍，僅作固定儲備參考。
            - 股票不會自動買賣，市值、股息及股價變動不會計入現金預測。
            - 未模擬一次性大額支出、額外稅項、借貸、手續費或不確定性。
            """)
        export_frame = frame.copy()
        export_frame["月份"] = export_frame["月份"].map(lambda value: value.strftime("%Y-%m"))
        with st.expander("查看 60 個月明細"):
            st.dataframe(export_frame.style.format({column: "{:,.2f}" for column in export_frame.columns if column != "月份"}), hide_index=True, width="stretch")
        st.download_button("下載 60 個月預測 CSV", csv_bytes(export_frame), file_name="60個月現金流預測.csv", mime="text/csv")
else:
    forecast_results.info("請先修正「家庭收支」的資料，才能產生預測。")

if portfolio is not None:
    with stock_metrics:
        metrics([("持倉總市值", money(portfolio.market_value)), ("持倉總成本", money(portfolio.cost)),
                 ("未實現盈虧", money(portfolio.profit)), ("組合回報率", percent(portfolio.return_rate))])
    with stock_details:
        st.caption("組合回報率＝總未實現盈虧 ÷ 總成本。成本與市值採用同一示範匯率，未計匯兌損益、股息、稅項及交易費用。零成本持倉的回報率不適用。")
        if positions:
            position_frame = pd.DataFrame(positions)
            chart = position_frame.assign(股票=lambda df: df["symbol"] + " · " + df["name"])
            st.markdown("#### 持倉市值（港元）")
            st.bar_chart(chart.rename(columns={"value_hkd": "市值（港元）"}), x="股票", y="市值（港元）", horizontal=True, color="#168b88")
            st.markdown("#### 各股未實現盈虧（港元）")
            st.bar_chart(chart.rename(columns={"profit_hkd": "未實現盈虧（港元）"}), x="股票", y="未實現盈虧（港元）", horizontal=True, color="#5675ba")
            details = position_frame.rename(columns={
                "symbol": "股票代號", "name": "示範名稱", "currency": "幣別", "quantity": "股數",
                "cost_hkd": "成本（港元）", "value_hkd": "市值（港元）",
                "profit_hkd": "盈虧（港元）", "return_rate": "回報率",
            })
            st.dataframe(details.style.format({"股數": "{:,.2f}", "成本（港元）": "{:,.2f}", "市值（港元）": "{:,.2f}", "盈虧（港元）": "{:,.2f}", "回報率": "{:.1%}"}, na_rep="不適用"), hide_index=True, width="stretch")
            st.download_button("下載持倉分析 CSV", csv_bytes(details), file_name="股票持倉分析.csv", mime="text/csv")
        else:
            st.info("目前沒有持倉。可在上方新增股票，查看成本、市值及盈虧。")

with overview_tab:
    st.subheader("家庭財務一覽")
    if budget is not None:
        metrics([("每月收入", money(budget.income)), ("每月支出", money(budget.expenses)),
                 ("每月結餘", money(budget.surplus)), ("儲蓄率", percent(budget.savings_rate))])
        reserve_months = initial_cash / budget.expenses if budget.expenses else None
        metrics([("起始現金儲備", money(initial_cash)),
                 ("現金可支應基本支出", f"{reserve_months:.1f} 個月" if reserve_months is not None else "不適用")])
        if budget.surplus < 0:
            st.warning("家庭收支錄得赤字，可先檢視「家庭收支」，再比較不同預測情境。")
        elif reserve_months is not None and reserve_months < 6:
            st.info("目前現金儲備少於六個月基本支出，可在「60 個月預測」檢視累積速度。")
        else:
            st.success("每月收支有結餘或持平，可調整假設，探索未來現金變化。")
    else:
        st.error("家庭收支資料未完整，請到「家庭收支」修正。")
    if portfolio is not None:
        metrics([("股票總市值", money(portfolio.market_value)), ("股票未實現盈虧", money(portfolio.profit))])
        st.metric("現金與股票合計", money(initial_cash + portfolio.market_value), border=True)
        st.caption("只計入起始現金與目前示範股票市值；不等同完整淨資產，未扣除任何負債。")
    else:
        st.error("股票資料未完整，請到「股票持倉」修正。")
    st.markdown("**如何開始**\n\n1. 到「家庭收支」編輯每月收入與支出。\n2. 在「60 個月預測」調整起始現金與增長假設。\n3. 到「股票持倉」修改持股及示範價格，觀察組合盈虧。")

st.divider()
st.caption("示範模式：修改僅保留於目前瀏覽器連線；重新載入或結束連線可能重設。需要保留結果時請下載 CSV。應用程式不連接銀行、券商或行情 API。")
