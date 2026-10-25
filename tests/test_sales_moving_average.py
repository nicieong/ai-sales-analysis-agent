import pandas as pd
import pytest

from sales_analysis import (
    get_daily_sales_trend,
    get_product_daily_sales_trend,
)


def test_daily_sales_trend_has_seven_day_moving_average():
    dates = pd.date_range("2026-07-21", periods=10, freq="D")

    df = pd.DataFrame({
        "sales_date": dates,
        "sales_qty": [1] * 10,
        "sales_amount": [10, 20, 30, 40, 50, 60, 70, 80, 90, 100],
    })

    result = get_daily_sales_trend(df)

    assert "sales_7day_ma" in result.columns

    # The first six days do not have a complete seven-day window.
    assert result["sales_7day_ma"].iloc[:6].isna().all()

    # First complete window: 10, 20, 30, 40, 50, 60, 70.
    assert result["sales_7day_ma"].iloc[6] == pytest.approx(40.0)

    # Next window: 20, 30, 40, 50, 60, 70, 80.
    assert result["sales_7day_ma"].iloc[7] == pytest.approx(50.0)


def test_daily_sales_trend_moving_average_uses_calendar_days():
    dates = pd.date_range("2026-07-21", periods=10, freq="D")

    df = pd.DataFrame({
        "sales_date": dates,
        "sales_qty": [1] * 10,
        "sales_amount": [10] * 10,
    })

    # The selected period starts on day 8.
    # The moving average should still use the preceding six days.
    result = get_daily_sales_trend(
        df,
        start_date="2026-07-28",
        end_date="2026-07-30",
    )

    assert len(result) == 3
    assert result["sales_date"].min() == pd.Timestamp("2026-07-28")
    assert result["sales_date"].max() == pd.Timestamp("2026-07-30")
    assert result["sales_7day_ma"].tolist() == pytest.approx([10, 10, 10])


def test_product_daily_sales_trend_calculates_moving_average():
    dates = pd.date_range("2026-07-21", periods=8, freq="D")

    df = pd.DataFrame({
        "sales_date": list(dates) * 2,
        "product_id": ["P001"] * 8 + ["P002"] * 8,
        "sales_qty": [1] * 16,
        "sales_amount": [
            10, 20, 30, 40, 50, 60, 70, 80,
            100, 100, 100, 100, 100, 100, 100, 100,
        ],
    })

    result = get_product_daily_sales_trend(
        df,
        product_id="P001",
    )

    assert len(result) == 8
    assert result["sales_7day_ma"].iloc[:6].isna().all()
    assert result["sales_7day_ma"].iloc[6] == pytest.approx(40.0)
    assert result["sales_7day_ma"].iloc[7] == pytest.approx(50.0)


def test_product_daily_sales_trend_does_not_mix_products():
    dates = pd.date_range("2026-07-21", periods=7, freq="D")

    df = pd.DataFrame({
        "sales_date": list(dates) * 2,
        "product_id": ["P001"] * 7 + ["P002"] * 7,
        "sales_qty": [1] * 14,
        "sales_amount": [10] * 7 + [100] * 7,
    })

    result = get_product_daily_sales_trend(
        df,
        product_id="P001",
    )

    assert result["sales_amount"].tolist() == [10] * 7
    assert result["sales_7day_ma"].iloc[6] == pytest.approx(10.0)