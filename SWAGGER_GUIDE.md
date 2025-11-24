# 📚 API Documentation with Swagger

## ✅ Swagger UI is Now Available!

Your ProcureFlow API now has interactive API documentation powered by drf-spectacular.

### Access the Documentation

| Documentation Type | URL | Description |
|-------------------|-----|-------------|
| **Swagger UI** | http://localhost:8000/api/docs/ | Interactive API documentation with "Try it out" feature |
| **ReDoc** | http://localhost:8000/api/redoc/ | Clean, responsive API documentation |
| **OpenAPI Schema** | http://localhost:8000/api/schema/ | Raw OpenAPI 3.0 schema (JSON) |

## 🎯 How to Use Swagger UI

### 1. Open Swagger UI
Visit: http://localhost:8000/api/docs/

### 2. Authenticate
1. Click the **"Authorize"** button (top right with lock icon)
2. Get your JWT token first:
   - Use the `/api/users/auth/login/` endpoint
   - Enter your credentials (admin/admin123)
   - Copy the `access` token from the response

3. In the Authorization dialog:
   - Enter: `Bearer YOUR_ACCESS_TOKEN`
   - Click "Authorize"
   - Click "Close"

### 3. Test Endpoints
Now you can test any endpoint:
1. Click on an endpoint to expand it
2. Click "Try it out"
3. Fill in the parameters
4. Click "Execute"
5. See the response below

## 📋 Available Endpoint Groups

### Authentication (`/api/users/auth/`)
- `POST /api/users/auth/login/` - Login and get JWT tokens
- `POST /api/users/auth/refresh/` - Refresh access token
- `POST /api/users/auth/register/` - Register new user

### Users (`/api/users/`)
- `GET /api/users/` - List users
- `POST /api/users/` - Create user
- `GET /api/users/{id}/` - Get user details
- `GET /api/users/profile/` - Get current user profile
- `PUT /api/users/profile/` - Update profile
- `POST /api/users/change_password/` - Change password

### Roles (`/api/roles/`)
- `GET /api/roles/roles/` - List roles
- `POST /api/roles/roles/` - Create role
- `POST /api/roles/roles/{id}/add_permission/` - Add permission to role
- `POST /api/roles/roles/{id}/remove_permission/` - Remove permission from role
- `GET /api/roles/permissions/` - List permissions
- `POST /api/roles/permissions/` - Create permission

### Procurement (`/api/procurement/`)
- `GET /api/procurement/requests/` - List purchase requests
- `POST /api/procurement/requests/` - Create purchase request
- `GET /api/procurement/requests/{id}/` - Get request details
- `POST /api/procurement/requests/{id}/approve/` - Approve current level
- `POST /api/procurement/requests/{id}/reject/` - Reject request
- `GET /api/procurement/requests/pending_approvals/` - Get pending approvals
- `GET /api/procurement/requests/my_requests/` - Get my requests
- `GET /api/procurement/purchase-orders/` - List purchase orders
- `GET /api/procurement/items/` - List request items

## 💡 Quick Example Workflow in Swagger

### 1. Login
```
POST /api/users/auth/login/
Body:
{
  "username": "admin",
  "password": "admin123"
}
```
Copy the `access` token.

### 2. Authorize
Click "Authorize" → Enter `Bearer YOUR_TOKEN` → Authorize

### 3. Create a Purchase Request
```
POST /api/procurement/requests/
Body:
{
  "title": "Office Supplies",
  "description": "Monthly supplies order",
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

### 4. View Pending Approvals
```
GET /api/procurement/requests/pending_approvals/
```

### 5. Approve Request
```
POST /api/procurement/requests/1/approve/
Body:
{
  "comments": "Approved"
}
```

## 🔧 Features

✅ **Interactive Testing** - Try out endpoints directly from the browser  
✅ **Authentication Support** - JWT Bearer token authentication  
✅ **Request/Response Examples** - See example payloads  
✅ **Schema Validation** - Automatic validation of request bodies  
✅ **Download Schema** - Export OpenAPI schema for client generation  
✅ **Deep Linking** - Share direct links to specific endpoints  
✅ **Persistent Authorization** - Token persists across page refreshes  

## 📥 Export API Schema

You can download the OpenAPI schema for:
- Generating client SDKs (Python, JavaScript, etc.)
- Importing into Postman
- API testing tools

Download from: http://localhost:8000/api/schema/

## 🎨 Two Documentation Styles

### Swagger UI (Recommended for Testing)
- Interactive "Try it out" feature
- Great for development and testing
- http://localhost:8000/api/docs/

### ReDoc (Recommended for Reading)
- Clean, professional layout
- Better for documentation review
- http://localhost:8000/api/redoc/

## 🚀 Next Steps

1. Open http://localhost:8000/api/docs/
2. Click "Authorize" and login
3. Explore all available endpoints
4. Test the approval workflow
5. Share the documentation with your team!

---

**Happy API Testing! 🎉**
