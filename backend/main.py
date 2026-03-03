from pathlib import Path
import csv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Assignment Dashboard API")

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "processed"

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def read_csv_or_404(filename: str) -> list[dict]:
    path = DATA_DIR / filename
    try:
        with path.open(newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            return [dict(row) for row in reader]
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=f"Data file not found: {filename}") from e


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/api/revenue")
def api_revenue():
    return read_csv_or_404("monthly_revenue.csv")


@app.get("/api/top-customers")
def api_top_customers():
    return read_csv_or_404("top_customers.csv")


@app.get("/api/categories")
def api_categories():
    return read_csv_or_404("category_performance.csv")


@app.get("/api/regions")
def api_regions():
    return read_csv_or_404("regional_analysis.csv")
