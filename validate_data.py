from pathlib import Path

import pandas as pd

# Locate the sales CSV file
PROJECT_DIR = Path(__file__).resolve().parent
SALES_FILE = PROJECT_DIR / "data" / "sales.csv"

# Expected CSV columns
EXPECTED_COLUMNS = [
    "sales_date",
    "transaction_id",
    "product_id",
    "product_name",
    "category",
    "sales_qty",
    "pos_price",
]

# Load sales data
sales_df = pd.read_csv(SALES_FILE)

# Basic validation
print("Sales Data Validation")
print("---------------------")
print(f"Total sales lines: {len(sales_df)}")
print(f"Columns correct: {list(sales_df.columns) == EXPECTED_COLUMNS}")
print(f"First sales date: {sales_df['sales_date'].min()}")
print(f"Last sales date: {sales_df['sales_date'].max()}")

print("\nData Quality Checks")
print("-------------------")

# Check for missing values
missing_values = sales_df.isnull().sum()
print("Missing values per column:")
print(missing_values)

# Check numeric values
sales_df["sales_qty"] = pd.to_numeric(
    sales_df["sales_qty"],
    errors="coerce",
)
sales_df["pos_price"] = pd.to_numeric(
    sales_df["pos_price"],
    errors="coerce",
)

invalid_qty = sales_df["sales_qty"].isnull() | (
    sales_df["sales_qty"] <= 0
)
invalid_price = sales_df["pos_price"].isnull() | (
    sales_df["pos_price"] < 0
)

print(f"Invalid sales quantities: {invalid_qty.sum()}")
print(f"Invalid POS prices: {invalid_price.sum()}")

print("\nDuplicate Record Checks")
print("-----------------------")

duplicate_lines = sales_df.duplicated().sum()

duplicate_transaction_products = sales_df.duplicated(
    subset=["transaction_id", "product_id"],
).sum()

print(f"Exact duplicate rows: {duplicate_lines}")
print(
    "Duplicate transaction-product pairs: "
    f"{duplicate_transaction_products}"
)


print("\nSales Summary")
print("-------------")

sales_df["sales_amount"] = (
    sales_df["sales_qty"] * sales_df["pos_price"]
)

total_sales = sales_df["sales_amount"].sum()

print(f"Total sales quantity: {sales_df['sales_qty'].sum()}")
print(f"Total sales amount: CAD {total_sales:,.2f}")

print("\nSales by Product")
print("----------------")

product_sales = (
    sales_df.groupby(
        ["product_id", "product_name"],
        as_index=False,
    )
    .agg(
        total_qty=("sales_qty", "sum"),
        total_sales=("sales_amount", "sum"),
    )
    .sort_values("total_sales", ascending=False)
)

product_sales["sales_contribution_pct"] = (
    product_sales["total_sales"]
    / product_sales["total_sales"].sum()
    * 100
)

print(
    product_sales.to_string(
        index=False,
        formatters={
            "total_sales": lambda value: f"CAD {value:,.2f}",
            "sales_contribution_pct": lambda value: f"{value:.2f}%",
        },
    )
)


print("\nDaily Sales Summary")
print("-------------------")

daily_sales = (
    sales_df.groupby("sales_date")
    .agg(
        sales_amount=("sales_amount", "sum"),
        sales_qty=("sales_qty", "sum"),
        transaction_count=("transaction_id", "nunique"),
    )
    .reset_index()
    .sort_values("sales_date")
)

print(f"Number of sales days: {len(daily_sales)}")
print("\nFirst 5 days:")
print(daily_sales.head().to_string(index=False))

print("\nDaily Sales KPIs")
print("----------------")

average_daily_sales = daily_sales["sales_amount"].mean()

median_daily_sales = daily_sales["sales_amount"].median()

highest_sales_day = daily_sales.loc[
    daily_sales["sales_amount"].idxmax()
]

lowest_sales_day = daily_sales.loc[
    daily_sales["sales_amount"].idxmin()
]

print(f"Average daily sales: CAD {average_daily_sales:,.2f}")

print(f"Median daily sales: CAD {median_daily_sales:,.2f}")

print(
    f"Highest sales day: {highest_sales_day['sales_date']} "
    f"(CAD {highest_sales_day['sales_amount']:,.2f})"
)

print(
    f"Lowest sales day: {lowest_sales_day['sales_date']} "
    f"(CAD {lowest_sales_day['sales_amount']:,.2f})"
)


print("\nMonth Period Analysis")
print("---------------------")

