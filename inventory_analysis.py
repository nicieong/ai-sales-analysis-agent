
from pathlib import Path

import pandas as pd


# ==================================================
# File Paths
# ==================================================

PROJECT_DIR = Path(__file__).resolve().parent
DATA_DIR = PROJECT_DIR / "data"

SALES_FILE = DATA_DIR / "sales.csv"
INVENTORY_FILE = DATA_DIR / "inventory.csv"


# ==================================================
# 1. Load Inventory Data
# ==================================================

def load_inventory_data(file_path=INVENTORY_FILE):
    """
    Load and validate basic Inventory data.
    """

    inventory_df = pd.read_csv(file_path)

    required_columns = [
        "snapshot_date",
        "product_id",
        "stock_on_hand",
        "reorder_level",
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in inventory_df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Inventory CSV is missing columns: {missing_columns}"
        )

    if inventory_df.empty:
        raise ValueError("Inventory CSV contains no records.")

    if inventory_df[required_columns].isnull().any().any():
        raise ValueError("Inventory CSV contains missing values.")

    inventory_df["snapshot_date"] = pd.to_datetime(
        inventory_df["snapshot_date"],
        errors="coerce",
    )

    if inventory_df["snapshot_date"].isnull().any():
        raise ValueError("Inventory contains invalid snapshot dates.")

    if inventory_df["snapshot_date"].dt.normalize().nunique() != 1:
        raise ValueError(
            "Inventory must contain exactly one snapshot date."
        )

    for column in ["stock_on_hand", "reorder_level"]:
        inventory_df[column] = pd.to_numeric(
            inventory_df[column],
            errors="coerce",
        )

        if inventory_df[column].isnull().any():
            raise ValueError(
                f"Inventory contains invalid values in {column}."
            )

        if (
            (inventory_df[column] < 0).any()
            or (inventory_df[column] % 1 != 0).any()
        ):
            raise ValueError(
                f"{column} must contain non-negative integers."
            )

    if inventory_df["product_id"].duplicated().any():
        raise ValueError("Inventory contains duplicate product IDs.")

    return inventory_df


# ==================================================
# 2. Calculate Average Daily Sales by Product
# ==================================================

def get_average_daily_sales(
    file_path=SALES_FILE,
    snapshot_date=None,
):
    """
    Calculate average daily sales using up to the latest
    90 calendar days ending on the inventory snapshot date.

    The actual available sales-data coverage is also returned
    as metadata so users can distinguish a full 90-day window
    from a shorter historical dataset.
    """

    sales_df = pd.read_csv(file_path)

    required_columns = [
        "sales_date",
        "product_id",
        "product_name",
        "category",
        "sales_qty",
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in sales_df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Sales CSV is missing columns: {missing_columns}"
        )

    if sales_df.empty:
        raise ValueError("Sales CSV contains no records.")

    sales_df["sales_date"] = pd.to_datetime(
        sales_df["sales_date"],
        errors="coerce",
    )

    if sales_df["sales_date"].isnull().any():
        raise ValueError("Sales CSV contains invalid sales dates.")

    sales_df["sales_qty"] = pd.to_numeric(
        sales_df["sales_qty"],
        errors="coerce",
    )

    if (
        sales_df["sales_qty"].isnull().any()
        or (sales_df["sales_qty"] < 0).any()
    ):
        raise ValueError(
            "Sales quantities must be non-negative numbers."
        )

    # Use the inventory snapshot date as the analysis anchor.
    if snapshot_date is None:
        snapshot_date = sales_df["sales_date"].max()

    snapshot_date = pd.Timestamp(snapshot_date).normalize()

    # Inclusive 90-calendar-day window.
    start_date = snapshot_date - pd.Timedelta(days=89)

    sales_df["sales_date"] = sales_df["sales_date"].dt.normalize()

    # Ignore sales after the inventory snapshot date.
    sales_df = sales_df[
        (sales_df["sales_date"] >= start_date)
        & (sales_df["sales_date"] <= snapshot_date)
    ].copy()

    if sales_df.empty:
        raise ValueError(
            "No sales records found within the 90-day window."
        )

    # Actual data coverage within the requested window.
    actual_start_date = sales_df["sales_date"].min()
    actual_end_date = sales_df["sales_date"].max()

    days_analyzed = (
        snapshot_date - start_date
    ).days + 1

    daily_sales = (
        sales_df.groupby("product_id", as_index=False)
        .agg(total_sales_qty=("sales_qty", "sum"))
    )

    daily_sales["average_daily_sales"] = (
        daily_sales["total_sales_qty"] / days_analyzed
    )

    product_info = (
        sales_df[
            ["product_id", "product_name", "category"]
        ]
        .drop_duplicates(subset=["product_id"])
    )

    daily_sales = daily_sales.merge(
        product_info,
        on="product_id",
        how="left",
        validate="one_to_one",
    )

    daily_sales.attrs["snapshot_date"] = snapshot_date.date().isoformat()
    daily_sales.attrs["window_start_date"] = start_date.date().isoformat()
    daily_sales.attrs["window_end_date"] = snapshot_date.date().isoformat()
    daily_sales.attrs["actual_start_date"] = actual_start_date.date().isoformat()
    daily_sales.attrs["actual_end_date"] = actual_end_date.date().isoformat()
    daily_sales.attrs["days_analyzed"] = days_analyzed

    return daily_sales[
        [
            "product_id",
            "product_name",
            "category",
            "total_sales_qty",
            "average_daily_sales",
        ]
    ]


