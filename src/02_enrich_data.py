#!/usr/bin/env python3
"""
Data Enrichment with Proton-like Business Context
==================================================

This script enriches the cleaned payment data with synthetic but realistic
business dimensions relevant to Proton's payment analytics needs:

1. Payment Provider: Map payment methods to actual payment processors
2. Geographic Region: Infer from email domains and customer distribution
3. Product Tier: Map to Proton product suite
4. Processing Time: Add realistic payment processing latency
5. MRR at Risk: Calculate monthly recurring revenue at risk
6. Failure Reason Standardization: Categorize and standardize failure reasons

All synthetic data generation is documented with clear logic and assumptions.

Input: data/processed/payments_clean.parquet
Output: data/processed/payments_proton.parquet
"""

import pandas as pd
import numpy as np
from pathlib import Path

# Set random seed for reproducibility
np.random.seed(42)

# File paths
BASE_DIR = Path(__file__).parent.parent
INPUT_FILE = BASE_DIR / 'data' / 'processed' / 'payments_clean.parquet'
OUTPUT_FILE = BASE_DIR / 'data' / 'processed' / 'payments_proton.parquet'

# Configuration for synthetic data generation
PAYMENT_PROVIDERS = {
    'credit_card': {
        'Stripe': 0.60,
        'CardDirect': 0.30,
        'Adyen': 0.10,
    },
    'debit_card': {
        'Stripe': 0.50,
        'CardDirect': 0.40,
        'Adyen': 0.10,
    },
    'paypal': {
        'PayPal': 1.0,
    },
    'bank_transfer': {
        'SEPA': 0.60,
        'Wire': 0.30,
        'ACH': 0.10,
    },
    'other': {
        'Crypto': 0.70,
        'Other': 0.30,
    }
}

# Geographic regions inferred from email domains
EMAIL_DOMAIN_TO_REGION = {
    # European domains
    '.de': 'DE',
    '.fr': 'FR',
    '.it': 'IT',
    '.es': 'ES',
    '.ch': 'CH',
    '.nl': 'NL',
    '.pt': 'PT',
    '.uk': 'GB',
    '.ie': 'IE',
    '.dk': 'DK',
    '.at': 'AT',
    '.be': 'BE',
    't-online.de': 'DE',
    'web.de': 'DE',
    'orange.fr': 'FR',
    'libero.it': 'IT',
    'bluewin.ch': 'CH',
    
    # Americas
    '.com': 'US',
    '.us': 'US',
    '.ca': 'CA',
    '.mx': 'MX',
    '.br': 'BR',
    '.ar': 'AR',
    '.cl': 'CL',
    '.co': 'CO',
    '.pe': 'PE',
    'gmail.com': 'US',
    'outlook.com': 'US',
    'yahoo.com': 'US',
    'hotmail.com': 'US',
    'aol.com': 'US',
    'icloud.com': 'US',
    'fastmail.com': 'US',
    'protonmail.com': 'CH',
    
    # Asia Pacific
    '.jp': 'JP',
    '.sg': 'SG',
    '.au': 'AU',
    '.nz': 'NZ',
    '.kr': 'KR',
    '.cn': 'CN',
    '.in': 'IN',
    '.vn': 'VN',
    'naver.com': 'KR',
    '163.com': 'CN',
    
    # Russia & Eastern Europe
    '.ru': 'RU',
    'rambler.ru': 'RU',
    
    # Others
    '.edu': 'US',
    '.ma': 'MA',
    '.za': 'ZA',
}

# Proton product mapping based on plan characteristics
PRODUCT_TIER_MAPPING = {
    'Monthly Basic': 'Mail Plus',
    'Quarterly Standard': 'Drive Plus',
    'Quarterly Premium': 'Unlimited',
    'Yearly Lite': 'VPN Plus',
    'Yearly Enterprise': 'Proton for Business',
    'Weekly Access': 'VPN Plus',
    'Weekly Student': 'VPN Plus',
    'Weekly Lite Plan': 'VPN Plus',
    'Monthly Basic Plan': 'Mail Plus',
    'Quarterly Standard Plan': 'Drive Plus',
    'Quarterly Premium Plan': 'Unlimited',
    'Yearly Lite Plan': 'VPN Plus',
    'Yearly Enterprise Plan': 'Proton for Business',
}

