import csv
import random
from datetime import date, timedelta
from pathlib import Path


# Make generated data reproducible
random.seed(42)

# Project paths
PROJECT_DIR = Path(__file__).resolve().parent
DATA_DIR = PROJECT_DIR / "data"

# Dataset settings
NUM_DAYS = 90
CURRENCY = "CAD"

# Synthetic product master
PRODUCTS = [
    {"product_id": "P001", "product_name": "Coffee", "category": "Beverages"},
    {"product_id": "P002", "product_name": "Green Tea", "category": "Beverages"},
    {"product_id": "P003", "product_name": "Orange Juice", "category": "Beverages"},
    {"product_id": "P004", "product_name": "Potato Chips", "category": "Snacks"},
    {"product_id": "P005", "product_name": "Chocolate Bar", "category": "Snacks"},
    {"product_id": "P006", "product_name": "Breakfast Cereal", "category": "Grocery"},
    {"product_id": "P007", "product_name": "Pasta", "category": "Grocery"},
    {"product_id": "P008", "product_name": "Laundry Detergent", "category": "Household"},
    {"product_id": "P009", "product_name": "Dish Soap", "category": "Household"},
    {"product_id": "P010", "product_name": "Shampoo", "category": "Personal Care"},
]

# Each product's regular selling price is only used to generate
# a plausible POS transaction price. It is NOT written as a CSV field.
REGULAR_PRICES = {
    "P001": 12.99,
    "P002": 6.49,
    "P003": 4.99,
    "P004": 3.49,
    "P005": 2.29,
    "P006": 5.99,
    "P007": 2.79,
    "P008": 9.99,
    "P009": 3.99,
    "P010": 7.99,
}

# Synthetic end-of-day inventory snapshot
INVENTORY_DATA = [
    {"snapshot_date": "2026-10-18", "product_id": "P001", "stock_on_hand": 45, "reorder_level": 20},
    {"snapshot_date": "2026-10-18", "product_id": "P002", "stock_on_hand": 18, "reorder_level": 25},
    {"snapshot_date": "2026-10-18", "product_id": "P003", "stock_on_hand": 60, "reorder_level": 20},
    {"snapshot_date": "2026-10-18", "product_id": "P004", "stock_on_hand": 12, "reorder_level": 15},
    {"snapshot_date": "2026-10-18", "product_id": "P005", "stock_on_hand": 80, "reorder_level": 30},
    {"snapshot_date": "2026-10-18", "product_id": "P006", "stock_on_hand": 22, "reorder_level": 20},
    {"snapshot_date": "2026-10-18", "product_id": "P007", "stock_on_hand": 35, "reorder_level": 15},
    {"snapshot_date": "2026-10-18", "product_id": "P008", "stock_on_hand": 8, "reorder_level": 12},
    {"snapshot_date": "2026-10-18", "product_id": "P009", "stock_on_hand": 28, "reorder_level": 15},
    {"snapshot_date": "2026-10-18", "product_id": "P010", "stock_on_hand": 14, "reorder_level": 18},
]


def create_inventory_csv():
    """Write synthetic inventory records to inventory.csv."""
    inventory_file = DATA_DIR / "inventory.csv"

    fieldnames = [
        "snapshot_date",
        "product_id",
        "stock_on_hand",
        "reorder_level",
    ]

    with inventory_file.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(INVENTORY_DATA)

    print(f"Inventory records generated: {len(INVENTORY_DATA)}")
    print(f"Inventory CSV saved to: {inventory_file}")


# Sales generation period ends on this date.
END_DATE = date(2026, 10, 18)
START_DATE = END_DATE - timedelta(days=NUM_DAYS - 1)

print(f"Currency: {CURRENCY}")
print(f"Number of products: {len(PRODUCTS)}")
print(f"Sales period: {START_DATE} to {END_DATE}")
print(f"Output folder: {DATA_DIR}")


def generate_sales_for_day(sales_date):
    """Generate synthetic POS sales lines for one day."""
    daily_sales = []

    num_transactions = random.randint(20, 40)

    for transaction_number in range(num_transactions):
        transaction_id = (
            f"TXN{sales_date.strftime('%Y%m%d')}"
            f"{transaction_number + 1:03d}"
        )

        products_in_transaction = random.randint(1, 3)
        selected_products = random.sample(
            PRODUCTS,
            products_in_transaction,
        )

        for product in selected_products:
            regular_price = REGULAR_PRICES[product["product_id"]]

            # Most sales use regular price; some receive a discount.
            if random.random() < 0.25:
                discount_rate = random.choice([0.10, 0.20])
            else:
                discount_rate = 0.0

            pos_price = round(
                regular_price * (1 - discount_rate),
                2,
            )

            sales_qty = random.randint(1, 4)

            daily_sales.append({
                "sales_date": sales_date.isoformat(),
                "transaction_id": transaction_id,
                "product_id": product["product_id"],
                "product_name": product["product_name"],
                "category": product["category"],
                "sales_qty": sales_qty,
                "pos_price": f"{pos_price:.2f}",
            })

    return daily_sales


def create_sales_csv(all_sales):
    """Write generated sales records to sales.csv."""
    sales_file = DATA_DIR / "sales.csv"

    fieldnames = [
        "sales_date",
        "transaction_id",
        "product_id",
        "product_name",
        "category",
        "sales_qty",
        "pos_price",
    ]

    with sales_file.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_sales)

    print(f"Total sales lines generated: {len(all_sales)}")
    print(f"Sales CSV saved to: {sales_file}")


def generate_all_sales():
    """Generate sales lines for the full 90-day period."""
    all_sales = []

    for day_number in range(NUM_DAYS):
        sales_date = START_DATE + timedelta(days=day_number)
        daily_sales = generate_sales_for_day(sales_date)
        all_sales.extend(daily_sales)

    create_sales_csv(all_sales)


generate_all_sales()
create_inventory_csv()