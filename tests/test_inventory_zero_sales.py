from pathlib import Path

import pandas as pd

from inventory_analysis import analyze_inventory


def test_inventory_product_with_zero_sales():
    project_dir = Path(__file__).resolve().parent.parent
    sales_file = project_dir / "data" / "sales.csv"
    test_sales_file = project_dir / "data" / "sales_zero_test.csv"

    df = pd.read_csv(sales_file)

    # Move P010's sales records outside the 90-day analysis window.
    df.loc[df["product_id"] == "P010", "sales_date"] = "2026-07-20"
    df.to_csv(test_sales_file, index=False)

    try:
        result = analyze_inventory(sales_file=test_sales_file)

        p010_rows = result.loc[result["product_id"] == "P010"]

        # P010 must remain in the inventory report.
        assert len(p010_rows) == 1

        p010 = p010_rows.iloc[0]

        # No sales in the analysis window.
        assert p010["total_sales_qty"] == 0
        assert p010["average_daily_sales"] == 0

        # Stock cover cannot be estimated when average daily sales is zero.
        assert pd.isna(p010["estimated_stock_cover_days"])

    finally:
        # Always remove the temporary test data.
        if test_sales_file.exists():
            test_sales_file.unlink()