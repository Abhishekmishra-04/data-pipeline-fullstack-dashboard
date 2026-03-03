// Configuration
const API_BASE = "http://127.0.0.1:8000";

// Utilities
const fmtNumber = (n) =>
  typeof n === "number"
    ? n.toLocaleString(undefined, { maximumFractionDigits: 2 })
    : n;
const toNum = (v) => {
  if (typeof v === "number") return v;
  if (typeof v === "string") return Number(v.replace(/[^0-9.\-]/g, "")) || 0;
  return 0;
};

// Revenue Trend with date-range filter
const revenueState = { raw: [], chart: null };

function parseMonth(val) {
  // Accept YYYY-MM or date-like strings; fallback to NaN
  try {
    if (typeof val === "string" && /^\d{4}-\d{2}$/.test(val)) {
      const [y, m] = val.split("-").map(Number);
      return new Date(y, m - 1, 1).getTime();
    }
    const d = new Date(val);
    return isNaN(d.getTime()) ? NaN : d.getTime();
  } catch {
    return NaN;
  }
}

function renderRevenueChart(records) {
  const labels = records.map((d) => d.order_year_month ?? d.month ?? d.date ?? d.period ?? "");
  const values = records.map((d) => toNum(d.total_revenue ?? d.revenue ?? d.total ?? d.value ?? 0));
  const ctx = document.getElementById("revenueChart").getContext("2d");
  if (revenueState.chart) revenueState.chart.destroy();
  revenueState.chart = new Chart(ctx, {
    type: "line",
    data: {
      labels,
      datasets: [
        {
          label: "Revenue",
          data: values,
          borderColor: "#3b82f6",
          backgroundColor: "rgba(59,130,246,0.2)",
          tension: 0.3,
          fill: true,
        },
      ],
    },
    options: {
      responsive: true,
      plugins: {
        legend: { display: true },
        tooltip: { mode: "index", intersect: false },
      },
      scales: {
        y: { ticks: { callback: (val) => fmtNumber(val) } },
      },
    },
  });
}

function applyRevenueDateFilter() {
  const fromRaw = document.getElementById("rev-from").value;
  const toRaw = document.getElementById("rev-to").value;
  const fromTs = fromRaw ? parseMonth(fromRaw) : NaN;
  const toTs = toRaw ? parseMonth(toRaw) : NaN;
  let filtered = revenueState.raw;
  if (!isNaN(fromTs) || !isNaN(toTs)) {
    filtered = revenueState.raw.filter((r) => {
      const ts = parseMonth(r.order_year_month ?? r.month ?? r.date ?? r.period ?? "");
      if (isNaN(ts)) return false;
      if (!isNaN(fromTs) && ts < fromTs) return false;
      if (!isNaN(toTs) && ts > toTs) return false;
      return true;
    });
  }
  renderRevenueChart(filtered);
}

