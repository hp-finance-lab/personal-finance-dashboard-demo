from pathlib import Path

from streamlit.testing.v1 import AppTest


APP = Path(__file__).resolve().parents[1] / "app.py"


def launch():
    app = AppTest.from_file(str(APP), default_timeout=20).run()
    assert not app.exception
    return app


def metric_values(app, label):
    return [metric.value for metric in app.metric if metric.label == label]


def edit_rows(app, key, edits=None, deleted=None):
    app.session_state[key] = {"edited_rows": edits or {}, "added_rows": [], "deleted_rows": deleted or []}
    return app.run()


def test_default_dashboard_renders_all_tabs_and_demo_values():
    app = launch()
    assert [tab.label for tab in app.tabs] == ["財務總覽", "家庭收支", "60 個月預測", "股票持倉"]
    assert metric_values(app, "每月收入") == ["HK$ 60,000", "HK$ 60,000"]
    assert metric_values(app, "每月支出") == ["HK$ 39,800", "HK$ 39,800"]
    assert metric_values(app, "未實現盈虧") == ["HK$ 5,700"]
    assert metric_values(app, "現金與股票合計") == ["HK$ 246,880"]
    assert len(app.get("download_button")) == 3
    assert len(app.dataframe) == 4  # two editors, forecast, portfolio analysis
    assert not app.error


def test_cash_assumption_updates_forecast_and_overview():
    app = launch()
    before = metric_values(app, "第 60 個月期末現金")
    app.number_input(key="initial_cash").set_value(240000.0).run()
    assert not app.exception
    assert metric_values(app, "起始現金儲備") == ["HK$ 240,000"]
    assert metric_values(app, "現金與股票合計") == ["HK$ 366,880"]
    assert metric_values(app, "第 60 個月期末現金") != before


def test_budget_editor_updates_totals_and_deficit_warning():
    app = launch()
    edit_rows(app, "budget_editor", edits={3: {"amount": 100000.0}})
    assert not app.exception
    assert metric_values(app, "每月支出") == ["HK$ 123,800", "HK$ 123,800"]
    assert metric_values(app, "每月結餘") == ["HK$ -63,800", "HK$ -63,800"]
    assert any("首次出現期末現金不足" in warning.value for warning in app.warning)


def test_empty_budget_and_empty_portfolio_are_rendered_safely():
    app = launch()
    edit_rows(app, "budget_editor", deleted=list(range(10)))
    edit_rows(app, "holdings_editor", deleted=list(range(4)))
    assert not app.exception
    assert metric_values(app, "儲蓄率") == ["不適用", "不適用"]
    assert metric_values(app, "組合回報率") == ["不適用"]
    assert metric_values(app, "持倉總市值") == ["HK$ 0"]
    assert any("目前沒有持倉" in message.value for message in app.info)


def test_exchange_rate_updates_both_stock_analysis_and_overview():
    app = launch()
    app.number_input(key="usd_hkd").set_value(8.0).run()
    assert not app.exception
    assert metric_values(app, "持倉總市值") == ["HK$ 128,600"]
    assert metric_values(app, "股票總市值") == ["HK$ 128,600"]
    assert metric_values(app, "未實現盈虧") == ["HK$ 5,800"]


def test_invalid_stock_row_shows_error_without_crashing_other_tabs():
    app = launch()
    edit_rows(app, "holdings_editor", edits={0: {"quantity": 0.0}})
    assert not app.exception
    assert any("股數必須大於零" in error.value for error in app.error)
    assert metric_values(app, "每月收入") == ["HK$ 60,000", "HK$ 60,000"]
    assert metric_values(app, "第 60 個月期末現金")


def test_invalid_budget_row_blocks_forecast_but_preserves_stock_tab():
    app = launch()
    edit_rows(app, "budget_editor", edits={0: {"category": ""}})
    assert not app.exception
    assert any("請填寫" in error.value for error in app.error)
    assert not metric_values(app, "第 60 個月期末現金")
    assert metric_values(app, "持倉總市值") == ["HK$ 126,880"]
