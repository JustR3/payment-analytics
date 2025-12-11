#!/usr/bin/env python3
"""
Database Loading Script
=======================

This script:
1. Creates the PostgreSQL database schema for payments data
2. Loads the enriched parquet data into the database
3. Creates appropriate indexes for Metabase queries
4. Validates the data load

Requires: PostgreSQL running (via docker-compose)
Input: data/processed/payments_enriched.parquet
Output: PostgreSQL 'payments' table
"""

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from pathlib import Path
import sys

# File paths
BASE_DIR = Path(__file__).parent.parent
INPUT_FILE = BASE_DIR / 'data' / 'processed' / 'payments_enriched.parquet'

# Database connection parameters
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'payments_analytics',
    'user': 'analytics_user',
    'password': 'analytics_pass_2024'
}

def create_connection_string():
    """Create PostgreSQL connection string"""
    return f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"

def test_connection():
    """Test database connection"""
    print("Testing database connection...")
    try:
        engine = create_engine(create_connection_string())
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version();"))
            version = result.fetchone()[0]
            print(f"  ✓ Connected to: {version.split(',')[0]}")
        return engine
    except Exception as e:
        print(f"  ✗ Connection failed: {e}")
        print("\n  Please ensure PostgreSQL is running:")
        print("    docker-compose up -d postgres")
        sys.exit(1)

def load_parquet_data():
    """Load enriched data from parquet"""
    print(f"\nLoading data from {INPUT_FILE}...")
    df = pd.read_parquet(INPUT_FILE)
    print(f"  Loaded {len(df):,} records with {len(df.columns)} columns")
    return df

def prepare_dataframe(df):
    """Prepare dataframe for database loading"""
    print("\nPreparing data for database...")
    
    # Create a copy to avoid modifying original
    df_db = df.copy()
    
    # Convert datetime columns to proper types
    datetime_cols = [
        'subscription_start_date',
        'next_renewal_date',
        'last_payment_date',
        'cancellation_date',
        'last_retention_action_date'
    ]
    
    for col in datetime_cols:
        if col in df_db.columns:
            df_db[col] = pd.to_datetime(df_db[col])
    
    # Convert date to datetime (PostgreSQL doesn't have Date type in pandas)
    if 'date' in df_db.columns:
        df_db['date'] = pd.to_datetime(df_db['date'])
    
    # Ensure proper string types for categorical columns
    string_cols = [
        'subscription_id', 'customer_id', 'customer_email', 'plan_id', 
        'plan_name', 'billing_cycle', 'payment_status', 'payment_failure_reason',
        'payment_method', 'retention_status', 'month', 'quarter', 'day_of_week',
        'txn_value_bucket', 'payment_provider', 'geo_region', 'product_tier',
        'processing_time_bucket', 'failure_reason_std', 'failure_severity',
        'subscription_type'
    ]
    
    for col in string_cols:
        if col in df_db.columns:
            df_db[col] = df_db[col].astype(str)
            df_db[col] = df_db[col].replace('nan', None)
            df_db[col] = df_db[col].replace('<NA>', None)
    
    # Ensure numeric types
    numeric_cols = [
        'plan_price', 'total_payments', 'failed_payments_count', 
        'year', 'hour', 'subscription_age_days', 'processing_time_s',
        'mrr_at_risk', 'retry_attempts'
    ]
    
    for col in numeric_cols:
        if col in df_db.columns:
            df_db[col] = pd.to_numeric(df_db[col], errors='coerce')
    
    print(f"  ✓ Data prepared for database loading")
    return df_db

def create_schema(engine):
    """Create database schema and indexes"""
    print("\nCreating database schema...")
    
    with engine.connect() as conn:
        # Drop table if exists
        conn.execute(text("DROP TABLE IF EXISTS payments CASCADE;"))
        conn.commit()
        
        # Note: We'll let pandas create the table with to_sql
        # This is simpler and handles type mapping automatically
        
        print("  ✓ Ready to create table")

def load_to_database(engine, df):
    """Load data to PostgreSQL"""
    print("\nLoading data to PostgreSQL...")
    
    try:
        # Load data using pandas to_sql
        df.to_sql(
            name='payments',
            con=engine,
            if_exists='replace',
            index=False,
            method='multi',
            chunksize=1000
        )
        
        print(f"  ✓ Loaded {len(df):,} records to 'payments' table")
        return True
        
    except SQLAlchemyError as e:
        print(f"  ✗ Error loading data: {e}")
        return False