async function loadRevenue() {
  const statusEl = document.getElementById("rev-status");
  try {
    statusEl.textContent = "Loading...";
    const res = await fetch(`${API_BASE}/api/revenue`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    statusEl.textContent = "";
    revenueState.raw = data;
    renderRevenueChart(data);
    document.getElementById("rev-apply").addEventListener("click", applyRevenueDateFilter);
  } catch (err) {
    statusEl.textContent = "Failed to load revenue data.";
  }
}

// Category Breakdown
async function loadCategories() {
  const statusEl = document.getElementById("cat-status");
  try {
    statusEl.textContent = "Loading...";
    const res = await fetch(`${API_BASE}/api/categories`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    statusEl.textContent = "";
    // Expect keys like: category, revenue
    const labels = data.map((d) => d.category ?? d.name ?? "");
    const values = data.map((d) => toNum(d.total_revenue ?? d.revenue ?? d.total ?? d.value ?? 0));
    const ctx = document.getElementById("categoryChart").getContext("2d");
    new Chart(ctx, {
      type: "bar",
      data: {
        labels,
        datasets: [
          {
            label: "Revenue",
            data: values,
            backgroundColor: "#10b981",
          },
        ],
      },
      options: {
        responsive: true,
        plugins: {
          legend: { display: true },
          tooltip: { mode: "index", intersect: false },
        },
        scales: {
          y: {
            ticks: { callback: (val) => fmtNumber(val) },
          },
        },
      },
    });
  } catch (err) {
    statusEl.textContent = "Failed to load category data.";
  }
}

// Top Customers (sortable + search)
const customersState = {
  raw: [],
  filtered: [],
  sortKey: "total_spend",
  sortDir: "desc",
};

function renderCustomers() {
  const tbody = document.querySelector("#customers-table tbody");
  tbody.innerHTML = "";
  for (const row of customersState.filtered) {
    const tr = document.createElement("tr");
    const name = row.customer_name ?? row.customer ?? row.name ?? "";
    const region = row.region ?? row.customer_region ?? row.area ?? "";
    const spend = toNum(row.total_spend ?? row.spend ?? row.total ?? 0);
    const orders = toNum(row.order_count ?? row.orders ?? 0);
    const churn = row.churn_status ?? row.churned ?? row.churn ?? "";
    tr.innerHTML = `
      <td>${name}</td>
      <td>${region}</td>
      <td>${fmtNumber(spend)}</td>
      <td>${fmtNumber(orders)}</td>
      <td>${churn}</td>
    `;
    tbody.appendChild(tr);
  }
}

function applyCustomerFilters() {
  const q = document.getElementById("customer-search").value.trim().toLowerCase();
  customersState.filtered = customersState.raw.filter((row) => {
    const name = (row.customer_name ?? row.customer ?? row.name ?? "").toLowerCase();
    return q === "" || name.includes(q);
  });
  const key = customersState.sortKey;
  const dir = customersState.sortDir;
  customersState.filtered.sort((a, b) => {
    const av = a[key] ?? 0;
    const bv = b[key] ?? 0;
    if (typeof av === "string" || typeof bv === "string") {
      return dir === "asc" ? String(av).localeCompare(String(bv)) : String(bv).localeCompare(String(av));
    }
    return dir === "asc" ? av - bv : bv - av;
  });
  renderCustomers();
}

async function loadCustomers() {
  const statusEl = document.getElementById("cust-status");
  try {
    statusEl.textContent = "Loading...";
    const res = await fetch(`${API_BASE}/api/top-customers`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    statusEl.textContent = "";
    customersState.raw = data;
    applyCustomerFilters();
    document.getElementById("customer-search").addEventListener("input", applyCustomerFilters);
    document.querySelectorAll("#customers-table thead th").forEach((th) => {
      th.addEventListener("click", () => {
        const key = th.dataset.key;
        if (!key) return;
        if (customersState.sortKey === key) {
          customersState.sortDir = customersState.sortDir === "asc" ? "desc" : "asc";
        } else {
          customersState.sortKey = key;
          customersState.sortDir = "asc";
        }
        applyCustomerFilters();
      });
    });
  } catch (err) {
    statusEl.textContent = "Failed to load customers.";
  }
}

// Region Summary table
async function loadRegions() {
  const statusEl = document.getElementById("region-status");
  try {
    statusEl.textContent = "Loading...";
    const res = await fetch(`${API_BASE}/api/regions`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    statusEl.textContent = "";
    const tbody = document.querySelector("#regions-table tbody");
    tbody.innerHTML = "";
    for (const row of data) {
      const region = row.region ?? row.name ?? "";
      const revenue = toNum(row.total_revenue ?? row.revenue ?? row.total ?? 0);
      const orders = toNum(row.num_orders ?? row.orders ?? row.order_count ?? 0);
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>${region}</td>
        <td>${fmtNumber(revenue)}</td>
        <td>${fmtNumber(orders)}</td>
      `;
      tbody.appendChild(tr);
    }
  } catch (err) {
    statusEl.textContent = "Failed to load regions.";
  }
}

// Bootstrap
document.addEventListener("DOMContentLoaded", () => {
  loadRevenue();
  loadCategories();
  loadCustomers();
  loadRegions();
});
