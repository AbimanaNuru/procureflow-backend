# Deployment Guide - Database Configuration

## Issue
```
django.db.utils.OperationalError: could not translate host name "db" to address: Name or service not known
```

This error occurs because the application is trying to connect to a database host named "db" (which works in Docker Compose) but doesn't exist in your deployment environment.

## Solution

### For Cloud Deployments (Render, Heroku, Railway, etc.)

1. **Set the `DATABASE_URL` environment variable** in your deployment platform:
   ```
   DATABASE_URL=postgresql://username:password@host:port/database_name
   ```

2. **Remove or don't set** the individual DB variables (`DB_HOST`, `DB_NAME`, etc.) as they will be ignored when `DATABASE_URL` is present.

3. **Example for Render**:
   - Go to your service dashboard
   - Navigate to "Environment" tab
   - Add environment variable:
     - Key: `DATABASE_URL`
     - Value: (Copy from your PostgreSQL database connection string)

### For Docker Compose (Local Development)

Keep the individual DB settings in your `.env`:
```bash
DB_ENGINE=django.db.backends.postgresql
DB_NAME=procureflow_db
DB_USER=postgres
DB_PASSWORD=your-password
DB_HOST=db
DB_PORT=5432
```

## How It Works

The updated `settings.py` now:
1. **First** checks for `DATABASE_URL` (cloud deployment)
2. **Then** falls back to individual DB settings (Docker)
3. **Finally** uses SQLite as last resort (local development)

## Verification

After deploying, check your logs to ensure the database connection is successful:
```bash
# The migration should run without errors
python manage.py migrate
```
