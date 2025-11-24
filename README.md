# ProcureFlow Backend

Django REST Framework-based procurement system with Role-Based Access Control (RBAC) and multi-level approval workflow.

## Features

✅ **RBAC System**: Flexible role and permission management  
✅ **Multi-Level Approval**: Sequential approval workflow with configurable levels  
✅ **Auto PO Generation**: Purchase orders created automatically after final approval  
✅ **File Management**: Support for proformas, receipts, and PO documents  
✅ **REST API**: Complete DRF implementation with JWT authentication  
✅ **Permission-Based Access**: Fine-grained control over who can perform what actions  
✅ **Audit Trail**: Timestamps and user tracking for all approvals

## Project Structure

```
procureflow-backend/
├── p2p_backend/          # Main project settings
├── roles/                # RBAC: Role, Permission, RolePermission
├── users/                # Custom User model with JWT auth
├── procurement/          # Purchase requests, approvals, orders
├── media/                # Uploaded files (proformas, receipts, POs)
├── manage.py
└── requirements.txt
```

## Installation

### Option 1: Docker (Recommended)

The easiest way to run the project is using Docker with PostgreSQL.

#### Prerequisites
- Docker and Docker Compose installed
- Git

#### Quick Start

1. **Clone the repository**
```bash
cd /Users/macbook/IST/procureflow-backend
```

2. **Build and run with Docker Compose**
```bash
docker-compose up --build
```

This will:
- Start PostgreSQL database
- Run migrations automatically
- Create a superuser (username: `admin`, password: `admin123`)
- Start the Django development server on `http://localhost:8000`

3. **Access the application**
- API: `http://localhost:8000`
- Admin Panel: `http://localhost:8000/admin`
- Login with: `admin` / `admin123`

#### Docker Commands

```bash
# Start services
docker-compose up

# Start in background
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f web

# Run migrations
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser

# Access Django shell
docker-compose exec web python manage.py shell

# Run tests
docker-compose exec web python manage.py test
```

---

### Option 2: Local Development (Without Docker)

If you prefer to run without Docker:

#### Prerequisites
- Python 3.11+
- PostgreSQL 15+

#### Setup

1. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Mac/Linux
# or
venv\Scripts\activate  # On Windows
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure PostgreSQL**
```bash
# Create database
createdb procureflow_db

# Or using psql
psql -U postgres
CREATE DATABASE procureflow_db;
\q
```

4. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your PostgreSQL credentials
```

5. **Run migrations**
```bash
python manage.py migrate
```

6. **Create superuser**
```bash
python manage.py createsuperuser
```

7. **Run development server**
```bash
python manage.py runserver
```

## API Endpoints

### Authentication
- `POST /api/users/auth/login/` - Login (get JWT tokens)
- `POST /api/users/auth/refresh/` - Refresh access token
- `POST /api/users/auth/register/` - Register new user

### Users
- `GET /api/users/` - List users
- `GET /api/users/{id}/` - Get user details
- `GET /api/users/profile/` - Get current user profile
- `PUT /api/users/profile/` - Update profile
- `POST /api/users/change_password/` - Change password

### Roles & Permissions
- `GET /api/roles/roles/` - List roles
- `POST /api/roles/roles/` - Create role
- `POST /api/roles/roles/{id}/add_permission/` - Add permission to role
- `GET /api/roles/permissions/` - List permissions
- `POST /api/roles/permissions/` - Create permission

### Procurement
- `GET /api/procurement/requests/` - List purchase requests
- `POST /api/procurement/requests/` - Create purchase request
- `GET /api/procurement/requests/{id}/` - Get request details
- `POST /api/procurement/requests/{id}/approve/` - Approve current level
- `POST /api/procurement/requests/{id}/reject/` - Reject request
- `GET /api/procurement/requests/pending_approvals/` - Get pending approvals
- `GET /api/procurement/requests/my_requests/` - Get my requests
- `GET /api/procurement/purchase-orders/` - List purchase orders
- `GET /api/procurement/items/` - List request items

## Usage Example

### 1. Setup Roles and Permissions

```bash
# Via Django admin at http://localhost:8000/admin
# Create roles: staff, manager, finance
# Create permissions: create_request, approve_request, view_request
# Assign permissions to roles
```

### 2. Create Purchase Request

```json
POST /api/procurement/requests/
{
  "title": "Office Supplies",
  "description": "Monthly office supplies order",
  "amount": "5000.00",
  "approval_config": [
    {"level": 1, "role_name": "manager"},
    {"level": 2, "role_name": "finance"}
  ],
  "items": [
    {
      "name": "Printer Paper",
      "quantity": 10,
      "unit_price": "25.00"
    }
  ]
}
```

### 3. Approve Request

```json
POST /api/procurement/requests/{id}/approve/
{
  "comments": "Approved for procurement"
}
```

## Multi-Level Approval Workflow

1. **Request Creation**: Staff creates a purchase request with approval levels
2. **Level 1 Approval**: Manager reviews and approves/rejects
3. **Level 2 Approval**: Finance reviews and approves/rejects
4. **Auto PO Generation**: After final approval, Purchase Order is auto-generated
5. **Rejection**: Any level can reject, which stops the entire workflow

## Database Schema

### Core Models

- **Role**: User roles (staff, manager, finance)
- **Permission**: Granular permissions (create_request, approve_request)
- **RolePermission**: Many-to-many relationship
- **User**: Custom user with role assignment
- **PurchaseRequest**: Main request with approval tracking
- **RequestApprovalLevel**: Multi-level approval chain
- **PurchaseOrder**: Auto-generated after approval
- **RequestItem**: Line items for requests

## Development

### Run tests
```bash
python manage.py test
```

### Create migrations
```bash
python manage.py makemigrations
```

### Access admin panel
```bash
http://localhost:8000/admin
```

## License

MIT
