import pandas as pd
from pathlib import Path
import logging

# -------------------------
# Setup logging
# -------------------------
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

# -------------------------
# Setup paths
# -------------------------
BASE_DIR = Path(__file__).parent
RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

# -------------------------
# Load CSV files
# -------------------------
customers = pd.read_csv(RAW_DIR / "customers.csv")
orders = pd.read_csv(RAW_DIR / "orders.csv")

customers_before = len(customers)
orders_before = len(orders)

# =========================
# 1. CLEAN customers.csv
# =========================

# Strip whitespace
customers["name"] = customers["name"].astype(str).str.strip()
customers["region"] = customers["region"].astype(str).str.strip()

# Fill missing region
customers["region"] = customers["region"].replace("", pd.NA)
customers["region"] = customers["region"].fillna("Unknown")

# Standardize email
customers["email"] = customers["email"].astype(str).str.lower()

# Validate email
customers["is_valid_email"] = customers["email"].apply(
    lambda x: False if pd.isna(x) or "@" not in x or "." not in x else True
)

# Parse signup_date
customers["signup_date"] = pd.to_datetime(
    customers["signup_date"], errors="coerce"
)

if customers["signup_date"].isna().sum() > 0:
    logger.warning("Some signup_date values could not be parsed and set to NaT.")

# Remove duplicates keeping most recent signup_date
customers = customers.sort_values(
    by="signup_date", ascending=False
)
customers = customers.drop_duplicates(
    subset="customer_id", keep="first"
)

customers_after = len(customers)

# Save cleaned customers
customers.to_csv(
    PROCESSED_DIR / "customers_clean.csv",
    index=False
)

# =========================
# 2. CLEAN orders.csv
# =========================

# Custom date parser
def parse_date(val):
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m-%d-%Y"):
        try:
            return pd.to_datetime(val, format=fmt)
        except:
            continue
    return pd.NaT

orders["order_date"] = orders["order_date"].apply(parse_date)

# Drop rows where BOTH ids are null
orders = orders.dropna(
    subset=["customer_id", "order_id"],
    how="all"
)

# Convert amount to numeric
orders["amount"] = pd.to_numeric(
    orders["amount"], errors="coerce"
)

# Fill missing amount with median per product
orders["amount"] = orders.groupby("product")["amount"].transform(
    lambda x: x.fillna(x.median())
)

# Normalize status
status_map = {
    "done": "completed",
    "complete": "completed",
    "completed": "completed",
    "canceled": "cancelled",
    "cancelled": "cancelled",
    "refund": "refunded",
    "refunded": "refunded",
    "pending": "pending"
}

orders["status"] = orders["status"].astype(str).str.lower()
orders["status"] = orders["status"].replace(status_map)

# Add order_year_month
orders["order_year_month"] = orders["order_date"].dt.strftime("%Y-%m")

orders_after = len(orders)

# Save cleaned orders
orders.to_csv(
    PROCESSED_DIR / "orders_clean.csv",
    index=False
)

# =========================
# 3. PRINT REPORT
# =========================

print("\n====== CLEANING REPORT ======")
print("\nCustomers:")
print("Rows before:", customers_before)
print("Rows after :", customers_after)
print("Null counts:\n", customers.isna().sum())

print("\nOrders:")
print("Rows before:", orders_before)
print("Rows after :", orders_after)
print("Null counts:\n", orders.isna().sum())
print("=============================")