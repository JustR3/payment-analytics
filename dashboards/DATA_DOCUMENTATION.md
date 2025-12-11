# Data Documentation

## Overview

This document describes the data pipeline, transformations, and synthetic field generation logic for the Proton Payment Analytics project.

---

## Data Pipeline

```
subscription-billing.csv (raw)
           ↓
    01_clean_data.py
           ↓
  payments_clean.parquet
           ↓
    02_enrich_data.py
           ↓
  payments_proton.parquet
           ↓
    03_load_to_db.py
           ↓
PostgreSQL: payments table (200 records, 40 columns)
           ↓
       Metabase
```

---

## Stage 1: Raw Data (subscription-billing.csv)

**Source**: Public subscription billing dataset  
**Records**: 200  
**Format**: CSV

### Original Fields (19 columns)

| Field | Type | Description |
|-------|------|-------------|
| subscription_id | String | Unique subscription identifier |
| customer_id | String | Customer identifier |
| customer_email | String | Customer email address |
| plan_id | String | Plan identifier |
| plan_name | String | Human-readable plan name |
| plan_price | Float | Subscription price |
| billing_cycle | String | monthly, quarterly, yearly, weekly |
| subscription_start_date | Date | When subscription began |
| next_renewal_date | Date | Next expected renewal |
| last_payment_date | Date | Most recent payment attempt |
| payment_status | String | success, failed, pending |
| payment_failure_reason | String | Reason for failure (if failed) |
| payment_method | String | credit_card, debit_card, paypal, bank_transfer, other |
| is_active | Boolean | Whether subscription is active |
| cancellation_date | Date | When subscription was cancelled (if any) |
| retention_status | String | retained, at-risk, churned |
| total_payments | Integer | Total payments made |
| failed_payments_count | Integer | Number of failed payments |
| last_retention_action_date | Date | Last retention effort |

### Data Quality Issues Found
- 5 records (2.5%) missing `last_payment_date` (likely pending/new subscriptions)
- 190 records (95%) missing `cancellation_date` (expected - most subscriptions active)
- 50 duplicate `subscription_id` values (customers with multiple subscriptions - valid)
- Some $0 or $0.01 prices (promotional/trial subscriptions - valid)

---

## Stage 2: Cleaned Data (payments_clean.parquet)

**Output**: `data/processed/payments_clean.parquet`  
**Records**: 200  
**Columns**: 30 (19 original + 11 derived)

### Derived Fields Added

| Field | Type | Derivation Logic |
|-------|------|------------------|
| date | Date | Extracted from `last_payment_date` |
| month | String | YYYY-MM format from `last_payment_date` |
| year | Integer | Year from `last_payment_date` |
| quarter | String | YYYY-Q format |
| day_of_week | String | Monday, Tuesday, etc. |
| hour | Integer | Hour of day (0-23) - set to 0 since raw data lacks time |
| is_success | Boolean | `True` if `payment_status == 'success'` |
| txn_value_bucket | Category | Quantile-based: Small (Q1), Medium (Q2), Large (Q3), Enterprise (Q4) |
| is_high_value | Boolean | `True` if `plan_price >= 90th percentile ($4,999.99)` |
| subscription_age_days | Integer | Days between `subscription_start_date` and `last_payment_date` |
| is_recurring | Boolean | `True` if `total_payments > 1` |

### Transformations
- All date fields parsed to datetime objects
- Numeric fields validated and converted
- Missing values preserved (not imputed)

---

## Stage 3: Enriched Data (payments_proton.parquet)

**Output**: `data/processed/payments_proton.parquet`  
**Records**: 200  
**Columns**: 40 (30 from Stage 2 + 10 synthetic)

### Synthetic Fields (Documented Logic)

All synthetic fields are created with transparent, reproducible logic. Seed set to 42 for reproducibility.

#### 1. payment_provider (String)

**Purpose**: Map generic payment methods to actual payment processors

**Logic**:
- `credit_card` → Stripe (60%), CardDirect (30%), Adyen (10%)
- `debit_card` → Stripe (50%), CardDirect (40%), Adyen (10%)
- `paypal` → PayPal (100%)
- `bank_transfer` → SEPA (60%), Wire (30%), ACH (10%)
- `other` → Crypto (70%), Other (30%)

**Rationale**: Realistic distribution based on European fintech market share

