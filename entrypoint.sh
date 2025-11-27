#!/bin/bash

# Exit on error
set -e

echo "🚀 Starting ProcureFlow Backend..."

# Wait for database to be ready
echo "⏳ Waiting for database connection..."
python /app/wait_for_db.py

# Run migrations
echo "📦 Running migrations..."
python manage.py migrate --noinput

# Initialize admin and test users
echo "👥 Initializing admin and test users..."
python manage.py init_admin

# Collect static files
echo "📁 Collecting static files..."
python manage.py collectstatic --noinput

# Start server
echo "✅ Starting Gunicorn server..."
PORT=${PORT:-8000}
exec gunicorn p2p_backend.wsgi:application \
    --bind 0.0.0.0:$PORT \
    --workers 3 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -


