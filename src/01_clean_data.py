#!/usr/bin/env python3
"""
Data Cleaning and Standardization Script
=========================================

This script processes the raw subscription billing data and performs:
1. Date parsing and standardization
2. Numeric type enforcement
3. Data quality checks and cleaning
4. Derived field creation

Input: data/raw/subscription-billing.csv
Output: data/processed/payments_clean.parquet
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime

# Configure pandas display
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)

# File paths
BASE_DIR = Path(__file__).parent.parent
RAW_DATA = BASE_DIR / 'data' / 'raw' / 'subscription-billing.csv'
OUTPUT_FILE = BASE_DIR / 'data' / 'processed' / 'payments_clean.parquet'

def load_raw_data():
    """Load the raw CSV data"""
    print(f"Loading data from {RAW_DATA}...")
    df = pd.read_csv(RAW_DATA)
    print(f"Loaded {len(df):,} records with {len(df.columns)} columns")
    return df

def clean_dates(df):
    """Parse and standardize date columns"""
    print("\nCleaning date fields...")
    
    date_columns = [
        'subscription_start_date',
        'next_renewal_date', 
        'last_payment_date',
        'cancellation_date',
        'last_retention_action_date'
    ]
    
    for col in date_columns:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')
            print(f"  - {col}: {df[col].notna().sum():,} valid dates")
    
    return df

def create_derived_fields(df):
    """Create derived columns for analysis"""
    print("\nCreating derived fields...")
    
    # Extract date components from last_payment_date
    df['date'] = df['last_payment_date'].dt.date
    df['month'] = df['last_payment_date'].dt.to_period('M').astype(str)
    df['year'] = df['last_payment_date'].dt.year
    df['quarter'] = df['last_payment_date'].dt.to_period('Q').astype(str)
    df['day_of_week'] = df['last_payment_date'].dt.day_name()
    df['hour'] = df['last_payment_date'].dt.hour
    
    print(f"  - Date components extracted")
    
    # Boolean success indicator
    df['is_success'] = (df['payment_status'] == 'success').astype(bool)
    success_rate = df['is_success'].mean() * 100
    print(f"  - is_success: {success_rate:.1f}% success rate")
    
    # Ensure numeric types for amounts
    df['plan_price'] = pd.to_numeric(df['plan_price'], errors='coerce')
    df['total_payments'] = pd.to_numeric(df['total_payments'], errors='coerce')
    df['failed_payments_count'] = pd.to_numeric(df['failed_payments_count'], errors='coerce')
    
    # Transaction value buckets (quantile-based)
    df['txn_value_bucket'] = pd.qcut(
        df['plan_price'], 
        q=4, 
        labels=['Small', 'Medium', 'Large', 'Enterprise'],
        duplicates='drop'
    )
    print(f"  - txn_value_bucket: {df['txn_value_bucket'].value_counts().to_dict()}")
    
    # Flag for high-value transactions (top 10%)
    high_value_threshold = df['plan_price'].quantile(0.90)
    df['is_high_value'] = (df['plan_price'] >= high_value_threshold).astype(bool)
    print(f"  - is_high_value: {df['is_high_value'].sum():,} transactions (threshold: ${high_value_threshold:.2f})")
    
    # Subscription age in days (at time of last payment)
    df['subscription_age_days'] = (df['last_payment_date'] - df['subscription_start_date']).dt.days
    
    # Is recurring payment (not first payment)
    df['is_recurring'] = (df['total_payments'] > 1).astype(bool)
    
    return df

def data_quality_checks(df):
    """Perform data quality validation"""
    print("\nData Quality Checks:")
    print("=" * 50)
    
    # Missing values
    print("\nMissing Values:")
    missing = df.isnull().sum()
    missing = missing[missing > 0].sort_values(ascending=False)
    if len(missing) > 0:
        for col, count in missing.items():
            pct = (count / len(df)) * 100
            print(f"  - {col}: {count:,} ({pct:.1f}%)")
    else:
        print("  No missing values found!")
    
    # Duplicates
    duplicates = df.duplicated(subset=['subscription_id']).sum()
    print(f"\nDuplicate subscription_ids: {duplicates}")
    
    # Value ranges
    print(f"\nValue Ranges:")
    print(f"  - plan_price: ${df['plan_price'].min():.2f} to ${df['plan_price'].max():.2f}")
    print(f"  - total_payments: {df['total_payments'].min():.0f} to {df['total_payments'].max():.0f}")
    print(f"  - failed_payments_count: {df['failed_payments_count'].min():.0f} to {df['failed_payments_count'].max():.0f}")
    
    # Payment status distribution
    print(f"\nPayment Status Distribution:")
    for status, count in df['payment_status'].value_counts().items():
        pct = (count / len(df)) * 100
        print(f"  - {status}: {count:,} ({pct:.1f}%)")
    
    # Billing cycle distribution
    print(f"\nBilling Cycle Distribution:")
    for cycle, count in df['billing_cycle'].value_counts().items():
        pct = (count / len(df)) * 100
        print(f"  - {cycle}: {count:,} ({pct:.1f}%)")
    
    return df

def save_clean_data(df):
    """Save cleaned data to parquet"""
    print(f"\nSaving cleaned data to {OUTPUT_FILE}...")
    
    # Ensure output directory exists
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    # Save to parquet (efficient columnar format)
    df.to_parquet(OUTPUT_FILE, index=False, engine='pyarrow')
    
    file_size = OUTPUT_FILE.stat().st_size / 1024  # KB
    print(f"Saved {len(df):,} records ({file_size:.1f} KB)")
    
    # Also save a sample CSV for inspection
    sample_csv = OUTPUT_FILE.parent / 'payments_clean_sample.csv'
    df.head(100).to_csv(sample_csv, index=False)
    print(f"Saved sample (100 rows) to {sample_csv}")

def main():
    """Main execution flow"""
    print("=" * 70)
    print("PAYMENT DATA CLEANING & STANDARDIZATION")
    print("=" * 70)
    
    # Load data
    df = load_raw_data()
    
    # Clean dates
    df = clean_dates(df)
    
    # Create derived fields
    df = create_derived_fields(df)
    
    # Data quality checks
    df = data_quality_checks(df)
    
    # Save cleaned data
    save_clean_data(df)
    
    print("\n" + "=" * 70)
    print("✓ Data cleaning completed successfully!")
    print("=" * 70)
    
    return df

if __name__ == '__main__':
    df_clean = main()
