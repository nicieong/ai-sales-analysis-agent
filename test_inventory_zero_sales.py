
from pathlib import Path
import pandas as pd

from inventory_analysis import analyze_inventory

project_dir = Path(__file__).resolve().parent
sales_file = project_dir / "data" / "sales.csv"
test_sales_file = project_dir / "data" / "sales_zero_test.csv"

df = pd.read_csv(sales_file)

# Move P010's sales records outside the 90-day analysis window.
df.loc[df["product_id"] == "P010", "sales_date"] = "2026-07-20"
df.to_csv(test_sales_file, index=False)

try:
    result = analyze_inventory(sales_file=test_sales_file)

    p010 = result.loc[result["product_id"] == "P010"].iloc[0]

    print("\nZERO-SALES TEST RESULT")
    print(p010[
        [
            "product_id",
            "total_sales_qty",
            "average_daily_sales",
            "estimated_stock_cover_days",
        ]
    ].to_string())

finally:
    if test_sales_file.exists():
        test_sales_file.unlink()