def create_indexes(engine):
    """Create indexes for better query performance"""
    print("\nCreating indexes for query optimization...")
    
    indexes = [
        "CREATE INDEX idx_payment_status ON payments(payment_status);",
        "CREATE INDEX idx_payment_provider ON payments(payment_provider);",
        "CREATE INDEX idx_geo_region ON payments(geo_region);",
        "CREATE INDEX idx_product_tier ON payments(product_tier);",
        "CREATE INDEX idx_date ON payments(date);",
        "CREATE INDEX idx_month ON payments(month);",
        "CREATE INDEX idx_is_success ON payments(is_success);",
        "CREATE INDEX idx_is_high_value ON payments(is_high_value);",
        "CREATE INDEX idx_failure_reason ON payments(failure_reason_std);",
        "CREATE INDEX idx_customer_id ON payments(customer_id);",
        "CREATE INDEX idx_subscription_id ON payments(subscription_id);",
    ]
    
    with engine.connect() as conn:
        for idx_sql in indexes:
            try:
                conn.execute(text(idx_sql))
                idx_name = idx_sql.split()[2]
                print(f"  ✓ Created {idx_name}")
            except Exception as e:
                print(f"  ✗ Error creating index: {e}")
        
        conn.commit()

def validate_load(engine):
    """Validate the data load"""
    print("\nValidating data load...")
    
    with engine.connect() as conn:
        # Count records
        result = conn.execute(text("SELECT COUNT(*) FROM payments;"))
        count = result.fetchone()[0]
        print(f"  Total records: {count:,}")
        
        # Success rate
        result = conn.execute(text("""
            SELECT 
                payment_status,
                COUNT(*) as count,
                ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as percentage
            FROM payments
            GROUP BY payment_status
            ORDER BY count DESC;
        """))
        
        print("\n  Payment Status Distribution:")
        for row in result:
            print(f"    - {row[0]}: {row[1]:,} ({row[2]}%)")
        
        # Provider distribution
        result = conn.execute(text("""
            SELECT 
                payment_provider,
                COUNT(*) as count
            FROM payments
            GROUP BY payment_provider
            ORDER BY count DESC
            LIMIT 5;
        """))
        
        print("\n  Top Payment Providers:")
        for row in result:
            print(f"    - {row[0]}: {row[1]:,}")
        
        # MRR at risk
        result = conn.execute(text("""
            SELECT 
                ROUND(SUM(mrr_at_risk)::numeric, 2) as total_mrr_at_risk,
                COUNT(*) FILTER (WHERE mrr_at_risk > 0) as affected_subscriptions
            FROM payments;
        """))
        
        row = result.fetchone()
        print(f"\n  MRR at Risk: ${row[0]:,.2f}")
        print(f"  Affected Subscriptions: {row[1]:,}")

def main():
    """Main execution flow"""
    print("=" * 70)
    print("PAYMENT ANALYTICS - DATABASE LOADING")
    print("=" * 70)
    
    # Test connection
    engine = test_connection()
    
    # Load data
    df = load_parquet_data()
    
    # Prepare data
    df_db = prepare_dataframe(df)
    
    # Create schema
    create_schema(engine)
    
    # Load to database
    success = load_to_database(engine, df_db)
    
    if not success:
        print("\n✗ Data loading failed!")
        sys.exit(1)
    
    # Create indexes
    create_indexes(engine)
    
    # Validate
    validate_load(engine)
    
    print("\n" + "=" * 70)
    print("✓ Database loading completed successfully!")
    print("=" * 70)
    print("\nNext steps:")
    print("  1. Start Metabase: docker-compose up -d metabase")
    print("  2. Open browser: http://localhost:3000")
    print("  3. Configure Metabase with these credentials:")
    print(f"       Database: PostgreSQL")
    print(f"       Host: postgres (or localhost if accessing from host)")
    print(f"       Port: {DB_CONFIG['port']}")
    print(f"       Database: {DB_CONFIG['database']}")
    print(f"       User: {DB_CONFIG['user']}")
    print(f"       Password: {DB_CONFIG['password']}")
    print("=" * 70)

if __name__ == '__main__':
    main()