**Result**: Stripe (26.5%), PayPal (26%), CardDirect (14%), SEPA (11%), Wire (8.5%), Adyen (6%), Crypto (5%), ACH (1.5%), Other (1.5%)

#### 2. geo_region (String)

**Purpose**: Infer customer geographic location

**Logic**:
- Parse email domain
- Match against known country domains:
  - `.de`, `web.de`, `t-online.de` → DE
  - `.fr`, `orange.fr` → FR
  - `.ch`, `bluewin.ch`, `protonmail.com` → CH
  - `.com`, `gmail.com`, `outlook.com`, etc. → US
  - `.jp`, `.sg`, `.au`, etc. → respective countries
- Default to 'Other' if no match

**Rationale**: Email domain is a strong geographic signal

**Result**: US (50%), DE (5.5%), ES (4.5%), CH (4%), etc.

#### 3. product_tier (String)

**Purpose**: Map generic plan names to Proton product suite

**Logic**:
- `Monthly Basic` → Mail Plus
- `Quarterly Standard` → Drive Plus
- `Quarterly Premium` → Unlimited
- `Yearly Lite` → VPN Plus
- `Weekly Access/Student` → VPN Plus
- `Yearly Enterprise` → Proton for Business
- Unmapped → Other

**Rationale**: Align with Proton's actual product lineup

**Result**: Mail Plus (34%), VPN Plus (20%), Proton for Business (16.5%), Drive Plus (14%), Unlimited (12%), Other (3.5%)

#### 4. processing_time_s (Float)

**Purpose**: Simulate realistic payment processing latency

**Logic**:
```python
if payment_method in ['credit_card', 'debit_card']:
    base_time = lognormal(μ=0.5, σ=0.6)  # ~1-3s
elif payment_method == 'paypal':
    base_time = lognormal(μ=1.0, σ=0.5)  # ~2-5s
elif payment_method == 'bank_transfer':
    base_time = lognormal(μ=2.0, σ=0.7)  # ~5-30s
elif payment_method == 'other':
    base_time = lognormal(μ=2.5, σ=0.8)  # ~10-60s

if not is_success:
    base_time *= random(1.5, 3.0)  # Failed payments take longer
```

**Rationale**: 
- Lognormal distribution matches real-world latency patterns
- Card payments fastest (online, real-time)
- Bank transfers slower (async processing)
- Failed payments encounter timeouts and retries

**Result**: Mean 6.62s, Median 3.65s, 95th percentile 24.61s

#### 5. processing_time_bucket (Category)

**Purpose**: Categorize processing times for analysis

**Logic**:
- `<1s`: 0-1 seconds
- `1-3s`: 1-3 seconds
- `3-10s`: 3-10 seconds
- `>10s`: >10 seconds

**Result**: <1s (6.5%), 1-3s (35.5%), 3-10s (41.5%), >10s (16.5%)

#### 6. mrr_at_risk (Float)

**Purpose**: Calculate monthly recurring revenue at risk from failures

**Logic**:
```python
if is_success or not is_active:
    mrr = 0
elif billing_cycle == 'monthly':
    mrr = plan_price
elif billing_cycle == 'quarterly':
    mrr = plan_price / 3
elif billing_cycle == 'yearly':
    mrr = plan_price / 12
elif billing_cycle == 'weekly':
    mrr = plan_price * 4.33  # avg weeks/month
```

**Rationale**: Standardize all billing cycles to monthly recurring value

**Result**: Total MRR at risk: $624.95 across 41 subscriptions

#### 7. failure_reason_std (String)

**Purpose**: Standardize failure reasons into categories

**Logic**:
```
Raw Reason                      → Standardized
"Insufficient funds"            → insufficient_funds
"Card expired"                  → card_expired
"Card declined"                 → card_declined
"Payment gateway error"         → gateway_error
"Awaiting bank authorization"   → pending_authorization
"Processing delay"              → processing_delay
"Bank account closed"           → account_closed
(successful payment)            → none
```

**Rationale**: Consistent categorization for analysis and alerting

**Result**: insufficient_funds (31.2%), card_expired (31.2%), gateway_error (15.6%), pending_authorization (12.5%)

#### 8. failure_severity (String)

**Purpose**: Classify failure severity for prioritization