daily_sales["sales_date"] = pd.to_datetime(
    daily_sales["sales_date"]
)

day_of_month = daily_sales["sales_date"].dt.day

daily_sales["month_period"] = pd.cut(
    day_of_month,
    bins=[0, 10, 20, 31],
    labels=["Beginning", "Middle", "End"],
)

print(
    daily_sales[
        ["sales_date", "sales_amount", "month_period"]
    ].head(10).to_string(index=False)
)


period_summary = (
    daily_sales.groupby(
        "month_period",
        observed=False,
    )
    .agg(
        days=("sales_date", "count"),
        avg_daily_sales=("sales_amount", "mean"),
        avg_daily_qty=("sales_qty", "mean"),
    )
    .reset_index()
)

print("\nAverage Performance by Month Period")
print("-----------------------------------")

print(
    period_summary.to_string(
        index=False,
        formatters={
            "avg_daily_sales": lambda value: f"CAD {value:,.2f}",
            "avg_daily_qty": lambda value: f"{value:.2f}",
        },
    )
)


overall_avg_sales = daily_sales["sales_amount"].mean()

period_summary["vs_overall_avg_pct"] = (
    (period_summary["avg_daily_sales"] - overall_avg_sales)
    / overall_avg_sales
    * 100
)

print("\nPeriod Sales vs Overall Average")
print("--------------------------------")

print(
    period_summary[
        ["month_period", "avg_daily_sales", "vs_overall_avg_pct"]
    ].to_string(
        index=False,
        formatters={
            "avg_daily_sales": lambda value: f"CAD {value:,.2f}",
            "vs_overall_avg_pct": lambda value: f"{value:+.2f}%",
        },
    )
)


print("\nWeekday / Weekend Classification")
print("--------------------------------")

daily_sales["day_of_week"] = (
    daily_sales["sales_date"].dt.day_name()
)

daily_sales["day_type"] = daily_sales["day_of_week"].isin(
    ["Saturday", "Sunday"]
).map({
    True: "Weekend",
    False: "Weekday",
})

print(
    daily_sales[
        ["sales_date", "day_of_week", "day_type"]
    ].head(15).to_string(index=False)
)

print("\nDays by Type")
print("------------")
print(
    daily_sales["day_type"]
    .value_counts()
    .to_string()
)


print("\nWeekday vs Weekend Analysis")
print("---------------------------")

day_type_summary = (
    daily_sales.groupby("day_type")
    .agg(
        days=("sales_date", "count"),
        total_sales=("sales_amount", "sum"),
        avg_daily_sales=("sales_amount", "mean"),
        avg_daily_qty=("sales_qty", "mean"),
        total_transactions=("transaction_count", "sum"),
    )
    .reset_index()
)

day_type_summary["avg_daily_transactions"] = (
    day_type_summary["total_transactions"]
    / day_type_summary["days"]
)

day_type_summary["avg_transaction_value"] = (
    day_type_summary["total_sales"]
    / day_type_summary["total_transactions"]
)

print(
    day_type_summary[
        [
            "day_type",
            "days",
            "avg_daily_sales",
            "avg_daily_qty",
            "avg_daily_transactions",
            "avg_transaction_value",
        ]
    ].to_string(
        index=False,
        formatters={
            "avg_daily_sales": lambda value: f"CAD {value:,.2f}",
            "avg_daily_qty": lambda value: f"{value:.2f}",
            "avg_daily_transactions": lambda value: f"{value:.2f}",
            "avg_transaction_value": lambda value: f"CAD {value:,.2f}",
        },
    )
)


print("\nSales Performance by Day of Week")
print("--------------------------------")

weekday_order = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]

weekday_summary = (
    daily_sales.groupby("day_of_week")
    .agg(
        days=("sales_date", "count"),
        avg_daily_sales=("sales_amount", "mean"),
        avg_daily_qty=("sales_qty", "mean"),
        total_sales=("sales_amount", "sum"),
        total_transactions=("transaction_count", "sum"),
    )
    .reindex(weekday_order)
    .reset_index(names="day_of_week")
)

weekday_summary["avg_daily_transactions"] = (
    weekday_summary["total_transactions"]
    / weekday_summary["days"]
)

weekday_summary["avg_transaction_value"] = (
    weekday_summary["total_sales"]
    / weekday_summary["total_transactions"]
)

