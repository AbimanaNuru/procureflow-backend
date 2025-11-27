#!/bin/bash

# Exit on error
set -e

echo "Starting ProcureFlow Backend..."

# Wait for database to be ready (works with both Docker Compose and Render)
echo "Waiting for database connection..."
python \<\< END
import sys
import time
import psycopg2
from urllib.parse import urlparse
import os

# Get database URL
db_url = os.environ.get('DATABASE_URL')
if not db_url:
    # Fallback to individual settings for Docker Compose
    db_url = f"postgresql://{os.environ.get('DB_USER', 'postgres')}:{os.environ.get('DB_PASSWORD', '')}@{os.environ.get('DB_HOST', 'db')}:{os.environ.get('DB_PORT', '5432')}/{os.environ.get('DB_NAME', 'procureflow_db')}"

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
        print("Database connection successful!")
        sys.exit(0)
    except psycopg2.OperationalError:
        if i < max_retries - 1:
            print(f"Database not ready, waiting... ({i+1}/{max_retries})")
            time.sleep(1)
        else:
            print("Could not connect to database after 30 attempts")
            sys.exit(1)
END

# Run migrations
echo "Running migrations..."
python manage.py migrate --noinput

# Initialize admin and test users
echo "Initializing admin and test users..."
python manage.py init_admin

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Start server
echo "Starting Gunicorn server..."
PORT=${PORT:-8000}
gunicorn p2p_backend.wsgi:application --bind 0.0.0.0:$PORT --workers 3 --timeout 120

