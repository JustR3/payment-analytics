# Metabase Setup Instructions

## First-Time Setup

Since you're accessing Metabase at http://localhost:3000 for the first time, follow these steps:

### Step 1: Create Your Admin Account
1. Open http://localhost:3000 in your browser
2. You'll see the "Welcome to Metabase" screen
3. Fill in:
   - **First name**: Your first name
   - **Last name**: Your last name
   - **Email**: Your email (can be anything like admin@local.com)
   - **Password**: Create a password
4. Click **Next**

### Step 2: Add Your Database Connection
1. On the "Add your data" screen, select **PostgreSQL**
2. Fill in the connection details:
   
   ```
   Display name: Payment Analytics
   Host: postgres
   Port: 5432
   Database name: payments_analytics
   Username: proton
   Password: proton_analytics_2025
   ```

3. **IMPORTANT**: The host is `postgres` (the Docker service name), NOT `localhost`
4. Click **Connect database**

### Step 3: Configure Usage Data (Optional)
1. Choose whether to share anonymous usage data with Metabase
2. Click **Next** or **Finish**

### Step 4: Verify Your Data
1. After setup, click on **Browse data** in the top navigation
2. You should see your "Payment Analytics" database
3. Click on it to see the table: `payments_proton`
4. Click on the table to browse your data

## What You'll See

Once connected, you'll have access to:
- **payments_proton** table with all your enriched payment data
- Ability to create questions (queries)
- Ability to create dashboards
- Full SQL editor for custom queries

## Troubleshooting

### If connection fails:
1. Make sure both containers are running: `docker-compose ps`
2. Both should show status "Up" and postgres should be "healthy"
3. Try using `payment-analytics-db` as the host instead of `postgres`
4. Check the database is accessible: `docker exec -it payment-analytics-db psql -U proton -d payments_analytics -c "\dt"`

### If you see "database doesn't exist":
Run: `docker-compose logs postgres` to check for PostgreSQL errors

## Next Steps

After connecting your database:
1. Create your first question/query
2. Build dashboards using the insights from `dashboards/KEY_FINDINGS.md`
3. Export and share your analysis

For specific analytical questions and SQL queries to try, see `dashboards/KEY_FINDINGS.md`.
