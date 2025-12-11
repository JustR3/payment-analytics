# Metabase Setup Guide

## Initial Setup

### 1. Start the Services

```bash
# Start both PostgreSQL and Metabase
docker-compose up -d

# Check that services are running
docker-compose ps
```

### 2. Access Metabase

- Open your browser and navigate to: `http://localhost:3000`
- Wait for Metabase to finish initializing (first startup takes 1-2 minutes)

### 3. Complete Initial Metabase Setup

#### Step 1: Language & Email
- **Language**: Select English (or your preference)
- **First name**: Your name
- **Email**: Your email
- **Company/Team name**: Proton Payment Analytics
- **Password**: Create a secure password

#### Step 2: Add Database Connection

Configure the PostgreSQL connection:

- **Database type**: PostgreSQL
- **Display name**: Payment Analytics Database
- **Host**: `postgres` (Docker container name)
  - If connecting from your local machine (outside Docker), use: `localhost`
- **Port**: `5432`
- **Database name**: `payments_analytics`
- **Username**: `proton`
- **Password**: `proton_analytics_2024`
- **Schema**: Leave empty (will use public schema)

Click "Connect database" and wait for Metabase to sync the schema.

#### Step 3: Usage Data Preference
- Choose whether to share anonymous usage data (optional)

#### Step 4: Complete Setup
- Click "Take me to Metabase"

---

## Database Schema Overview

The `payments` table contains **40 columns** with **200 records**:

### Key Business Metrics
- `is_success` - Payment success indicator
- `mrr_at_risk` - Monthly recurring revenue at risk
- `payment_status` - success, failed, pending
- `plan_price` - Subscription price
- `billing_cycle` - monthly, quarterly, yearly, weekly

### Enriched Dimensions
- `payment_provider` - Stripe, PayPal, CardDirect, etc.
- `geo_region` - Customer geographic region (US, DE, CH, etc.)
- `product_tier` - Mail Plus, VPN Plus, Unlimited, etc.
- `processing_time_s` - Payment processing latency
- `failure_reason_std` - Standardized failure categories

### Temporal Fields
- `date` - Payment date
- `month` - YYYY-MM format
- `quarter` - Quarterly grouping
- `day_of_week` - Monday, Tuesday, etc.
- `hour` - Hour of day (0-23)

---

## Creating Your First Question

### Example 1: Overall Payment Success Rate

1. Click "New" → "Question"
2. Select "Simple question"
3. Choose "Payment Analytics Database" → "Payments" table
4. Click "Summarize"
5. Select "Count of rows"
6. Group by: `payment_status`
7. Click "Visualize"
8. Change visualization to "Pie chart"
9. Save as "Payment Status Distribution"

### Example 2: MRR at Risk by Provider

1. Click "New" → "Question"
2. Select "Simple question"
3. Choose "Payments" table
4. Click "Summarize"
5. Select "Sum of" → `mrr_at_risk`
6. Group by: `payment_provider`
7. Filter: `is_success` = false
8. Sort by: Sum of mrr_at_risk descending
9. Change visualization to "Bar chart"
10. Save as "MRR at Risk by Provider"

### Example 3: Success Rate Over Time

1. Click "New" → "Question"
2. Choose "Payments" table
3. Click "Custom column" and create:
   - Name: `Success Rate`
   - Formula: `case([Is Success] = true, 1, 0)`
4. Click "Summarize"
5. Select "Average of" → `Success Rate`
6. Group by: `Month`
7. Change visualization to "Line chart"
8. Format Y-axis as percentage
9. Save as "Monthly Success Rate Trend"

---

## SQL Query Examples

For more complex analysis, use Metabase's SQL editor:

### Success Rate by Product Tier and Region

```sql
SELECT 
    product_tier,
    geo_region,
    COUNT(*) as total_transactions,
    SUM(CASE WHEN is_success THEN 1 ELSE 0 END) as successful,
    ROUND(AVG(CASE WHEN is_success THEN 1 ELSE 0 END) * 100, 2) as success_rate_pct,
    ROUND(SUM(mrr_at_risk), 2) as total_mrr_at_risk
FROM payments
GROUP BY product_tier, geo_region
HAVING COUNT(*) >= 5
ORDER BY success_rate_pct ASC;
```

### Processing Time Impact on Success

```sql
SELECT 
    processing_time_bucket,
    COUNT(*) as transactions,
    ROUND(AVG(CASE WHEN is_success THEN 1 ELSE 0 END) * 100, 2) as success_rate_pct,
    ROUND(AVG(processing_time_s), 2) as avg_processing_time
FROM payments
GROUP BY processing_time_bucket
ORDER BY 
    CASE processing_time_bucket
        WHEN '<1s' THEN 1
        WHEN '1-3s' THEN 2
        WHEN '3-10s' THEN 3
        WHEN '>10s' THEN 4
    END;
```

### Top Failure Reasons with MRR Impact