# Standardized failure reasons
FAILURE_REASON_MAPPING = {
    'Insufficient funds': 'insufficient_funds',
    'Insufficient funds on account': 'insufficient_funds',
    'Card expired': 'card_expired',
    'Card declined': 'card_declined',
    'Payment gateway error': 'gateway_error',
    'Awaiting bank authorization': 'pending_authorization',
    'Awaiting confirmation': 'pending_authorization',
    'Processing delay': 'processing_delay',
    'Bank account closed': 'account_closed',
}


def load_clean_data():
    """Load the cleaned data"""
    print(f"Loading cleaned data from {INPUT_FILE}...")
    df = pd.read_parquet(INPUT_FILE)
    print(f"Loaded {len(df):,} records")
    return df


def add_payment_provider(df):
    """
    Map payment methods to actual payment providers.
    
    Logic:
    - credit_card -> Stripe (60%), CardDirect (30%), Adyen (10%)
    - debit_card -> Stripe (50%), CardDirect (40%), Adyen (10%)
    - paypal -> PayPal (100%)
    - bank_transfer -> SEPA (60%), Wire (30%), ACH (10%)
    - other -> Crypto (70%), Other (30%)
    """
    print("\nAdding payment provider...")
    
    def assign_provider(payment_method):
        if pd.isna(payment_method):
            return 'Unknown'
        
        providers = PAYMENT_PROVIDERS.get(payment_method, {'Unknown': 1.0})
        provider_list = list(providers.keys())
        probabilities = list(providers.values())
        
        return np.random.choice(provider_list, p=probabilities)
    
    df['payment_provider'] = df['payment_method'].apply(assign_provider)
    
    print("  Provider distribution:")
    for provider, count in df['payment_provider'].value_counts().items():
        pct = (count / len(df)) * 100
        print(f"    - {provider}: {count:,} ({pct:.1f}%)")
    
    return df


def add_geographic_region(df):
    """
    Infer geographic region from email domain.
    
    Logic:
    - Parse email domain and match against known patterns
    - Default to 'Other' if no match found
    """
    print("\nAdding geographic region...")
    
    def infer_region(email):
        if pd.isna(email):
            return 'Other'
        
        email_lower = email.lower()
        
        # Check each domain pattern
        for domain, region in EMAIL_DOMAIN_TO_REGION.items():
            if domain in email_lower:
                return region
        
        return 'Other'
    
    df['geo_region'] = df['customer_email'].apply(infer_region)
    
    print("  Region distribution:")
    for region, count in df['geo_region'].value_counts().head(10).items():
        pct = (count / len(df)) * 100
        print(f"    - {region}: {count:,} ({pct:.1f}%)")
    
    return df


def add_product_tier(df):
    """
    Map plan names to Proton product tiers.
    
    Logic:
    - Map based on plan_name to Proton products:
      - Basic -> Mail Plus
      - Standard -> Drive Plus
      - Premium -> Unlimited
      - Lite/Weekly -> VPN Plus
      - Enterprise -> Proton for Business
    """
    print("\nAdding product tier...")
    
    df['product_tier'] = df['plan_name'].map(PRODUCT_TIER_MAPPING)
    df['product_tier'].fillna('Other', inplace=True)
    
    print("  Product distribution:")
    for product, count in df['product_tier'].value_counts().items():
        pct = (count / len(df)) * 100
        print(f"    - {product}: {count:,} ({pct:.1f}%)")
    
    return df


