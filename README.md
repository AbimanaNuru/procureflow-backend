# ProcureFlow Backend

ProcureFlow is a modern, AI-powered Procure-to-Pay system designed to streamline procurement processes. This backend repository provides the core API services, including purchase request management, multi-level approval workflows, automatic purchase order generation, and intelligent document processing.

## 🚀 Features

- **Purchase Request Management**: Create, track, and manage purchase requests.
- **Multi-Level Approval Workflow**: Configurable approval chains based on request amount and department (e.g., Manager -> Finance).
- **Automatic PO Generation**: Automatically generates Purchase Orders once a request is fully approved.
- **AI Document Processing**:
  - **Proforma Extraction**: Upload proforma invoices to automatically extract vendor details, line items, and prices.
  - **Receipt Validation**: Upload receipts to validate them against the generated PO, flagging discrepancies in prices or items.
- **Role-Based Access Control (RBAC)**: Granular permissions for Requesters, Approvers, and Admins.
- **API Documentation**: Interactive Swagger/OpenAPI documentation.

## 🛠️ Tech Stack

- **Framework**: Django 5 & Django REST Framework (DRF)
- **Database**: PostgreSQL
- **Authentication**: JWT (SimpleJWT)
- **AI/ML**: Groq API (Llama 3 models) for document intelligence
- **OCR**: Tesseract & PDFPlumber
- **Containerization**: Docker & Docker Compose

## 📋 Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.10+**
- **Docker & Docker Compose** (optional, for containerized run)
- **PostgreSQL** (if running locally without Docker)
- **System Dependencies** (for OCR/PDF processing):
  - `tesseract` (OCR engine)
  - `poppler` (PDF rendering)

### Installing System Dependencies

**macOS:**
```bash
brew install tesseract poppler
```

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr poppler-utils
```

## ⚙️ Configuration

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd procureflow-backend
   ```

2. **Environment Variables:**
   Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

   Update `.env` with your configuration:

   | Variable | Description | Default |
   |----------|-------------|---------|
   | `SECRET_KEY` | Django secret key | *Change this!* |
   | `DEBUG` | Debug mode | `True` |
   | `DB_NAME` | Database name | `procureflow_db` |
   | `DB_USER` | Database user | `postgres` |
   | `DB_PASSWORD` | Database password | - |
   | `DB_HOST` | Database host | `localhost` (or `db` for Docker) |
   | `GROQ_API_KEY` | API Key for AI features | **Required** |
   | `USE_AI_EXTRACTION` | Enable/Disable AI | `True` |

   > **Note:** Get your Groq API key from [console.groq.com](https://console.groq.com/keys).

## 🚀 Installation & Usage

### Option A: Using Docker (Recommended)

1. **Build and start the containers:**
   ```bash
   docker-compose up --build
   ```

2. **Access the application:**
   The API will be available at `http://localhost:8000`.

### Option B: Local Setup

1. **Create and activate a virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Apply migrations:**
   ```bash
   python manage.py migrate
   ```

4. **Create a superuser:**
   ```bash
   python manage.py createsuperuser
   ```

5. **Run the development server:**
   ```bash
   python manage.py runserver
   ```

## 📚 API Documentation

Once the server is running, you can access the interactive API documentation:

- **Swagger UI**: [http://localhost:8000/api/schema/swagger-ui/](http://localhost:8000/api/schema/swagger-ui/)
- **Redoc**: [http://localhost:8000/api/schema/redoc/](http://localhost:8000/api/schema/redoc/)

## 🤖 AI Features Guide

### 1. Extract Data from Proforma
Upload a proforma invoice (PDF/Image) to create a new purchase request with auto-filled data.

**Endpoint**: `POST /api/procurement/requests/extract_proforma/`
- **Body**: `proforma` (file), `title` (optional)

### 2. Validate Receipt
Upload a receipt to validate it against an approved Purchase Order.

**Endpoint**: `POST /api/procurement/requests/{id}/validate_receipt/`
- **Body**: `receipt` (file)

## 🧪 Testing

To run the verification scripts and ensure the AI workflow is functioning correctly:

1. **Ensure `.env` is configured** with a valid `GROQ_API_KEY`.
2. **Run the verification script:**
   ```bash
   # Make sure your venv is active
   ./run_verification.sh
   ```
   *Note: This script requires the server to be running or a properly configured environment to run standalone tests.*

## 🔒 Security

- **Never commit `.env` files.**
- **Keep `DEBUG=False` in production.**
- **Rotate `SECRET_KEY` and API keys regularly.**

## 📄 License

[MIT License](LICENSE)
