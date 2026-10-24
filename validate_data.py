from pathlib import Path

import pandas as pd


# ==================================================
# File Paths
# ==================================================

PROJECT_DIR = Path(__file__).resolve().parent
SALES_FILE = PROJECT_DIR / "data" / "sales.csv"
INVENTORY_FILE = PROJECT_DIR / "data" / "inventory.csv"


# ==================================================
# Expected CSV Columns
# ==================================================

EXPECTED_SALES_COLUMNS = [
    "sales_date",
    "transaction_id",
    "product_id",
    "product_name",
    "category",
    "sales_qty",
    "pos_price",
]

EXPECTED_INVENTORY_COLUMNS = [
    "snapshot_date",
    "product_id",
    "stock_on_hand",
    "reorder_level",
]


# ==================================================
# Sales Data Validation
# ==================================================

print("=" * 50)
print("SALES DATA VALIDATION")
print("=" * 50)

if not SALES_FILE.exists():
    print(f"ERROR - Sales file not found: {SALES_FILE}")

else:
    sales_df = pd.read_csv(SALES_FILE)

    print(f"Sales records: {len(sales_df)}")
    print(f"Sales columns: {list(sales_df.columns)}")

    missing_columns = [
        column
        for column in EXPECTED_SALES_COLUMNS
        if column not in sales_df.columns
    ]

    if missing_columns:
        print(f"ERROR - Missing columns: {missing_columns}")

    else:
        print("PASS - Required columns exist")

        # Check missing values
        missing_values = sales_df[
            EXPECTED_SALES_COLUMNS
        ].isnull().sum()

        if missing_values.sum() == 0:
            print("PASS - No missing values")
        else:
            print("ERROR - Missing values:")
            print(missing_values[missing_values > 0])

        # Check sales dates
        sales_dates = pd.to_datetime(
            sales_df["sales_date"],
            errors="coerce",
        )

        if sales_dates.isna().any():
            print("ERROR - Invalid or missing sales dates")
        else:
            print("PASS - Sales dates are valid")
            print(f"First sales date: {sales_dates.min().date()}")
            print(f"Last sales date: {sales_dates.max().date()}")

        # Check numeric values
        sales_df["sales_qty"] = pd.to_numeric(
            sales_df["sales_qty"],
            errors="coerce",
        )

        sales_df["pos_price"] = pd.to_numeric(
            sales_df["pos_price"],
            errors="coerce",
        )

        invalid_qty = (
            sales_df["sales_qty"].isna()
            | (sales_df["sales_qty"] <= 0)
        )

        invalid_price = (
            sales_df["pos_price"].isna()
            | (sales_df["pos_price"] < 0)
        )

        print(f"Invalid sales quantities: {invalid_qty.sum()}")
        print(f"Invalid POS prices: {invalid_price.sum()}")

        # Check duplicate records
        duplicate_lines = sales_df.duplicated().sum()

        duplicate_transaction_products = sales_df.duplicated(
            subset=["transaction_id", "product_id"],
        ).sum()

        print(f"Exact duplicate rows: {duplicate_lines}")
        print(
            "Duplicate transaction-product pairs: "
            f"{duplicate_transaction_products}"
        )


# ==================================================
# Inventory Data Validation
# ==================================================

print("\n" + "=" * 50)
print("INVENTORY DATA VALIDATION")
print("=" * 50)

if not INVENTORY_FILE.exists():
    print(f"ERROR - Inventory file not found: {INVENTORY_FILE}")

else:
    inventory_df = pd.read_csv(INVENTORY_FILE)

    print(f"Inventory records: {len(inventory_df)}")
    print(f"Inventory columns: {list(inventory_df.columns)}")

    missing_columns = [
        column
        for column in EXPECTED_INVENTORY_COLUMNS
        if column not in inventory_df.columns
    ]

    if missing_columns:
        print(f"ERROR - Missing columns: {missing_columns}")

    else:
        print("PASS - Required columns exist")

        # Check missing values
        missing_values = inventory_df[
            EXPECTED_INVENTORY_COLUMNS
        ].isnull().sum()

        if missing_values.sum() == 0:
            print("PASS - No missing values")
        else:
            print("ERROR - Missing values:")
            print(missing_values[missing_values > 0])

        # Check snapshot dates
        inventory_df["snapshot_date"] = pd.to_datetime(
            inventory_df["snapshot_date"],
            errors="coerce",
        )

        if inventory_df["snapshot_date"].isna().any():
            print("ERROR - Invalid or missing snapshot dates")

        elif (
            inventory_df["snapshot_date"]
            .dt.normalize()
            .nunique() != 1
        ):
            print("ERROR - Inventory must use one snapshot date")

        else:
            snapshot_date = inventory_df[
                "snapshot_date"
            ].iloc[0].date()

            print(f"PASS - Single snapshot date: {snapshot_date}")

        # Check inventory quantities
        for column in ["stock_on_hand", "reorder_level"]:
            numeric_values = pd.to_numeric(
                inventory_df[column],
                errors="coerce",
            )

            if numeric_values.isna().any():
                print(f"ERROR - Invalid numeric values in {column}")

            elif (
                (numeric_values < 0).any()
                or (numeric_values % 1 != 0).any()
            ):
                print(
                    f"ERROR - {column} must contain "
                    "non-negative integers"
                )

            else:
                print(
                    f"PASS - {column} contains valid quantities"
                )

        # Check duplicate product IDs
        if inventory_df["product_id"].duplicated().any():
            print("ERROR - Duplicate product IDs found")
            print(
                inventory_df.loc[
                    inventory_df["product_id"].duplicated(
                        keep=False
                    ),
                    "product_id",
                ]
            )

        else:
            print("PASS - No duplicate product IDs")

        # Compare product IDs with sales data
        if (
            SALES_FILE.exists()
            and all(
                column in sales_df.columns
                for column in ["product_id"]
            )
        ):
            sales_product_ids = set(
                sales_df["product_id"].dropna()
            )

            inventory_product_ids = set(
                inventory_df["product_id"].dropna()
            )

            missing_inventory_products = (
                sales_product_ids - inventory_product_ids
            )

            unknown_inventory_products = (
                inventory_product_ids - sales_product_ids
            )

            if (
                not missing_inventory_products
                and not unknown_inventory_products
            ):
                print(
                    "PASS - Inventory product IDs match "
                    "Sales dataset"
                )

            else:
                if missing_inventory_products:
                    print(
                        "ERROR - Products missing from Inventory:",
                        sorted(missing_inventory_products),
                    )

                if unknown_inventory_products:
                    print(
                        "ERROR - Unknown products in Inventory:",
                        sorted(unknown_inventory_products),
                    )