# ==================================================
# 3. Analyze Inventory Risk and Stock Cover
# ==================================================

def analyze_inventory(
    inventory_file=INVENTORY_FILE,
    sales_file=SALES_FILE,
):
    """
    Combine Inventory and Sales data to assess stock risk.

    Inventory is a single snapshot, not a rolling stock ledger.
    Stock cover is an estimate based on historical average
    daily sales velocity.
    """

    inventory_df = load_inventory_data(inventory_file)

    snapshot_date = inventory_df["snapshot_date"].max()

    daily_sales = get_average_daily_sales(
        file_path=sales_file,
        snapshot_date=snapshot_date,
    )

    result_df = inventory_df.merge(
        daily_sales,
        on="product_id",
        how="left",
        validate="one_to_one",
    )

    # Products with no sales records in the analysis window
    # should remain in the Inventory report.
    result_df["total_sales_qty"] = (
        result_df["total_sales_qty"].fillna(0)
    )
    result_df["average_daily_sales"] = (
        result_df["average_daily_sales"].fillna(0)
    )

    # Check product IDs against the full Sales dataset,
    # not only the filtered 90-day sales results.
    all_sales_df = pd.read_csv(sales_file)

    sales_product_ids = set(
        all_sales_df["product_id"].dropna()
    )

    inventory_product_ids = set(
        inventory_df["product_id"].dropna()
    )

    unknown_product_ids = (
            inventory_product_ids - sales_product_ids
    )

    if unknown_product_ids:
        raise ValueError(
            "Inventory products not found in Sales data: "
            f"{sorted(unknown_product_ids)}"
        )

    # 1. Inventory risk status
    result_df["inventory_status"] = "In Stock"

    reorder_mask = (
        result_df["stock_on_hand"]
        <= result_df["reorder_level"]
    )

    result_df.loc[
        reorder_mask, "inventory_status"
    ] = "Reorder Required"

    # 2. Estimated Stock Cover
    result_df["estimated_stock_cover_days"] = float("nan")

    has_sales = result_df["average_daily_sales"] > 0

    result_df.loc[
        has_sales, "estimated_stock_cover_days"
    ] = (
        result_df.loc[has_sales, "stock_on_hand"]
        / result_df.loc[has_sales, "average_daily_sales"]
    )

    # Round for easier reading.
    result_df["average_daily_sales"] = (
        result_df["average_daily_sales"].round(2)
    )

    result_df["estimated_stock_cover_days"] = (
        result_df["estimated_stock_cover_days"].round(2)
    )

    # Show the lowest-stock and reorder items first.
    result_df = result_df.sort_values(
        by=["inventory_status", "estimated_stock_cover_days"],
        ascending=[True, True],
        na_position="last",
    ).reset_index(drop=True)

    return result_df[
        [
            "snapshot_date",
            "product_id",
            "product_name",
            "category",
            "stock_on_hand",
            "reorder_level",
            "total_sales_qty",
            "average_daily_sales",
            "inventory_status",
            "estimated_stock_cover_days",
        ]
    ]


# ==================================================
# 4. Run Inventory Analysis
# ==================================================

if __name__ == "__main__":

    inventory_result = analyze_inventory()

    print("\n" + "=" * 80)
    print("INVENTORY ANALYSIS")
    print("=" * 80)

    print(
        inventory_result.to_string(
            index=False,
            formatters={
                "average_daily_sales": lambda value: f"{value:.2f}",
                "estimated_stock_cover_days": (
                    lambda value: (
                        f"{value:.2f}"
                        if pd.notna(value)
                        else "Not estimable"
                    )
                ),
            },
        )
    )

    print("\n" + "-" * 80)
    print("INVENTORY SUMMARY")
    print("-" * 80)

    print(
        "Snapshot date:",
        inventory_result["snapshot_date"].iloc[0].date(),
    )

    print(
        "Total products:",
        len(inventory_result),
    )

    print(
        "Products requiring reorder:",
        (
            inventory_result["inventory_status"]
            == "Reorder Required"
        ).sum(),
    )

    print(
        "Products with stock cover estimable:",
        inventory_result["estimated_stock_cover_days"].notna().sum(),
    )
