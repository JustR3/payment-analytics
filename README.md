# Proton Payment Analytics

## Project Overview

This project demonstrates a comprehensive payment analytics solution built for the **Proton Data Analyst – Finance & Customer Payments** role. It analyzes subscription billing data to identify payment friction points, provider performance, and revenue risks using industry-standard tools and methodologies.

## Objective

Build a production-ready analytics pipeline that:
- Identifies payment failure patterns and friction points
- Analyzes provider and payment method performance
- Calculates Monthly Recurring Revenue (MRR) at risk
- Provides actionable insights through interactive Metabase dashboards
- Demonstrates proficiency in SQL, Python, data modeling, and BI tools

## Technology Stack

- **Data Processing**: Python 3.12+ (pandas, numpy, SQLAlchemy)
- **Package Management**: UV (modern Python package manager)
- **Database**: PostgreSQL 16
- **Business Intelligence**: Metabase (via Docker)
- **Version Control**: Git
- **Data Format**: Parquet (for processed data)

## Project Structure

```
payment-analytics/
├── data/
│   ├── raw/                    # Original subscription-billing.csv
│   └── processed/              # Cleaned and enriched parquet files
├── src/                        # Python data processing scripts
│   ├── 01_clean_data.py       # Data cleaning and standardization
│   └── 02_enrich_data.py      # Business context enrichment
├── scripts/                    # Utility and setup scripts
├── dashboards/                 # Dashboard screenshots and documentation
├── docker-compose.yml          # Metabase + PostgreSQL setup
├── pyproject.toml             # Python dependencies (UV)
└── README.md                  # This file
```

## Data Pipeline

### 1. Source Data
- **Dataset**: `subscription-billing.csv` (200 subscription records)
- **Fields**: subscription_id, customer details, plan information, payment status, billing cycle, failure reasons, retention metrics

### 2. Data Cleaning (`src/01_clean_data.py`)
- Parse and standardize date fields
- Ensure numeric types for amounts
- Create derived fields:
  - `is_success`: Boolean payment success indicator
  - `date`, `month`: Temporal dimensions
  - `txn_value_bucket`: Transaction size categorization

### 3. Data Enrichment (`src/02_enrich_data.py`)
Adds realistic Proton-like business context:
- **Payment Provider**: Maps payment methods to processors (Stripe, PayPal, CardDirect, Crypto)
- **Geographic Region**: Infers from email domains (CH, DE, FR, US, etc.)
- **Product Tier**: Maps to Proton products (MailPlus, DrivePlus, VPNPlus, Unlimited)
- **Processing Time**: Synthetic but realistic latency metrics
- **MRR at Risk**: Calculates revenue risk from failed payments
- **Failure Categorization**: Standardizes failure reasons

### 4. Database Loading
- PostgreSQL database with optimized schema
- Single `payments` table with proper indexes
- Ready for Metabase connection

## Key Metrics & KPIs

1. **Payment Success Rate**: `(successful_payments / total_payments) × 100`
2. **MRR at Risk**: Sum of monthly recurring revenue from failed/pending payments
3. **Provider Performance**: Success rates by payment provider
4. **Geographic Performance**: Success rates and volume by region
5. **High-Value Transaction Risk**: Failure rates for top-tier subscriptions
6. **Processing Time Impact**: Correlation between latency and success

## Metabase Dashboards

### Dashboard 1: Executive Overview
- Overall success rate trends
- Total MRR at risk
- Failure reason breakdown
- Month-over-month comparisons

### Dashboard 2: Provider Performance
- Success rates by payment provider
- Processing time analysis
- Failure reasons per provider
- Provider comparison table

### Dashboard 3: Geographic & Product Insights
- Success rates by region
- Product tier performance
- High-value transaction analysis
- Regional MRR at risk

### Dashboard 4: Operational Drill-Down
- Processing time distribution
- Time-of-day patterns
- Top failure combinations
- Detailed failure diagnostics

## Getting Started

### Prerequisites
- Python 3.10+
- UV package manager ([installation](https://github.com/astral-sh/uv))
- Docker & Docker Compose
- Git

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd payment-analytics
```

2. **Set up Python environment**
```bash
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e .
```

3. **Process the data**
```bash
python src/01_clean_data.py
python src/02_enrich_data.py
python src/03_load_to_db.py
```

4. **Start Metabase and PostgreSQL**
```bash
docker-compose up -d
```

5. **Access Metabase**
- Open browser: `http://localhost:3000`
- Complete initial setup
- Connect to PostgreSQL database (credentials in docker-compose.yml)
- Import dashboards or create your own

## Key Findings

*(To be populated after dashboard analysis)*

## Data Quality & Assumptions

### Assumptions Made:
1. **Geographic Inference**: Email domains used to infer customer regions
2. **Provider Mapping**: Payment methods mapped to likely processors
3. **Processing Time**: Synthetic but follows realistic distributions
4. **Product Mapping**: Plan names mapped to Proton product suite

### Data Quality:
- All dates validated and standardized
- Null values handled appropriately
- Outliers investigated and documented
- Referential integrity maintained

## Future Enhancements

- Real-time payment monitoring
- Predictive churn modeling
- Automated anomaly detection
- Integration with data quality tools (Great Expectations)
- Revenue recognition automation
- Multi-currency support

## Author

Created as a portfolio project demonstrating:
- Payment analytics expertise
- SQL and Python proficiency
- Dashboard design for financial stakeholders
- Understanding of SaaS billing and payment systems
- Data pipeline development

---

**Contact**: [Your Email]  
**LinkedIn**: [Your LinkedIn]  
**GitHub**: [Your GitHub]
