# Assignment Fullstack Dashboard

## Requirements
- Python 3.9+ (Windows, macOS, or Linux)
- No Node.js required (frontend served via Python http.server)

## Project Structure
- backend/
  - main.py
  - requirements.txt
- frontend/
  - index.html
  - css/styles.css
  - js/app.js
- data/
  - raw/products.csv
  - processed/monthly_revenue.csv, top_customers.csv, category_performance.csv, regional_analysis.csv
- clean_data.py
- analyze.py
- README.md

## Setup
1) Create/activate a virtual environment (optional but recommended)
- python -m venv .venv
- .\\.venv\\Scripts\\Activate.ps1  (Windows PowerShell)
- source .venv/bin/activate        (macOS/Linux)

2) Install backend dependencies
- python -m pip install -r backend/requirements.txt

3) Install data processing dependencies
- python -m pip install pandas numpy

## Generate Data
1) Run cleaning
- python clean_data.py

2) Run analysis
- python analyze.py

This produces CSV outputs in data/processed/.

## Run Backend
- python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

API Endpoints:
- GET /health
- GET /api/revenue
- GET /api/top-customers
- GET /api/categories
- GET /api/regions

## Run Frontend
- python -m http.server 5500 --directory frontend
- Open http://localhost:5500 in your browser

## Verification
Backend:
- Open http://127.0.0.1:8000/health -> {"status":"ok"}
- Open each endpoint and confirm JSON arrays:
  - http://127.0.0.1:8000/api/revenue
  - http://127.0.0.1:8000/api/top-customers
  - http://127.0.0.1:8000/api/categories
  - http://127.0.0.1:8000/api/regions

Frontend:
- Ensure frontend/js/app.js has API_BASE = "http://127.0.0.1:8000"
- Use browser DevTools → Network to confirm 200 responses and JSON payloads

Expected JSON keys:
- revenue: { "month": "YYYY-MM", "revenue": 12345.67 }
- categories: { "category": "Electronics", "revenue": 250000.75 }
- regions: { "region": "NA", "revenue": 300450.0, "orders": 1234 }
- top_customers: { "customer_name": "Acme", "region": "EMEA", "total_spend": 45230.5, "order_count": 12, "churn_status": "active" }

## Troubleshooting
- If charts show zeros:
  - Confirm endpoints return numerics; app.js uses a toNum() helper to coerce strings like "12,345.67" to numbers
  - Confirm key names match the mappings (month/date/period, revenue/total/value)
- If 404 on endpoints:
  - Confirm data/processed CSV files exist and have non-empty content
- If CORS errors:
  - Backend includes CORS middleware allowing "*"; restart backend and reload frontend

## Linting (Optional)
- python -m pip install flake8 black
- flake8
- black .

- Demo--<img width="1900" height="824" alt="image" src="https://github.com/user-attachments/assets/2f547c2a-a090-4628-9c64-e5a48b78eefc" />