```sql
SELECT 
    failure_reason_std,
    failure_severity,
    COUNT(*) as failure_count,
    ROUND(SUM(mrr_at_risk), 2) as total_mrr_at_risk,
    ROUND(AVG(mrr_at_risk), 2) as avg_mrr_at_risk,
    STRING_AGG(DISTINCT payment_provider, ', ') as affected_providers
FROM payments
WHERE failure_reason_std != 'none'
GROUP BY failure_reason_std, failure_severity
ORDER BY total_mrr_at_risk DESC;
```

### High-Value Transaction Analysis

```sql
SELECT 
    product_tier,
    payment_provider,
    COUNT(*) as total_high_value_txns,
    SUM(CASE WHEN is_success THEN 1 ELSE 0 END) as successful,
    ROUND(AVG(CASE WHEN is_success THEN 1 ELSE 0 END) * 100, 2) as success_rate_pct,
    ROUND(AVG(plan_price), 2) as avg_transaction_value,
    ROUND(SUM(mrr_at_risk), 2) as mrr_at_risk
FROM payments
WHERE is_high_value = true
GROUP BY product_tier, payment_provider
ORDER BY mrr_at_risk DESC;
```

---

## Dashboard Recommendations

### Dashboard 1: Executive Overview
**Purpose**: Quick snapshot for leadership

**Widgets**:
1. **KPI Card**: Overall success rate (%)
2. **KPI Card**: Total MRR at risk ($)
3. **KPI Card**: Total transactions (count)
4. **Line Chart**: Success rate trend by month
5. **Pie Chart**: Failure reasons distribution
6. **Bar Chart**: MRR at risk by failure reason

**Filters**:
- Date range
- Payment provider
- Geographic region

### Dashboard 2: Provider Performance
**Purpose**: Compare payment provider effectiveness

**Widgets**:
1. **Table**: Provider comparison (success rate, avg processing time, MRR at risk)
2. **Line Chart**: Success rate over time by provider
3. **Bar Chart**: Failure count by provider
4. **Stacked Bar**: Failure reasons by provider

**Filters**:
- Date range
- Product tier
- Geographic region

### Dashboard 3: Geographic & Product Insights
**Purpose**: Identify regional and product-specific issues

**Widgets**:
1. **Bar Chart**: Success rate by geographic region
2. **Table**: Product tier performance
3. **Scatter Plot**: Transaction value vs success rate
4. **Map** (if enabled): Regional distribution

**Filters**:
- Date range
- Payment provider
- High-value only toggle

### Dashboard 4: Operational Deep Dive
**Purpose**: Technical analysis for payment ops team

**Widgets**:
1. **Histogram**: Processing time distribution
2. **Bar Chart**: Success rate by processing time bucket
3. **Table**: Top failure combinations (provider × region × reason)
4. **Line Chart**: Hourly success rate pattern

**Filters**:
- Date range
- Provider
- Region
- Product tier

---

## Tips for Effective Dashboards

### 1. Use Appropriate Visualizations
- **Trends over time**: Line charts
- **Comparisons**: Bar charts
- **Proportions**: Pie charts (max 5 categories)
- **Distributions**: Histograms
- **Multi-dimensional**: Tables with conditional formatting

### 2. Add Context
- Include target/benchmark lines (e.g., 95% success rate target)
- Use colors meaningfully (red for failures, green for success)
- Add text cards to explain key insights

### 3. Optimize Performance
- Use date filters to limit data range
- Create summary tables for large datasets
- Use indexes (already created in our database)

### 4. Make it Actionable
- Link to detailed drill-down reports
- Include "What to do about this" text cards
- Highlight outliers and anomalies

---

## Troubleshooting

### Can't connect to database
- Ensure Docker containers are running: `docker-compose ps`
- Check PostgreSQL logs: `docker-compose logs postgres`
- Verify network: `docker network ls`

### Metabase not loading
- Wait 2 minutes for initial startup
- Check Metabase logs: `docker-compose logs metabase`
- Restart: `docker-compose restart metabase`

### Data not appearing
- Verify data was loaded: `docker-compose exec postgres psql -U proton -d payments_analytics -c "SELECT COUNT(*) FROM payments;"`
- Re-sync database in Metabase: Settings → Admin → Databases → Payment Analytics Database → Sync

### Slow queries
- Check indexes exist: Run `\di` in psql
- Limit date ranges in dashboard filters
- Use materialized views for complex aggregations

---

## Next Steps

1. **Explore the data** using Metabase's data browser
2. **Create the 4 recommended dashboards** (or customize to your needs)
3. **Set up email subscriptions** for daily/weekly dashboard snapshots
4. **Add alerts** for MRR at risk exceeding thresholds
5. **Document key findings** in the main README

---

## Resources

- [Metabase Documentation](https://www.metabase.com/docs/latest/)
- [SQL Tutorial](https://www.metabase.com/learn/sql-questions/)
- [Dashboard Best Practices](https://www.metabase.com/learn/dashboards/)