def add_processing_time(df):
    """
    Add realistic payment processing time.
    
    Logic:
    - Payment method affects processing time:
      - credit_card/debit_card: 0.5-3s (fast, online)
      - paypal: 1-5s (moderate, redirect)
      - bank_transfer: 5-30s (slow, async)
      - crypto: 10-60s (very slow, blockchain)
    - Failed payments tend to have longer processing times
    """
    print("\nAdding processing time...")
    
    def generate_processing_time(row):
        payment_method = row['payment_method']
        is_success = row['is_success']
        
        # Base processing time by method (in seconds)
        if payment_method in ['credit_card', 'debit_card']:
            base_time = np.random.lognormal(0.5, 0.6)  # ~1-3s
        elif payment_method == 'paypal':
            base_time = np.random.lognormal(1.0, 0.5)  # ~2-5s
        elif payment_method == 'bank_transfer':
            base_time = np.random.lognormal(2.0, 0.7)  # ~5-30s
        elif payment_method == 'other':
            base_time = np.random.lognormal(2.5, 0.8)  # ~10-60s
        else:
            base_time = np.random.lognormal(1.0, 0.5)
        
        # Failed payments take longer (timeout, retries)
        if not is_success:
            base_time *= np.random.uniform(1.5, 3.0)
        
        return round(base_time, 2)
    
    df['processing_time_s'] = df.apply(generate_processing_time, axis=1)
    
    # Create processing time buckets
    df['processing_time_bucket'] = pd.cut(
        df['processing_time_s'],
        bins=[0, 1, 3, 10, float('inf')],
        labels=['<1s', '1-3s', '3-10s', '>10s'],
        include_lowest=True
    )
    
    print(f"  Processing time stats:")
    print(f"    - Mean: {df['processing_time_s'].mean():.2f}s")
    print(f"    - Median: {df['processing_time_s'].median():.2f}s")
    print(f"    - 95th percentile: {df['processing_time_s'].quantile(0.95):.2f}s")
    print(f"  Processing time buckets:")
    for bucket, count in df['processing_time_bucket'].value_counts().sort_index().items():
        pct = (count / len(df)) * 100
        print(f"    - {bucket}: {count:,} ({pct:.1f}%)")
    
    return df


def calculate_mrr_at_risk(df):
    """
    Calculate Monthly Recurring Revenue at risk from failed/pending payments.
    
    Logic:
    - For failed/pending recurring payments (total_payments > 0):
      - Monthly: MRR = plan_price
      - Quarterly: MRR = plan_price / 3
      - Yearly: MRR = plan_price / 12
      - Weekly: MRR = plan_price * 4.33 (avg weeks per month)
    - Only applies to is_active subscriptions
    """
    print("\nCalculating MRR at risk...")
    
    def calculate_mrr(row):
        if row['is_success'] or not row['is_active']:
            return 0.0
        
        price = row['plan_price']
        cycle = row['billing_cycle']
        
        if cycle == 'monthly':
            return price
        elif cycle == 'quarterly':
            return price / 3
        elif cycle == 'yearly':
            return price / 12
        elif cycle == 'weekly':
            return price * 4.33  # avg weeks per month
        else:
            return 0.0
    
    df['mrr_at_risk'] = df.apply(calculate_mrr, axis=1).round(2)
    
    total_at_risk = df['mrr_at_risk'].sum()
    affected_subs = (df['mrr_at_risk'] > 0).sum()
    
    print(f"  Total MRR at risk: ${total_at_risk:,.2f}")
    print(f"  Affected subscriptions: {affected_subs:,}")
    
    return df


def standardize_failure_reasons(df):
    """
    Standardize and categorize failure reasons.
    
    Logic:
    - Map raw failure reasons to standardized categories
    - Add severity level (critical, high, medium, low)
    """
    print("\nStandardizing failure reasons...")
    
    df['failure_reason_std'] = df['payment_failure_reason'].map(FAILURE_REASON_MAPPING)
    df['failure_reason_std'].fillna('none', inplace=True)
    
    # Assign severity levels
    severity_map = {
        'insufficient_funds': 'high',
        'card_expired': 'high',
        'card_declined': 'high',
        'account_closed': 'critical',
        'gateway_error': 'medium',
        'processing_delay': 'low',
        'pending_authorization': 'low',
        'none': 'none',
    }
    
    df['failure_severity'] = df['failure_reason_std'].map(severity_map)
    
    print("  Standardized failure reasons:")
    failed_df = df[df['failure_reason_std'] != 'none']
    for reason, count in failed_df['failure_reason_std'].value_counts().items():
        pct = (count / len(failed_df)) * 100 if len(failed_df) > 0 else 0
        print(f"    - {reason}: {count:,} ({pct:.1f}%)")
    
    return df