**Logic**:
- `critical`: account_closed (permanent, requires customer action)
- `high`: insufficient_funds, card_expired, card_declined (fixable by customer)
- `medium`: gateway_error (technical, may resolve)
- `low`: processing_delay, pending_authorization (temporary state)

**Rationale**: Prioritize retention efforts based on recoverability

#### 9. subscription_type (String)

**Purpose**: Categorize subscription lifecycle stage

**Logic**:
```python
if total_payments <= 1:
    return 'new'
elif is_active:
    return 'renewal'
else:
    return 'churned'
```

**Rationale**: Simple heuristic based on payment history

**Result**: renewal (66%), new (33%), churned (1%)

#### 10. retry_attempts (Integer)

**Purpose**: Track payment retry behavior

**Logic**:
```python
if payment_status == 'failed':
    return random_choice([1, 2, 3], p=[0.5, 0.3, 0.2])
else:
    return 0
```

**Rationale**: 
- Most failures caught on 1st retry
- Decreasing probability of multiple retries
- Success/pending have no retries

**Result**: 0 retries (84.5%), 1 retry (6.5%), 2 retries (2%), 3 retries (7%)

---

## Stage 4: Database (PostgreSQL)

**Database**: payments_analytics  
**Table**: payments  
**Records**: 200  
**Columns**: 40

### Indexes Created

For optimal Metabase query performance:

```sql
CREATE INDEX idx_payment_status ON payments(payment_status);
CREATE INDEX idx_payment_provider ON payments(payment_provider);
CREATE INDEX idx_geo_region ON payments(geo_region);
CREATE INDEX idx_product_tier ON payments(product_tier);
CREATE INDEX idx_date ON payments(date);
CREATE INDEX idx_month ON payments(month);
CREATE INDEX idx_is_success ON payments(is_success);
CREATE INDEX idx_is_high_value ON payments(is_high_value);
CREATE INDEX idx_failure_reason ON payments(failure_reason_std);
CREATE INDEX idx_customer_id ON payments(customer_id);
CREATE INDEX idx_subscription_id ON payments(subscription_id);
```

**Rationale**: Indexes on frequently filtered/grouped columns

---

## Key Metrics

### Payment Success Rate
**Calculation**: `(COUNT(is_success = true) / COUNT(*)) * 100`  
**Current Value**: 77.5%  
**Benchmark**: Industry average is 80-85%

### MRR at Risk
**Calculation**: `SUM(mrr_at_risk WHERE payment_status != 'success')`  
**Current Value**: $624.95  
**Affected Subscriptions**: 41 (20.5% of total)

### High-Value Transactions
**Definition**: Transactions in top 10% by value (≥$4,999.99)  
**Count**: 21 transactions  
**Success Rate**: Similar to overall (~77%)

---

## Data Quality & Assumptions

### Validated Aspects
✓ All dates parsed successfully  
✓ Numeric fields have valid ranges  
✓ No unexpected null values in critical fields  
✓ Referential integrity maintained  
✓ Indexes created successfully  

### Known Limitations
⚠ Time component missing (all payments at midnight)  
⚠ Geographic inference based on email domain only  
⚠ Processing time is synthetic (not measured)  
⚠ Retry attempts are synthetic (not tracked in source)  

### Assumptions Made
1. **Email domain → Geography**: Valid approximation for B2C
2. **Payment method → Provider**: Based on European market patterns
3. **Plan names → Products**: Manual mapping based on Proton docs
4. **MRR calculation**: Standard SaaS methodology
5. **Failure categorization**: Aligned with industry standards

---

## Future Enhancements

### Data Quality
- [ ] Add Great Expectations validation suite
- [ ] Implement schema evolution tracking
- [ ] Add data lineage documentation
- [ ] Monitor for data drift

### Enrichment
- [ ] Add IP geolocation (if available)
- [ ] Include payment processor webhook data
- [ ] Add retry timing details
- [ ] Include 3DS authentication status

### Metrics
- [ ] Customer Lifetime Value (CLV)
- [ ] Cohort analysis by signup date
- [ ] Churn prediction scores
- [ ] Payment velocity metrics

---

## References

- **SaaS Metrics**: [Chargebee SaaS Metrics Guide](https://www.chargebee.com/resources/glossaries/saas-metrics/)
- **Payment Analytics**: Stripe Atlas payment failure patterns
- **Geographic Inference**: Email domain standards (ICANN)

