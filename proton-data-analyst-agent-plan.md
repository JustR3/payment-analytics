# PROTON PAYMENT ANALYTICS PROJECT PLAN
_For Sonnet 4.5 agentic execution in VS Code – Metabase + Python + SQL_  
_Note: Metabase will run locally via Docker and connect to a database with the enriched payment data._

## 0. PROJECT GOAL & CONTEXT
- Goal: Build a Metabase dashboard that analyzes payment friction (failures, providers, geo, MRR at risk) for the Proton “Data Analyst – Finance & Customer Payments” role.
- Deliverables:
  - Local Metabase instance connected to a DB with enriched payment data.
  - 3–4 dashboards with filters and clear business insights.
  - README explaining approach, assumptions, and key findings.

---

## 1. REPO & ENVIRONMENT SETUP
### 1.1 Create project structure
- Create repo folder `payment-analytics`.
- Inside, create:
  - `AGENT_PLAN.md` (this file).
  - `README.md` (project doc).
  - `data/raw/` (original dataset).
  - `data/processed/` (clean/enriched data).
  - `src/` (Python scripts).
  - `dashboards/` (screenshots, notes).
  - `.gitignore` (exclude large data, venv, etc.).
- Add minimal 'pyproject.toml' or `requirements.txt` listing core Python deps (pandas, numpy, sqlalchemy, db driver).

### 1.2 Document project intent in README
- Brief description of:
  - Proton role and why this project exists.
  - High-level pipeline: Kaggle data → enrichment → DB → Metabase dashboards.
  - Tech stack: Python + SQL + DB + Metabase (Docker).

---

## 2. DATA SOURCE & UNDERSTANDING
### 2.1 Select dataset
- Use public free dataset 'subscription-billing.csv' for subscription billing.
- Move CSV into `data/raw/`.

### 2.2 Data understanding (theoretical plan)
- Inspect columns: transaction id, timestamp, amount, type, status, etc.
- Identify:
  - Which fields can represent success/failure.
  - Which can be repurposed or extended for: provider, geo, product tier.
- Note assumptions (e.g., mapping certain transaction types to “subscription payments”).

---

## 3. DATA PREPARATION & ENRICHMENT
_All steps implemented in Python scripts under `src/`._

### 3.1 Clean & standardize data
- Input: `data/raw/...csv`
- Output: `data/processed/payments_clean.parquet`
- Tasks:
  - Parse timestamps into a unified datetime column.
  - Ensure numeric types for amounts.
  - Remove or flag obviously corrupt rows.
  - Add derived columns:
    - `date` (date only).
    - `month` (YYYY-MM).
    - `is_success` (boolean).
    - `txn_value_bucket` (small/medium/large by quantiles).

### 3.2 Add Proton-like business context
- Input: `payments_clean.parquet`
- Output: `payments_proton.parquet`
- Add synthetic but realistic dimensions:
  - `payment_provider` (e.g., Stripe, PayPal, CardDirect, Crypto) with defined probabilities.
  - `geo_region` (e.g., CH, DE, FR, NL, US, EU_other, ROW).
  - `product_tier` (e.g., MailPlus, DrivePlus, Unlimited, VPNPlus).
  - `subscription_type` (new, renewal, upgrade) inferred from patterns/assumptions.
  - `failure_reason` for failed transactions (card_declined, insufficient_funds, 3ds_abandon, network_timeout, fraud_block, expired_card).
  - `processing_time_s` (random but realistic distribution, then bucket into `<1s`, `1–3s`, `3–10s`, `>10s`).
- Compute business metrics:
  - `mrr_at_risk` for failed recurring payments (amount × 12 or similar rule).
  - `high_value_flag` for top X% transactions by amount.

### 3.3 Prepare DB-ready schema
- Define a logical table schema (field names and types) for a single `payments` table.
- Ensure column names are clean and consistent for Metabase use.

---

## 4. DATABASE & METABASE SETUP
### 4.1 Database
- Choose simple relational DB (e.g., PostgreSQL or SQLite) as Metabase source.
- Plan:
  - Create `payments` table with schema defined in 3.3.
  - Load `payments_proton.parquet`/CSV into this table.

### 4.2 Metabase via Docker
- Plan a simple Docker setup:
  - One container for Metabase.
  - One for the DB (if using Postgres).
- Configure:
  - Metabase pointing at the DB with the `payments` table.
  - Access via `http://localhost:3000` [web:65][web:83].

