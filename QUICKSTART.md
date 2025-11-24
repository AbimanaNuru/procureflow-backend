# Quick Start Guide

## ✅ Your ProcureFlow Backend is Running!

### Access Points

- **API Base URL**: http://localhost:8000
- **Admin Panel**: http://localhost:8000/admin
- **Default Credentials**: `admin` / `admin123`

### Initial Setup Steps

1. **Login to Admin Panel**
   ```
   http://localhost:8000/admin
   Username: admin
   Password: admin123
   ```

2. **Create Roles**
   - Go to "Roles" section
   - Add these roles:
     - `staff` - For employees creating requests
     - `manager` - For first-level approvers
     - `finance` - For second-level approvers

3. **Create Permissions**
   - Go to "Permissions" section
   - Add these permissions:
     - `create_request` - Can create purchase requests
     - `approve_request` - Can approve requests
     - `view_request` - Can view requests

4. **Assign Permissions to Roles**
   - Go to "Role permissions" section
   - Assign:
     - **staff**: `create_request`, `view_request`
     - **manager**: `approve_request`, `view_request`
     - **finance**: `approve_request`, `view_request`

5. **Create Test Users**
   - Go to "Users" section
   - Create users with different roles:
     - John (staff) - can create requests
     - Sarah (manager) - can approve level 1
     - Mike (finance) - can approve level 2

### Test the Approval Workflow

#### 1. Get JWT Token (Login as John - staff)

```bash
curl -X POST http://localhost:8000/api/users/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john",
    "password": "password123"
  }'
```

#### 2. Create Purchase Request

```bash
curl -X POST http://localhost:8000/api/procurement/requests/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "title": "Office Supplies Order",
    "description": "Monthly office supplies",
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
  }'
```

#### 3. Approve as Manager (Sarah)

```bash
curl -X POST http://localhost:8000/api/procurement/requests/1/approve/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer SARAH_ACCESS_TOKEN" \
  -d '{
    "comments": "Approved for procurement"
  }'
```

#### 4. Approve as Finance (Mike)

```bash
curl -X POST http://localhost:8000/api/procurement/requests/1/approve/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer MIKE_ACCESS_TOKEN" \
  -d '{
    "comments": "Budget approved"
  }'
```

After Mike's approval, a Purchase Order will be auto-generated!

### Useful Docker Commands

```bash
# View logs
docker-compose logs -f web

# Access Django shell
docker-compose exec web python manage.py shell

# Create superuser
docker-compose exec web python manage.py createsuperuser

# Run migrations
docker-compose exec web python manage.py migrate

# Stop containers
docker-compose down

# Restart containers
docker-compose restart
```

### API Endpoints

**Authentication:**
- `POST /api/users/auth/login/` - Login
- `POST /api/users/auth/refresh/` - Refresh token
- `POST /api/users/auth/register/` - Register

**Procurement:**
- `GET /api/procurement/requests/` - List requests
- `POST /api/procurement/requests/` - Create request
- `GET /api/procurement/requests/{id}/` - Get request details
- `POST /api/procurement/requests/{id}/approve/` - Approve
- `POST /api/procurement/requests/{id}/reject/` - Reject
- `GET /api/procurement/requests/pending_approvals/` - My pending approvals
- `GET /api/procurement/requests/my_requests/` - My requests

**Roles & Permissions:**
- `GET /api/roles/roles/` - List roles
- `POST /api/roles/roles/` - Create role
- `GET /api/roles/permissions/` - List permissions
- `POST /api/roles/permissions/` - Create permission

### Troubleshooting

**Port conflicts:**
- PostgreSQL: Changed to port 5433 (instead of 5432)
- Django: Running on port 8000

**Reset everything:**
```bash
docker-compose down -v
docker-compose up --build
```

### Next Steps

1. ✅ Setup roles and permissions (via admin panel)
2. ✅ Create test users
3. ✅ Test approval workflow
4. 🔄 Integrate with frontend
5. 🔄 Deploy to production

---

**Need help?** Check:
- `README.md` - Full documentation
- `DOCKER_SETUP.md` - Detailed Docker guide
- `walkthrough.md` - Implementation details
