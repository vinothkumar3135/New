# Infoez Backend (Enterprise Architecture)

A modular, scalable, enterprise-level **FastAPI** backend for **Infoez** — a local business directory and discovery platform supporting Web, Android, and iOS clients.

---

## 🏛️ Architecture Overview

The backend follows a layered domain-driven architecture:

```text
HTTP Request
     │
     ▼
API Router (app/api/v1/)
     │
     ▼
Dependency & Role Validation (app/dependencies/)
     │
     ▼
Domain Service Layer (app/services/)
     │
     ▼
Repository Layer (app/repositories/)
     │
     ▼
Database Layer (app/database/ - MongoDB via Async Motor)
```

### Layer Responsibilities

- **`app/main.py`**: FastAPI entrypoint, lifespan management, CORS, error middleware, and route mounting.
- **`app/core/`**: Configuration (`config.py`), security & hashing (`security.py`), domain constants (`constants.py`), and custom domain exceptions (`exceptions.py`).
- **`app/database/`**: Single async Motor client (`mongodb.py`), idempotent indexes (`indexes.py`), and seeder (`seed.py`).
- **`app/schemas/`**: Pydantic models with input sanitization and response normalization (preventing undefined/null frontend crashes).
- **`app/repositories/`**: Isolated database queries, pagination, projections, and aggregation pipelines.
- **`app/services/`**: Business logic, rating recalculations, Haversine geo-distance math, and notifications.
- **`app/dependencies/`**: JWT auth (`get_current_user`), optional auth, and RBAC (`require_role`).
- **`app/api/v1/`**: Thin controllers that validate requests, call services, and return responses.

---

## 📁 Directory Structure

```text
backend/
├── app/
│   ├── main.py
│   ├── core/
│   │   ├── config.py
│   │   ├── security.py
│   │   ├── constants.py
│   │   └── exceptions.py
│   ├── database/
│   │   ├── mongodb.py
│   │   ├── indexes.py
│   │   └── seed.py
│   ├── api/
│   │   ├── router.py
│   │   └── v1/
│   │       ├── auth.py
│   │       ├── businesses.py
│   │       ├── categories.py
│   │       ├── reviews.py
│   │       ├── favorites.py
│   │       ├── enquiries.py
│   │       ├── claims.py
│   │       ├── subscriptions.py
│   │       ├── notifications.py
│   │       ├── users.py
│   │       ├── uploads.py
│   │       └── health.py
│   ├── schemas/
│   │   ├── auth.py
│   │   ├── user.py
│   │   ├── business.py
│   │   ├── category.py
│   │   ├── review.py
│   │   ├── enquiry.py
│   │   ├── claim.py
│   │   ├── notification.py
│   │   └── subscription.py
│   ├── services/
│   │   ├── auth_service.py
│   │   ├── user_service.py
│   │   ├── business_service.py
│   │   ├── category_service.py
│   │   ├── review_service.py
│   │   ├── favorite_service.py
│   │   ├── enquiry_service.py
│   │   ├── claim_service.py
│   │   ├── notification_service.py
│   │   ├── subscription_service.py
│   │   └── storage_service.py
│   ├── repositories/
│   │   ├── base_repository.py
│   │   ├── user_repository.py
│   │   ├── business_repository.py
│   │   ├── category_repository.py
│   │   ├── review_repository.py
│   │   ├── favorite_repository.py
│   │   ├── enquiry_repository.py
│   │   ├── claim_repository.py
│   │   ├── notification_repository.py
│   │   ├── subscription_repository.py
│   │   └── file_repository.py
│   ├── dependencies/
│   │   ├── auth.py
│   │   ├── permissions.py
│   │   └── services.py
│   ├── utils/
│   │   ├── slug.py
│   │   ├── datetime.py
│   │   ├── distance.py
│   │   └── response.py
│   └── middleware/
│       ├── error_handler.py
│       └── request_logging.py
├── tests/
│   ├── conftest.py
│   ├── test_auth.py
│   ├── test_businesses.py
│   └── test_health.py
├── .env
├── .env.example
├── requirements.txt
├── Dockerfile
└── README.md
```

---

## ⚙️ Environment Variables

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

| Variable | Default | Description |
| :--- | :--- | :--- |
| `MONGO_URL` | `mongodb://localhost:27017` | MongoDB connection URI |
| `DB_NAME` | `localconnect-justdial` | Target MongoDB database |
| `JWT_SECRET` | `...` | Secret key for signing JWT tokens |
| `JWT_ALGORITHM` | `HS256` | JWT signature algorithm |
| `ACCESS_TOKEN_EXPIRE_DAYS` | `30` | Access token lifespan in days |
| `CORS_ORIGINS` | `*` | Allowed CORS origins (comma-separated) |
| `ENVIRONMENT` | `development` | Deployment environment |

---

## 🚀 Running Locally

### 1. Setup Virtual Environment

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate

pip install -r requirements.txt
```

### 2. Start the API Server

```bash
python -m uvicorn app.main:app --reload --port 8000
```

- **Interactive API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc Documentation**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **Health Check**: [http://localhost:8000/health](http://localhost:8000/health)

---

## 🧪 Running Tests

Run the test suite with pytest:

```bash
pytest tests/ -v
```

---

## 🛡️ API Compatibility

Every endpoint maintains 100% backward-compatibility:
- `/api/...` routes match existing Expo mobile and React web frontend calls.
- `/api/v1/...` routes provide modern versioned routes.