def add_subscription_type(df):
    """
    Infer subscription type (new, renewal, upgrade).
    
    Logic:
    - new: total_payments <= 1
    - renewal: total_payments > 1 and same customer/plan pattern
    - upgrade: customers with multiple active subscriptions
    """
    print("\nInferring subscription type...")
    
    # Simple logic: based on payment count
    def infer_type(row):
        if row['total_payments'] <= 1:
            return 'new'
        elif row['is_active']:
            return 'renewal'
        else:
            return 'churned'
    
    df['subscription_type'] = df.apply(infer_type, axis=1)
    
    print("  Subscription type distribution:")
    for sub_type, count in df['subscription_type'].value_counts().items():
        pct = (count / len(df)) * 100
        print(f"    - {sub_type}: {count:,} ({pct:.1f}%)")
    
    return df


def add_retry_attempts(df):
    """
    Add synthetic retry attempt count for failed payments.
    
    Logic:
    - Failed payments: 1-3 retry attempts (weighted towards fewer retries)
    - Pending payments: 0 retries (awaiting first response)
    - Success payments: 0 retries (worked first time)
    """
    print("\nAdding retry attempts...")
    
    def assign_retries(payment_status):
        if payment_status == 'failed':
            return np.random.choice([1, 2, 3], p=[0.5, 0.3, 0.2])
        elif payment_status == 'pending':
            return 0
        else:  # success
            return 0
    
    df['retry_attempts'] = df['payment_status'].apply(assign_retries)
    
    print(f"  Retry attempts distribution:")
    for retries, count in df['retry_attempts'].value_counts().sort_index().items():
        pct = (count / len(df)) * 100
        print(f"    - {retries} retries: {count:,} ({pct:.1f}%)")
    
    return df


def save_enriched_data(df):
    """Save enriched data to parquet"""
    print(f"\nSaving enriched data to {OUTPUT_FILE}...")
    
    # Ensure output directory exists
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    # Save to parquet
    df.to_parquet(OUTPUT_FILE, index=False, engine='pyarrow')
    
    file_size = OUTPUT_FILE.stat().st_size / 1024  # KB
    print(f"Saved {len(df):,} records with {len(df.columns)} columns ({file_size:.1f} KB)")
    
    # Save sample CSV
    sample_csv = OUTPUT_FILE.parent / 'payments_proton_sample.csv'
    df.head(100).to_csv(sample_csv, index=False)
    print(f"Saved sample (100 rows) to {sample_csv}")
    
    # Print column list
    print(f"\n  Final columns ({len(df.columns)}):")
    for i, col in enumerate(df.columns, 1):
        print(f"    {i:2d}. {col}")


def main():
    """Main execution flow"""
    print("=" * 70)
    print("PAYMENT DATA ENRICHMENT - PROTON BUSINESS CONTEXT")
    print("=" * 70)
    
    # Load cleaned data
    df = load_clean_data()
    
    # Add enrichments
    df = add_payment_provider(df)
    df = add_geographic_region(df)
    df = add_product_tier(df)
    df = add_processing_time(df)
    df = calculate_mrr_at_risk(df)
    df = standardize_failure_reasons(df)
    df = add_subscription_type(df)
    df = add_retry_attempts(df)
    
    # Save enriched data
    save_enriched_data(df)
    
    print("\n" + "=" * 70)
    print("✓ Data enrichment completed successfully!")
    print("=" * 70)
    print("\nSynthetic fields added (with documented logic):")
    print("  1. payment_provider - Mapped from payment_method")
    print("  2. geo_region - Inferred from email domain")
    print("  3. product_tier - Mapped from plan_name to Proton products")
    print("  4. processing_time_s - Realistic latency based on method")
    print("  5. processing_time_bucket - Categorized latency")
    print("  6. mrr_at_risk - Calculated from failed/pending payments")
    print("  7. failure_reason_std - Standardized failure categories")
    print("  8. failure_severity - Severity level (critical/high/medium/low)")
    print("  9. subscription_type - Inferred (new/renewal/churned)")
    print(" 10. retry_attempts - Synthetic retry count for failed payments")
    print("=" * 70)
    
    return df


if __name__ == '__main__':
    df_enriched = main()