print(
    weekday_summary[
        [
            "day_of_week",
            "days",
            "avg_daily_sales",
            "avg_daily_transactions",
            "avg_transaction_value",
        ]
    ].to_string(
        index=False,
        formatters={
            "avg_daily_sales": lambda value: f"CAD {value:,.2f}",
            "avg_daily_transactions": lambda value: f"{value:.2f}",
            "avg_transaction_value": lambda value: f"CAD {value:,.2f}",
        },
    )
)


overall_avg_daily_sales = daily_sales["sales_amount"].mean()

weekday_summary["vs_overall_avg_pct"] = (
    (
        weekday_summary["avg_daily_sales"]
        - overall_avg_daily_sales
    )
    / overall_avg_daily_sales
    * 100
)

print("\nDay of Week vs Overall Average")
print("--------------------------------")

print(
    weekday_summary[
        [
            "day_of_week",
            "avg_daily_sales",
            "vs_overall_avg_pct",
        ]
    ].to_string(
        index=False,
        formatters={
            "avg_daily_sales": lambda value: f"CAD {value:,.2f}",
            "vs_overall_avg_pct": lambda value: f"{value:+.2f}%",
        },
    )
)



# ==================================================
# Inventory Data Validation
# ==================================================

INVENTORY_FILE = PROJECT_DIR / "data" / "inventory.csv"

EXPECTED_INVENTORY_COLUMNS = [
    "snapshot_date",
    "product_id",
    "stock_on_hand",
    "reorder_level",
]

print("\n" + "=" * 50)
print("INVENTORY DATA VALIDATION")
print("=" * 50)

# 1. Load Inventory CSV
inventory_df = pd.read_csv(INVENTORY_FILE)

print(f"Inventory records: {len(inventory_df)}")
print(f"Inventory columns: {list(inventory_df.columns)}")

# 2. Check required columns
missing_columns = [
    column
    for column in EXPECTED_INVENTORY_COLUMNS
    if column not in inventory_df.columns
]

if missing_columns:
    print(f"ERROR - Missing columns: {missing_columns}")
else:
    print("PASS - Required columns exist")


# Continue detailed checks only when all required columns exist
if not missing_columns:

    # 3. Check missing values
    missing_values = inventory_df[
        EXPECTED_INVENTORY_COLUMNS
    ].isnull().sum()

    if missing_values.sum() == 0:
        print("PASS - No missing values")
    else:
        print("ERROR - Missing values:")
        print(missing_values[missing_values > 0])

    # 4. Validate snapshot dates
    inventory_df["snapshot_date"] = pd.to_datetime(
        inventory_df["snapshot_date"],
        errors="coerce"
    )

    if inventory_df["snapshot_date"].isna().any():
        print("ERROR - Invalid or missing snapshot dates")
    elif inventory_df["snapshot_date"].dt.normalize().nunique() != 1:
        print("ERROR - Inventory must use one snapshot date")
    else:
        snapshot_date = inventory_df["snapshot_date"].iloc[0].date()
        print(f"PASS - Single snapshot date: {snapshot_date}")

    # 5. Validate inventory quantities
    for column in ["stock_on_hand", "reorder_level"]:
        numeric_values = pd.to_numeric(
            inventory_df[column],
            errors="coerce"
        )

        if numeric_values.isna().any():
            print(f"ERROR - Invalid numeric values in {column}")
        elif (
            (numeric_values < 0).any()
            or (numeric_values % 1 != 0).any()
        ):
            print(f"ERROR - {column} must contain non-negative integers")
        else:
            print(f"PASS - {column} contains valid quantities")

    # 6. Check duplicate product IDs
    if inventory_df["product_id"].duplicated().any():
        print("ERROR - Duplicate product IDs found")
        print(
            inventory_df.loc[
                inventory_df["product_id"].duplicated(keep=False),
                "product_id"
            ]
        )
    else:
        print("PASS - No duplicate product IDs")

    # 7. Check product IDs against Sales dataset
    sales_product_ids = set(sales_df["product_id"].dropna())
    inventory_product_ids = set(
        inventory_df["product_id"].dropna()
    )

    missing_inventory_products = (
        sales_product_ids - inventory_product_ids
    )
    unknown_inventory_products = (
        inventory_product_ids - sales_product_ids
    )

    if not missing_inventory_products and not unknown_inventory_products:
        print("PASS - Inventory product IDs match Sales dataset")
    else:
        if missing_inventory_products:
            print(
                "ERROR - Products missing from Inventory:",
                sorted(missing_inventory_products)
            )

        if unknown_inventory_products:
            print(
                "ERROR - Unknown products in Inventory:",
                sorted(unknown_inventory_products)
            )