---

## 5. METABASE MODELING & QUESTIONS
### 5.1 Connect & model
- In Metabase:
  - Add the database connection.
  - Verify `payments` table appears.
  - Set appropriate field types (e.g., datetime, category).
  - Mark key fields (e.g., primary key, foreign key if any).

### 5.2 Core “questions” (reusable queries)
Define these logical questions (Metabase queries) to use in dashboards:

1. **Overall success rate over time**
   - Group by date, calculate success rate and volume.

2. **Failure reasons breakdown**
   - Count by `failure_reason`, sorted by count and MRR at risk.

3. **Provider performance**
   - For each `payment_provider`: success rate, avg amount, MRR at risk, processing time metrics.

4. **Geo-region performance**
   - Success rate and MRR at risk by `geo_region` and `product_tier`.

5. **High-value transaction risks**
   - Filter `high_value_flag = true`, show success vs failure counts and MRR at risk.

6. **Retry / recovery pattern** (if you model retries)
   - Success rate by `retry_attempts` value.

7. **Time-of-day / day-of-week patterns**
   - Heatmap-like aggregation on hour of day × day of week vs success rate.

Document each question: purpose, grouping fields, filters, metric(s).

---

## 6. DASHBOARD DESIGN (METABASE)
_Use Metabase dashboards as grouped “reports” built from the questions above [web:79]._

### 6.1 Dashboard 1 – Executive Overview
Goal: quick view for finance leadership.

Tiles:
- KPI cards:
  - Overall success rate (current period vs previous).
  - Total volume (current month).
  - Total MRR at risk from failed payments.
- Charts:
  - Success rate trend (line chart by date).
  - Failure reasons (bar or pie).
  - MRR at risk by failure reason (bar).

Filters (global):
- Date range.
- Payment provider.
- Geo-region.

### 6.2 Dashboard 2 – Provider Performance
Goal: compare Stripe/PayPal/CardDirect/Crypto.

Tiles:
- Table: one row per provider with:
  - Success rate.
  - Avg processing time bucket metrics.
  - MRR at risk.
- Charts:
  - Success rate over time by provider (multi-line).
  - Failures by reason per provider (stacked bar).

Filters:
- Date range.
- Product tier.
- Geo-region.

### 6.3 Dashboard 3 – Geographic & Product Insights
Goal: understand where and on what products friction is highest.

Tiles:
- Map or bar chart: success rate by `geo_region`.
- Funnel or bar: conversions by `product_tier`.
- Scatter or bar: high-value transaction failures by `geo_region`.

Filters:
- Date range.
- Payment provider.
- High-value only (boolean).

### 6.4 Dashboard 4 – Operational Drill-Down
Goal: help payment ops dig into root causes.

Tiles:
- Histogram: `processing_time_s` distribution and failure rate per bucket.
- Chart: success rate by `retry_attempts`.
- Heatmap: hour-of-day vs success rate.
- Table: top N failure combinations (provider × region × failure_reason) by MRR at risk.

Filters:
- Date range.
- Provider.
- Region.
- Product tier.

---

## 7. DOCUMENTATION & STORYTELLING
### 7.1 README content
- Sections:
  - Project overview.
  - Data source + enrichment logic (transparent about synthetic fields).
  - Key metrics and definitions (success rate, MRR at risk, etc.).
  - Summary of 3–5 main insights from dashboards.
  - How to run:
    - Install dependencies.
    - Start DB and Metabase.
    - Load data.
    - Open dashboards.

### 7.2 Application-facing summary
- Draft short paragraph for cover letter:
  - Mention analyzing millions of payment records.
  - Highlight 1–2 concrete friction insights (e.g., specific provider or failure reason).
  - Emphasize Metabase dashboards built for non-technical stakeholders.

---

## 8. EXECUTION ORDER FOR AGENT
1. Create repo structure (Section 1.1) and minimal README (1.2).
2. Download and place dataset in `data/raw/` (2.1).
3. Plan and implement data cleaning + enrichment as described (3.1, 3.2, 3.3).
4. Set up DB and load enriched data (4.1).
5. Run Metabase via Docker and connect DB (4.2).
6. In Metabase:
   - Configure fields and basic modeling (5.1).
   - Create core questions (5.2).
   - Build 4 dashboards with described tiles and filters (6.1–6.4).
7. Take screenshots and finalize README with findings (7.1).
8. Draft application summary text (7.2).

