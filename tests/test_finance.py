from datetime import date

import pytest

from demo_data import DEMO_BUDGET, DEMO_HOLDINGS
from finance import calculate_budget, calculate_portfolio, project_cash_flow


def forecast(**overrides):
    values = dict(initial_cash=1000, monthly_income=200, monthly_expenses=150,
                  start_month=date(2026, 11, 1), annual_income_growth=0,
                  annual_expense_growth=0, annual_cash_return=0)
    return project_cash_flow(**(values | overrides))


def holding(**overrides):
    return dict(symbol="DEMO", name="示範股票", currency="HKD", quantity=10,
                avg_cost=100, price=120) | overrides


def test_demo_budget_totals():
    result = calculate_budget(DEMO_BUDGET)
    assert result.income == 60000
    assert result.expenses == 39800
    assert result.surplus == 20200
    assert result.savings_rate == pytest.approx(20200 / 60000)


def test_zero_income_and_deficit_do_not_divide_by_zero():
    result = calculate_budget([dict(kind="支出", category="住屋", amount=500)])
    assert result.surplus == -500
    assert result.savings_rate is None
    assert calculate_budget([]).surplus == 0


@pytest.mark.parametrize("amount", [-1, float("nan"), float("inf"), "100", True, None])
def test_invalid_budget_amount_is_rejected(amount):
    with pytest.raises(ValueError, match="金額"):
        calculate_budget([dict(kind="支出", category="住屋", amount=amount)])


@pytest.mark.parametrize("row", [dict(kind="其他", category="住屋", amount=1),
                                  dict(kind="收入", category=" ", amount=1)])
def test_incomplete_or_unknown_budget_category_is_rejected(row):
    with pytest.raises(ValueError):
        calculate_budget([row])


def test_blank_editor_rows_are_ignored():
    assert calculate_budget([dict(kind=None, category="", amount=float("nan"))]).income == 0
    positions, summary = calculate_portfolio([dict(symbol=None, quantity=None)])
    assert positions == []
    assert summary.market_value == 0


def test_sixty_month_projection_and_calendar_rollover():
    rows = forecast()
    assert len(rows) == 60
    assert rows[0]["month"] == date(2026, 11, 1)
    assert rows[2]["month"] == date(2027, 1, 1)
    assert rows[-1]["month"] == date(2031, 10, 1)
    assert rows[0]["closing_cash"] == 1050
    assert rows[-1]["closing_cash"] == 4000


def test_growth_starts_in_month_thirteen_and_compounds_annually():
    rows = forecast(annual_income_growth=0.1, annual_expense_growth=0.2)
    assert rows[11]["income"] == 200
    assert rows[11]["expenses"] == 150
    assert rows[12]["income"] == pytest.approx(220)
    assert rows[12]["expenses"] == pytest.approx(180)
    assert rows[24]["income"] == pytest.approx(242)
    assert rows[24]["expenses"] == pytest.approx(216)


def test_effective_annual_return_is_converted_to_monthly_compounding():
    rows = forecast(months=12, monthly_income=0, monthly_expenses=0, annual_cash_return=0.12)
    assert rows[0]["interest"] == pytest.approx(1000 * (1.12 ** (1 / 12) - 1))
    assert rows[-1]["closing_cash"] == pytest.approx(1120)


def test_interest_precedes_month_end_contribution():
    rows = forecast(months=1, initial_cash=0, annual_cash_return=0.12)
    assert rows[0]["interest"] == 0
    assert rows[0]["closing_cash"] == 50


def test_cash_deficit_is_visible_without_invented_debt_interest():
    rows = forecast(initial_cash=50, monthly_income=0, monthly_expenses=100,
                    annual_cash_return=0.12, months=2)
    assert rows[0]["closing_cash"] < 0
    assert rows[1]["opening_cash"] == rows[0]["closing_cash"]
    assert rows[1]["interest"] == 0
    assert rows[1]["closing_cash"] == pytest.approx(rows[0]["closing_cash"] - 100)


@pytest.mark.parametrize("override", [dict(initial_cash=-1), dict(months=0), dict(months=1.5),
                                      dict(months=True), dict(annual_income_growth=-1.01),
                                      dict(annual_cash_return=-0.1), dict(monthly_income=float("inf"))])
def test_invalid_projection_inputs_are_rejected(override):
    with pytest.raises(ValueError):
        forecast(**override)


def test_portfolio_handles_profit_loss_and_currency_conversion():
    rows, result = calculate_portfolio([
        holding(), holding(symbol="USD", currency="USD", quantity=2, avg_cost=50, price=40)
    ], usd_hkd=8)
    assert rows[0]["profit_hkd"] == 200
    assert rows[1]["cost_hkd"] == 800
    assert rows[1]["value_hkd"] == 640
    assert rows[1]["profit_hkd"] == -160
    assert result.cost == 1800
    assert result.market_value == 1840
    assert result.profit == 40
    assert result.return_rate == pytest.approx(40 / 1800)


def test_portfolio_return_is_cost_weighted_not_average_of_percentages():
    _, result = calculate_portfolio([
        holding(quantity=1, avg_cost=100, price=200),
        holding(quantity=1, avg_cost=900, price=810),
    ])
    assert result.return_rate == pytest.approx(0.01)


def test_empty_and_zero_cost_holdings_have_no_percentage():
    rows, result = calculate_portfolio([])
    assert rows == []
    assert result.market_value == result.profit == 0
    assert result.return_rate is None
    rows, result = calculate_portfolio([holding(avg_cost=0)])
    assert rows[0]["return_rate"] is None
    assert result.profit == 1200
    assert result.return_rate is None


def test_fractional_shares_and_total_loss_are_supported():
    rows, result = calculate_portfolio([holding(quantity=0.5, price=0)])
    assert result.cost == 50
    assert result.market_value == 0
    assert rows[0]["return_rate"] == -1


def test_demo_portfolio_totals():
    _, result = calculate_portfolio(DEMO_HOLDINGS)
    assert result.cost == 121180
    assert result.market_value == 126880
    assert result.profit == 5700


@pytest.mark.parametrize("override", [dict(quantity=-1), dict(quantity=0), dict(price=float("inf")),
                                      dict(avg_cost=-1), dict(currency="EUR"), dict(symbol=""),
                                      dict(name=None)])
def test_invalid_holdings_are_rejected(override):
    with pytest.raises(ValueError):
        calculate_portfolio([holding(**override)])


@pytest.mark.parametrize("rate", [0, -1, float("nan"), float("inf")])
def test_invalid_exchange_rates_are_rejected(rate):
    with pytest.raises(ValueError):
        calculate_portfolio([holding()], usd_hkd=rate)
