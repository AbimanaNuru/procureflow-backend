# Docker Setup Guide

## Quick Start with Docker

This guide will help you set up the ProcureFlow backend using Docker and PostgreSQL.

### Prerequisites

- Docker Desktop installed ([Download here](https://www.docker.com/products/docker-desktop))
- Docker Compose (included with Docker Desktop)

### Step 1: Start the Application

```bash
# Navigate to project directory
cd /Users/macbook/IST/procureflow-backend

# Build and start all services
docker-compose up --build
```

**What happens:**
1. PostgreSQL database starts on port 5432
2. Django migrations run automatically
3. Superuser created (admin/admin123)
4. Django server starts on port 8000

### Step 2: Access the Application

- **API**: http://localhost:8000
- **Admin Panel**: http://localhost:8000/admin
- **Default Login**: `admin` / `admin123`

### Step 3: Initial Setup

1. **Login to Admin Panel**
   - Go to http://localhost:8000/admin
   - Login with admin/admin123

2. **Create Roles**
   - Navigate to Roles section
   - Create: `staff`, `manager`, `finance`

3. **Create Permissions**
   - Navigate to Permissions section
   - Create: `create_request`, `approve_request`, `view_request`

4. **Assign Permissions to Roles**
   - staff → create_request, view_request
   - manager → approve_request, view_request
   - finance → approve_request, view_request

5. **Create Users**
   - Navigate to Users section
   - Create users and assign roles

## Common Docker Commands

```bash
# Start services (after first build)
docker-compose up

# Start in background
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f web
docker-compose logs -f db

# Restart services
docker-compose restart

# Remove all containers and volumes
docker-compose down -v
```

## Database Management

```bash
# Access PostgreSQL shell
docker-compose exec db psql -U postgres -d procureflow_db

# Backup database
docker-compose exec db pg_dump -U postgres procureflow_db > backup.sql

# Restore database
docker-compose exec -T db psql -U postgres procureflow_db < backup.sql

# Run migrations
docker-compose exec web python manage.py migrate

# Create new migrations
docker-compose exec web python manage.py makemigrations
```

## Django Management

```bash
# Create superuser
docker-compose exec web python manage.py createsuperuser

# Access Django shell
docker-compose exec web python manage.py shell

# Collect static files
docker-compose exec web python manage.py collectstatic

# Run tests
docker-compose exec web python manage.py test
```

## Troubleshooting

### Port Already in Use

If port 8000 or 5432 is already in use:

```bash
# Stop conflicting services
# For Mac/Linux
lsof -ti:8000 | xargs kill -9
lsof -ti:5432 | xargs kill -9

# Or change ports in docker-compose.yml
ports:
  - "8001:8000"  # Change host port
```

### Database Connection Issues

```bash
# Check if database is running
docker-compose ps

# Restart database
docker-compose restart db

# Check database logs
docker-compose logs db
```

### Reset Everything

```bash
# Stop and remove all containers, networks, and volumes
docker-compose down -v

# Rebuild from scratch
docker-compose up --build
```

## Production Deployment

For production, create a `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  db:
    image: postgres:15-alpine
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_DB=${DB_NAME}
      - POSTGRES_USER=${DB_USER}
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    restart: always

  web:
    build: .
    command: gunicorn p2p_backend.wsgi:application --bind 0.0.0.0:8000
    volumes:
      - static_volume:/app/staticfiles
      - media_volume:/app/media
    expose:
      - 8000
    env_file:
      - .env
    depends_on:
      - db
    restart: always

  nginx:
    image: nginx:alpine
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - static_volume:/app/staticfiles
      - media_volume:/app/media
    ports:
      - "80:80"
    depends_on:
      - web
    restart: always

volumes:
  postgres_data:
  static_volume:
  media_volume:
```

## Environment Variables

Create `.env` file for production:

```bash
SECRET_KEY=your-very-secure-secret-key
DEBUG=False
ALLOWED_HOSTS=your-domain.com,www.your-domain.com
DB_ENGINE=django.db.backends.postgresql
DB_NAME=procureflow_db
DB_USER=postgres
DB_PASSWORD=your-secure-password
DB_HOST=db
DB_PORT=5432
CORS_ALLOWED_ORIGINS=https://your-frontend.com
```

## Next Steps

1. Test the API endpoints using the examples in README.md
2. Create roles and permissions
3. Register users with different roles
4. Test the approval workflow
5. Integrate with your frontend application
