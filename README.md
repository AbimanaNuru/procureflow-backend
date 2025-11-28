# ProcureFlow Backend

[![Django](https://img.shields.io/badge/Django-5.0-green.svg)](https://www.djangoproject.com/)
[![DRF](https://img.shields.io/badge/DRF-3.15-red.svg)](https://www.django-rest-framework.org/)
[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

ProcureFlow is a modern, AI-powered Procure-to-Pay (P2P) system designed to streamline procurement processes from purchase request creation to payment. This backend provides comprehensive REST APIs for purchase request management, multi-level approval workflows, automatic purchase order generation, and intelligent document processing using AI.

## 📑 Table of Contents

- [Features](#-features)
- [Architecture](#-architecture)
- [Tech Stack](#️-tech-stack)
- [Prerequisites](#-prerequisites)
- [Installation](#-installation--usage)
- [Configuration](#️-configuration)
- [API Documentation](#-api-documentation)
- [Development Workflow](#-development-workflow)
- [Testing](#-testing)
- [Deployment](#-deployment)
- [Troubleshooting](#-troubleshooting)
- [Contributing](#-contributing)
- [Security](#-security)
- [License](#-license)

## 🚀 Features

### Core Functionality
- **Purchase Request Management**: Create, track, and manage purchase requests with line items
- **Multi-Level Approval Workflow**: Configurable approval chains based on request amount and department
- **Automatic PO Generation**: Automatically generates Purchase Orders once a request is fully approved
- **Role-Based Access Control (RBAC)**: Granular permissions for Requesters, Approvers, and Admins

### AI-Powered Features
- **Proforma Extraction**: Upload proforma invoices to automatically extract vendor details, line items, and prices using Groq AI (Llama 3)
- **Receipt Validation**: Upload receipts to validate them against generated POs, flagging discrepancies in prices or items
- **OCR Support**: Extract text from scanned documents using Tesseract and PDFPlumber

### API & Documentation
- **RESTful API**: Comprehensive REST API with JWT authentication
- **Interactive Documentation**: Swagger/OpenAPI and ReDoc documentation
- **Filtering & Search**: Advanced filtering, searching, and pagination on all endpoints

## 🏗 Architecture

### System Architecture

```mermaid
graph TB
    subgraph "Client Layer"
        FE[Frontend Application]
    end
    
    subgraph "API Layer"
        API[Django REST Framework]
        AUTH[JWT Authentication]
        PERM[Permission System]
    end
    
    subgraph "Business Logic Layer"
        PR[Purchase Request Service]
        APR[Approval Workflow Service]
        DOC[Document Processing Service]
        PO[Purchase Order Service]
    end
    
    subgraph "Data Layer"
        DB[(PostgreSQL Database)]
        MEDIA[Media Storage]
    end
    
    subgraph "External Services"
        GROQ[Groq AI API]
        OCR[Tesseract OCR]
    end
    
    FE -->|HTTP/JSON| API
    API --> AUTH
    AUTH --> PERM
    API --> PR
    API --> APR
    API --> DOC
    API --> PO
    
    PR --> DB
    APR --> DB
    PO --> DB
    DOC --> MEDIA
    DOC --> GROQ
    DOC --> OCR
    
    PR -.->|triggers| APR
    APR -.->|generates| PO
```

### Data Flow: Purchase Request Lifecycle

```mermaid
sequenceDiagram
    participant User
    participant API
    participant ApprovalService
    participant Database
    participant POService
    
    User->>API: Create Purchase Request
    API->>Database: Save Request (status: pending)
    API->>ApprovalService: Setup Approval Levels
    ApprovalService->>Database: Create Approval Levels
    
    User->>API: Approve Level 1
    API->>ApprovalService: Process Approval
    ApprovalService->>Database: Update Level Status
    
    User->>API: Approve Level 2 (Final)
    API->>ApprovalService: Process Final Approval
    ApprovalService->>Database: Update Request Status
    ApprovalService->>POService: Generate Purchase Order
    POService->>Database: Create PO
    POService-->>User: Return PO Details
```

### Component Structure

```
procureflow-backend/
├── p2p_backend/          # Project settings & configuration
│   ├── settings.py       # Django settings
│   ├── urls.py          # Root URL configuration
│   └── wsgi.py          # WSGI application
├── procurement/          # Procurement app (core business logic)
│   ├── models.py        # Data models (Request, PO, Approval)
│   ├── views.py         # API endpoints
│   ├── serializers.py   # Data serialization
│   ├── services.py      # Business logic services
│   └── document_processing.py  # AI/OCR processing
├── users/               # User management & authentication
│   ├── models.py        # Custom User model
│   ├── views.py         # User API endpoints
│   ├── serializers.py   # User serialization
│   └── permissions.py   # Custom permissions
└── manage.py            # Django management script
```

## 🛠️ Tech Stack

| Category | Technology |
|----------|-----------|
| **Framework** | Django 5.0 & Django REST Framework 3.15 |
| **Database** | PostgreSQL (production) / SQLite (development) |
| **Authentication** | JWT (djangorestframework-simplejwt) |
| **AI/ML** | Groq API (Llama 3 models) |
| **OCR** | Tesseract & PDFPlumber |
| **API Docs** | drf-spectacular (OpenAPI 3.0) |
| **Containerization** | Docker & Docker Compose |
| **Web Server** | Gunicorn (production) |
| **Static Files** | WhiteNoise |

## 📋 Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.10+** ([Download](https://www.python.org/downloads/))
- **PostgreSQL** (optional for local development, required for production)
- **Docker & Docker Compose** (optional, for containerized deployment)

### System Dependencies (for AI/OCR features)

**macOS:**
```bash
brew install tesseract poppler
```

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr poppler-utils
```

**Windows:**
- Download Tesseract from [GitHub](https://github.com/UB-Mannheim/tesseract/wiki)
- Download Poppler from [oschwartz10612/poppler-windows](https://github.com/oschwartz10612/poppler-windows/releases)

## ⚙️ Installation & Usage

### Option A: Using Docker (Recommended)

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd procureflow-backend
   ```

2. **Configure environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env and set your values (especially GROQ_API_KEY)
   ```

3. **Build and start containers:**
   ```bash
   docker-compose up --build
   ```

4. **Access the application:**
   - API: [http://localhost:8000](http://localhost:8000)
   - Admin: [http://localhost:8000/admin](http://localhost:8000/admin)
   - Swagger UI: [http://localhost:8000/api/docs/#/](http://localhost:8000/api/docs/#/)

### Option B: Local Development Setup

1. **Clone and navigate to the repository:**
   ```bash
   git clone <repository-url>
   cd procureflow-backend
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Run database migrations:**
   ```bash
   python manage.py migrate
   ```

6. **Create initial admin user and groups:**
   ```bash
   python manage.py init_admin
   ```
   This creates:
   - Admin user: `admin` / `admin123`
   - Groups: Manager, Finance, Procurement

7. **Collect static files:**
   ```bash
   python manage.py collectstatic --noinput
   ```

8. **Run the development server:**
   ```bash
   python manage.py runserver
   ```

9. **Access the application:**
   - API: [http://localhost:8000](http://localhost:8000)
   - Admin Panel: [http://localhost:8000/admin](http://localhost:8000/admin)

## 🔧 Configuration

### Environment Variables

Copy `.env.example` to `.env` and configure the following variables:

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `SECRET_KEY` | Django secret key for cryptographic signing | - | ✅ |
| `DEBUG` | Enable debug mode (never use in production) | `True` | ✅ |
| `ALLOWED_HOSTS` | Comma-separated list of allowed hosts | `localhost,127.0.0.1` | ✅ |
| **Database** | | | |
| `DATABASE_URL` | Full database URL (overrides individual settings) | - | ⚠️ Production |
| `DB_ENGINE` | Database engine | `django.db.backends.sqlite3` | - |
| `DB_NAME` | Database name | `db.sqlite3` | - |
| `DB_USER` | Database user | - | ⚠️ PostgreSQL |
| `DB_PASSWORD` | Database password | - | ⚠️ PostgreSQL |
| `DB_HOST` | Database host | `localhost` | - |
| `DB_PORT` | Database port | `5432` | - |
| **AI Configuration** | | | |
| `GROQ_API_KEY` | API key for Groq AI services | - | ✅ AI features |
| `USE_AI_EXTRACTION` | Enable/disable AI extraction | `True` | - |
| **JWT Configuration** | | | |
| `JWT_ACCESS_TOKEN_LIFETIME` | Access token lifetime (minutes) | `60` | - |
| `JWT_REFRESH_TOKEN_LIFETIME` | Refresh token lifetime (minutes) | `1440` | - |

> **Note:** Get your Groq API key from [console.groq.com](https://console.groq.com/keys)

### Database Configuration Priority

The system uses the following priority for database configuration:

1. **`DATABASE_URL`** (highest priority) - Used in cloud deployments (Render, Heroku)
2. **Individual DB settings** (`DB_NAME`, `DB_USER`, etc.) - Used in Docker Compose
3. **SQLite fallback** (lowest priority) - Used for local development

## 📚 API Documentation

### Authentication

All API endpoints (except registration) require JWT authentication. Include the token in the Authorization header:

```bash
Authorization: Bearer <your_access_token>
```

#### Obtain Token
```http
POST /api/token/
Content-Type: application/json

{
  "username": "admin",
  "password": "admin123"
}
```

**Response:**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

#### Refresh Token
```http
POST /api/token/refresh/
Content-Type: application/json

{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

### Core API Endpoints

#### Purchase Requests

| Method | Endpoint | Description | Permission |
|--------|----------|-------------|------------|
| `GET` | `/api/v1/procurement/requests/` | List all requests | Authenticated |
| `POST` | `/api/v1/procurement/requests/` | Create new request | Can Create Request |
| `GET` | `/api/v1/procurement/requests/{id}/` | Get request details | Can View Request |
| `PATCH` | `/api/v1/procurement/requests/{id}/` | Update request | Owner/Admin |
| `DELETE` | `/api/v1/procurement/requests/{id}/` | Delete request | Owner/Admin |
| `POST` | `/api/v1/procurement/requests/{id}/approve/` | Approve current level | Can Approve |
| `POST` | `/api/v1/procurement/requests/{id}/reject/` | Reject request | Can Approve |
| `GET` | `/api/v1/procurement/requests/my_requests/` | Get user's requests | Authenticated |
| `GET` | `/api/v1/procurement/requests/pending_approvals/` | Get pending approvals | Approver |

#### AI Document Processing

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/procurement/requests/extract_proforma/` | Extract data from proforma and create request |
| `POST` | `/api/v1/procurement/requests/{id}/process_proforma/` | Process proforma for existing request |
| `POST` | `/api/v1/procurement/requests/{id}/validate_receipt/` | Validate receipt against PO |

**Example: Extract Proforma**
```bash
curl -X POST http://localhost:8000/api/v1/procurement/requests/extract_proforma/ \
  -H "Authorization: Bearer <token>" \
  -F "proforma=@/path/to/invoice.pdf" \
  -F "title=Office Supplies Request"
```

#### Purchase Orders

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/procurement/purchase-orders/` | List all POs |
| `GET` | `/api/v1/procurement/purchase-orders/{id}/` | Get PO details |
| `PATCH` | `/api/v1/procurement/purchase-orders/{id}/` | Update PO |

#### Request Items

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/procurement/items/` | List all items |
| `POST` | `/api/v1/procurement/items/` | Add item to request |
| `GET` | `/api/v1/procurement/items/{id}/` | Get item details |
| `PATCH` | `/api/v1/procurement/items/{id}/` | Update item |
| `DELETE` | `/api/v1/procurement/items/{id}/` | Delete item |

> **Note:** Items can only be modified before any approval level is passed.

#### Users

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/users/` | List all users |
| `POST` | `/api/v1/users/` | Create new user |
| `GET` | `/api/v1/users/{id}/` | Get user details |
| `PATCH` | `/api/v1/users/{id}/` | Update user |
| `GET` | `/api/v1/users/profile/` | Get current user profile |
| `PATCH` | `/api/v1/users/profile/` | Update current user profile |
| `POST` | `/api/v1/users/change_password/` | Change password |

#### Approval Configuration

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/procurement/approval-configs/` | List approval configs |
| `POST` | `/api/v1/procurement/approval-configs/` | Create approval config |
| `GET` | `/api/v1/procurement/approval-configs/{id}/` | Get config details |
| `PATCH` | `/api/v1/procurement/approval-configs/{id}/` | Update config |
| `DELETE` | `/api/v1/procurement/approval-configs/{id}/` | Delete config |

### Interactive API Documentation

Once the server is running, access the interactive documentation:

- **Swagger UI**: [http://localhost:8000/](http://localhost:8000/)
- **ReDoc**: [http://localhost:8000/api/schema/redoc/](http://localhost:8000/api/schema/redoc/)

## 💻 Development Workflow

### Project Structure

```
procureflow-backend/
├── procurement/              # Main procurement app
│   ├── models.py            # Database models
│   ├── views.py             # API views (ViewSets)
│   ├── serializers.py       # DRF serializers
│   ├── services.py          # Business logic
│   ├── document_processing.py  # AI/OCR services
│   ├── urls.py              # URL routing
│   └── admin.py             # Django admin config
├── users/                   # User management app
│   ├── models.py            # Custom User model
│   ├── views.py             # User API views
│   ├── serializers.py       # User serializers
│   ├── permissions.py       # Custom permissions
│   └── management/commands/ # Custom management commands
├── p2p_backend/             # Project configuration
│   ├── settings.py          # Django settings
│   ├── urls.py              # Root URL config
│   └── wsgi.py              # WSGI entry point
├── media/                   # Uploaded files
├── staticfiles/             # Collected static files
├── requirements.txt         # Python dependencies
├── Dockerfile               # Docker configuration
├── docker-compose.yml       # Docker Compose config
└── manage.py                # Django CLI
```

### Adding a New Feature

1. **Create/Update Models** (`models.py`)
   ```python
   class YourModel(models.Model):
       # Define fields
       pass
   ```

2. **Create Migrations**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

3. **Create Serializers** (`serializers.py`)
   ```python
   class YourModelSerializer(serializers.ModelSerializer):
       class Meta:
           model = YourModel
           fields = '__all__'
   ```

4. **Create Views** (`views.py`)
   ```python
   class YourModelViewSet(viewsets.ModelViewSet):
       queryset = YourModel.objects.all()
       serializer_class = YourModelSerializer
   ```

5. **Register URLs** (`urls.py`)
   ```python
   router.register(r'your-endpoint', YourModelViewSet)
   ```

6. **Register in Admin** (`admin.py`)
   ```python
   @admin.register(YourModel)
   class YourModelAdmin(admin.ModelAdmin):
       list_display = ['field1', 'field2']
   ```

### Database Migrations

```bash
# Create migrations after model changes
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Show migration status
python manage.py showmigrations

# Rollback migration
python manage.py migrate app_name migration_name
```

### Creating Custom Management Commands

Create a file in `app_name/management/commands/command_name.py`:

```python
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Description of your command'

    def handle(self, *args, **options):
        # Your logic here
        self.stdout.write(self.style.SUCCESS('Success message'))
```

Run with:
```bash
python manage.py command_name
```

## 🧪 Testing

### Running Tests

```bash
# Run all tests
python manage.py test

# Run tests for specific app
python manage.py test procurement

# Run with coverage
coverage run --source='.' manage.py test
coverage report
```

### Manual Testing with cURL

**Create a Purchase Request:**
```bash
curl -X POST http://localhost:8000/api/v1/procurement/requests/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Office Supplies",
    "description": "Monthly office supplies order",
    "items": [
      {
        "name": "Printer Paper",
        "quantity": 10,
        "unit_price": "25.00"
      }
    ]
  }'
```

**Approve a Request:**
```bash
curl -X POST http://localhost:8000/api/v1/procurement/requests/{id}/approve/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "comments": "Approved for procurement"
  }'
```

### AI Feature Testing

Use the provided test script:

```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Run verification script
./run_verification.sh
```

This script tests:
- Proforma extraction
- Receipt validation
- AI integration

## 🚀 Deployment

### Docker Deployment

1. **Build the image:**
   ```bash
   docker build -t procureflow-backend .
   ```

2. **Run the container:**
   ```bash
   docker run -p 8000:8000 \
     -e SECRET_KEY=your-secret-key \
     -e DATABASE_URL=postgresql://user:pass@host:5432/db \
     -e GROQ_API_KEY=your-groq-key \
     procureflow-backend
   ```

### Cloud Deployment (Render/Heroku)

1. **Set environment variables** in your cloud platform dashboard:
   - `SECRET_KEY`
   - `DATABASE_URL` (provided by platform)
   - `GROQ_API_KEY`
   - `DEBUG=False`
   - `ALLOWED_HOSTS=.onrender.com` (or your domain)

2. **Deploy:**
   - **Render**: Connect your GitHub repo and deploy
   - **Heroku**: 
     ```bash
     heroku create your-app-name
     git push heroku main
     ```

3. **Run migrations:**
   ```bash
   # Render: Runs automatically via entrypoint.sh
   # Heroku:
   heroku run python manage.py migrate
   heroku run python manage.py init_admin
   ```

### Production Checklist

- [ ] Set `DEBUG=False`
- [ ] Configure `SECRET_KEY` with a strong random value
- [ ] Set `ALLOWED_HOSTS` to your domain(s)
- [ ] Use PostgreSQL (not SQLite)
- [ ] Configure `DATABASE_URL`
- [ ] Set up HTTPS/SSL
- [ ] Configure CORS for your frontend domain
- [ ] Set up static file serving (WhiteNoise is included)
- [ ] Configure media file storage (S3, CloudFlare R2, etc.)
- [ ] Set up monitoring and logging
- [ ] Configure backup strategy for database
- [ ] Review and rotate API keys regularly

## 🔍 Troubleshooting

### Common Issues

#### Database Connection Error

**Problem:** `django.db.utils.OperationalError: could not connect to server`

**Solution:**
1. Check PostgreSQL is running: `pg_isready`
2. Verify database credentials in `.env`
3. For Docker: Ensure database container is healthy
4. Wait for database to be ready (use `wait_for_db.py` script)

#### Gunicorn Not Found (Deployment)

**Problem:** `gunicorn: not found`

**Solution:**
1. Ensure `gunicorn` is in `requirements.txt`
2. Rebuild Docker image: `docker-compose up --build`
3. Check virtual environment is activated

#### AI Features Not Working

**Problem:** AI extraction returns errors

**Solution:**
1. Verify `GROQ_API_KEY` is set correctly
2. Check API key is valid at [console.groq.com](https://console.groq.com)
3. Ensure `USE_AI_EXTRACTION=True` in `.env`
4. Check Groq API status and rate limits

#### CORS Errors

**Problem:** Frontend can't access API due to CORS

**Solution:**
1. Add frontend URL to `CORS_ALLOWED_ORIGINS` in `settings.py`
2. Add to `CSRF_TRUSTED_ORIGINS` as well
3. Restart server after changes

#### Migration Conflicts

**Problem:** `Conflicting migrations detected`

**Solution:**
```bash
# Reset migrations (development only!)
python manage.py migrate app_name zero
python manage.py migrate
```

### Debug Mode

Enable detailed error messages:

```python
# .env
DEBUG=True
```

View logs:
```bash
# Docker
docker-compose logs -f web

# Local
# Errors appear in console where runserver is running
```

## 🤝 Contributing

We welcome contributions! Please follow these guidelines:

### Code Style

- Follow [PEP 8](https://pep8.org/) for Python code
- Use meaningful variable and function names
- Add docstrings to all functions and classes
- Keep functions focused and concise

### Commit Messages

Use conventional commit format:

```
type(scope): subject

body (optional)

footer (optional)
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Example:**
```
feat(procurement): add bulk approval endpoint

Implement endpoint to approve multiple requests at once.
Includes permission checks and transaction handling.

Closes #123
```

### Pull Request Process

1. Fork the repository
2. Create a feature branch: `git checkout -b feat/your-feature`
3. Make your changes
4. Run tests: `python manage.py test`
5. Commit your changes with conventional commits
6. Push to your fork: `git push origin feat/your-feature`
7. Create a Pull Request

### Development Setup for Contributors

```bash
# Clone your fork
git clone https://github.com/your-username/procureflow-backend.git
cd procureflow-backend

# Add upstream remote
git remote add upstream https://github.com/original-repo/procureflow-backend.git

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up pre-commit hooks (if available)
pre-commit install
```

## 🔒 Security

### Best Practices

1. **Never commit sensitive data**
   - Use `.env` files (already in `.gitignore`)
   - Never hardcode API keys or passwords

2. **Keep dependencies updated**
   ```bash
   pip list --outdated
   pip install --upgrade package-name
   ```

3. **Use strong SECRET_KEY**
   ```python
   # Generate a new key
   python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
   ```

4. **Enable HTTPS in production**
   - Use SSL/TLS certificates
   - Set `SECURE_SSL_REDIRECT=True`

5. **Implement rate limiting** (consider django-ratelimit)

6. **Regular security audits**
   ```bash
   pip install safety
   safety check
   ```

### Reporting Security Issues

If you discover a security vulnerability, please email [security@example.com](mailto:security@example.com) instead of using the issue tracker.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 📞 Support

- **Documentation**: [API Docs](http://localhost:8000/api/docs/#/)
- **Issues**: [GitHub Issues](https://github.com/your-repo/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-repo/discussions)

---

**Built with ❤️ using Django and Django REST Framework**
