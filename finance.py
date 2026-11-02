"""可獨立測試的財務計算；金額只在顯示時四捨五入。"""

from dataclasses import dataclass
from datetime import date
from math import isfinite, isnan
from numbers import Real
from typing import Iterable, Mapping


@dataclass(frozen=True)
class BudgetSummary:
    income: float
    expenses: float

    @property
    def surplus(self) -> float:
        return self.income - self.expenses

    @property
    def savings_rate(self) -> float | None:
        return self.surplus / self.income if self.income else None


@dataclass(frozen=True)
class PortfolioSummary:
    cost: float
    market_value: float

    @property
    def profit(self) -> float:
        return self.market_value - self.cost

    @property
    def return_rate(self) -> float | None:
        return self.profit / self.cost if self.cost else None


def _number(value: object, label: str, minimum: float = 0) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{label}必須是數字。")
    result = float(value)
    if not isfinite(result) or result < minimum:
        raise ValueError(f"{label}必須是有限數字，且不少於 {minimum:g}。")
    return result


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"請填寫{label}。")
    return value.strip()


def _empty_row(row: Mapping) -> bool:
    """忽略資料編輯器尚未填入任何內容的新列。"""
    return all(
        value is None
        or (isinstance(value, str) and not value.strip())
        or (isinstance(value, Real) and isnan(value))
        for value in row.values()
    )


def calculate_budget(rows: Iterable[Mapping]) -> BudgetSummary:
    income = expenses = 0.0
    for index, row in enumerate(rows, 1):
        if _empty_row(row):
            continue
        _text(row.get("category"), f"第 {index} 列的收支項目")
        amount = _number(row.get("amount"), f"第 {index} 列金額")
        kind = row.get("kind")
        if kind == "收入":
            income += amount
        elif kind == "支出":
            expenses += amount
        else:
            raise ValueError(f"第 {index} 列類型必須為收入或支出。")
    if not isfinite(income + expenses):
        raise ValueError("收支總額過大，請調低金額。")
    return BudgetSummary(income=income, expenses=expenses)


def project_cash_flow(
    *,
    initial_cash: float,
    monthly_income: float,
    monthly_expenses: float,
    start_month: date,
    months: int = 60,
    annual_income_growth: float = 0.02,
    annual_expense_growth: float = 0.03,
    annual_cash_return: float = 0.01,
) -> list[dict]:
    """首月沿用基礎收支，第 13、25…月調整；利息以正數期初現金計算。"""
    cash = _number(initial_cash, "起始現金")
    income = _number(monthly_income, "每月收入")
    expenses = _number(monthly_expenses, "每月支出")
    income_growth = _number(annual_income_growth, "收入年增長率", -1)
    expense_growth = _number(annual_expense_growth, "支出年增長率", -1)
    cash_return = _number(annual_cash_return, "現金年回報率")
    if isinstance(months, bool) or not isinstance(months, int) or not 1 <= months <= 600:
        raise ValueError("預測月數必須為 1 至 600 的整數。")
    if not isinstance(start_month, date):
        raise ValueError("請提供有效的開始月份。")
    monthly_return = (1 + cash_return) ** (1 / 12) - 1
    result = []
    for offset in range(months):
        absolute_month = start_month.year * 12 + start_month.month - 1 + offset
        year, month_index = divmod(absolute_month, 12)
        period_income = income * (1 + income_growth) ** (offset // 12)
        period_expenses = expenses * (1 + expense_growth) ** (offset // 12)
        interest = max(cash, 0) * monthly_return
        net_flow = period_income - period_expenses
        closing_cash = cash + net_flow + interest
        if not all(isfinite(v) for v in (period_income, period_expenses, closing_cash)):
            raise ValueError("預測金額過大，請調低金額或增長率。")
        result.append({
            "month": date(year, month_index + 1, 1),
            "opening_cash": cash,
            "income": period_income,
            "expenses": period_expenses,
            "net_flow": net_flow,
            "interest": interest,
            "closing_cash": closing_cash,
        })
        cash = closing_cash
    return result


def calculate_portfolio(
    rows: Iterable[Mapping], usd_hkd: float = 7.8
) -> tuple[list[dict], PortfolioSummary]:
    fx = _number(usd_hkd, "美元兌港元匯率")
    if fx == 0:
        raise ValueError("美元兌港元匯率必須大於零。")
    positions = []
    for index, row in enumerate(rows, 1):
        if _empty_row(row):
            continue
        symbol = _text(row.get("symbol"), f"第 {index} 列股票代號")
        name = _text(row.get("name"), f"第 {index} 列股票名稱")
        currency = row.get("currency")
        if currency not in ("HKD", "USD"):
            raise ValueError(f"第 {index} 列幣別必須為 HKD 或 USD。")
        quantity = _number(row.get("quantity"), f"第 {index} 列股數")
        if quantity == 0:
            raise ValueError(f"第 {index} 列股數必須大於零；清倉請刪除該列。")
        avg_cost = _number(row.get("avg_cost"), f"第 {index} 列每股成本")
        price = _number(row.get("price"), f"第 {index} 列示範股價")
        exchange_rate = fx if currency == "USD" else 1
        cost = quantity * avg_cost * exchange_rate
        value = quantity * price * exchange_rate
        if not isfinite(cost + value):
            raise ValueError("持倉金額過大，請調低股數或價格。")
        positions.append({
            "symbol": symbol,
            "name": name,
            "currency": currency,
            "quantity": quantity,
            "cost_hkd": cost,
            "value_hkd": value,
            "profit_hkd": value - cost,
            "return_rate": (value - cost) / cost if cost else None,
        })
    summary = PortfolioSummary(
        cost=sum(p["cost_hkd"] for p in positions),
        market_value=sum(p["value_hkd"] for p in positions),
    )
    if not isfinite(summary.cost + summary.market_value):
        raise ValueError("持倉總額過大，請調低金額。")
    return positions, summary
