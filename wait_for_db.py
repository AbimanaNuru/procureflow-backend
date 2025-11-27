#!/usr/bin/env python3
"""
Database connection checker for Docker deployments
Works with both DATABASE_URL and individual DB settings
"""
import sys
import time
import os

try:
    import psycopg2
    from urllib.parse import urlparse
except ImportError:
    print("Error: psycopg2 not installed")
    sys.exit(1)

# Get database URL
db_url = os.environ.get('DATABASE_URL')
if not db_url:
    # Fallback to individual settings for Docker Compose
    db_user = os.environ.get('DB_USER', 'postgres')
    db_password = os.environ.get('DB_PASSWORD', '')
    db_host = os.environ.get('DB_HOST', 'db')
    db_port = os.environ.get('DB_PORT', '5432')
    db_name = os.environ.get('DB_NAME', 'procureflow_db')
    db_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

# Parse the URL
result = urlparse(db_url)
username = result.username
password = result.password
database = result.path[1:]
hostname = result.hostname
port = result.port

# Wait for connection
max_retries = 30
for i in range(max_retries):
    try:
        conn = psycopg2.connect(
            dbname=database,
            user=username,
            password=password,
            host=hostname,
            port=port
        )
        conn.close()
        print("✓ Database connection successful!")
        sys.exit(0)
    except psycopg2.OperationalError as e:
        if i < max_retries - 1:
            print(f"⏳ Database not ready, waiting... ({i+1}/{max_retries})")
            time.sleep(1)
        else:
            print(f"✗ Could not connect to database after {max_retries} attempts")
            print(f"Error: {e}")
            sys.exit(1)
