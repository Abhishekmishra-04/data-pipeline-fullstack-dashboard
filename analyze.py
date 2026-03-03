from pathlib import Path
import pandas as pd
from pandas.errors import EmptyDataError


def load_csv(path: Path) -> pd.DataFrame:
    """Load CSV with basic error handling."""
    try:
        return pd.read_csv(path)
    except FileNotFoundError as e:
        raise FileNotFoundError(f"File not found: {path}") from e
    except EmptyDataError as e:
        raise EmptyDataError(f"CSV is empty: {path}") from e


# -----------------------------
# Paths (no hardcoded absolute paths)
# -----------------------------
BASE = Path(__file__).parent
RAW = BASE / "data" / "raw"
PROCESSED = BASE / "data" / "processed"

# -----------------------------
# Load input files
# -----------------------------
customers = load_csv(PROCESSED / "customers_clean.csv")
orders = load_csv(PROCESSED / "orders_clean.csv")
products = load_csv(RAW / "products.csv")

print("Files loaded successfully!")

# Ensure date is datetime
orders["order_date"] = pd.to_datetime(orders["order_date"], errors="coerce")

# -----------------------------
# 2.1 Merging (EXPLICIT)
# -----------------------------
orders_with_customers = pd.merge(
    orders,
    customers,
    on="customer_id",
    how="left"
)

full_data = pd.merge(
    orders_with_customers,
    products,
    left_on="product",
    right_on="product_name",
    how="left"
)

# Missing match report
no_customer = int(orders_with_customers["name"].isna().sum())
no_product = int(full_data["product_id"].isna().sum())

print("\n====== MERGE REPORT ======")
print("Orders with NO matching customer:", no_customer)
print("Orders with NO matching product :", no_product)
print("==========================\n")

# -----------------------------
# 2.2 Analysis (COMPLETED orders only)
# -----------------------------
full_data["order_date"] = pd.to_datetime(full_data["order_date"], errors="coerce")
completed = full_data[full_data["status"] == "completed"].copy()

# 1) Monthly Revenue Trend
if "order_year_month" not in completed.columns:
    completed["order_year_month"] = completed["order_date"].dt.strftime("%Y-%m")
completed_non_null = completed[completed["order_year_month"].notna()].copy()
monthly_revenue = (
    completed_non_null.groupby("order_year_month")["amount"]
    .sum()
    .reset_index()
    .rename(columns={"amount": "total_revenue"})
    .sort_values("order_year_month")
)
monthly_revenue.to_csv(PROCESSED / "monthly_revenue.csv", index=False)
print("Saved: monthly_revenue.csv")

# 2) Top Customers (Top 10)
top_customers = (
    completed.groupby(["customer_id", "name", "region"], dropna=False)["amount"]
    .sum()
    .reset_index()
    .rename(columns={"amount": "total_spend"})
    .sort_values("total_spend", ascending=False)
    .head(10)
)

# 5) Churn Indicator (no completed orders in last 90 days)
latest_date = completed["order_date"].max()

if pd.isna(latest_date):
    top_customers["churned"] = True
else:
    cutoff = latest_date - pd.Timedelta(days=90)
    active_customers = set(
        completed.loc[completed["order_date"] >= cutoff, "customer_id"]
        .dropna()
        .astype(int)
        .tolist()
    )
    top_customers["churned"] = ~top_customers["customer_id"].astype(int).isin(active_customers)

top_customers.to_csv(PROCESSED / "top_customers.csv", index=False)
print("Saved: top_customers.csv")

# 3) Category Performance
category_performance = (
    completed.groupby("category", dropna=False)
    .agg(
        total_revenue=("amount", "sum"),
        avg_order_value=("amount", "mean"),
        number_of_orders=("order_id", "count"),
    )
    .reset_index()
    .sort_values("total_revenue", ascending=False)
)
category_performance.to_csv(PROCESSED / "category_performance.csv", index=False)
print("Saved: category_performance.csv")

# 4) Regional Analysis
customers_per_region = (
    customers.groupby("region", dropna=False)["customer_id"]
    .nunique()
    .reset_index()
    .rename(columns={"customer_id": "num_customers"})
)

region_orders_revenue = (
    completed.groupby("region", dropna=False)
    .agg(
        num_orders=("order_id", "count"),
        total_revenue=("amount", "sum"),
    )
    .reset_index()
)

regional_analysis = pd.merge(
    customers_per_region,
    region_orders_revenue,
    on="region",
    how="left"
)

regional_analysis["num_orders"] = regional_analysis["num_orders"].fillna(0).astype(int)
regional_analysis["total_revenue"] = regional_analysis["total_revenue"].fillna(0)

regional_analysis["avg_revenue_per_customer"] = (
    regional_analysis["total_revenue"] / regional_analysis["num_customers"]
).round(2)

regional_analysis.to_csv(PROCESSED / "regional_analysis.csv", index=False)
print("Saved: regional_analysis.csv")

print("\n✅ TASK 2 COMPLETE. Outputs saved in data/processed/")
