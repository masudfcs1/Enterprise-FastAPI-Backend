# Enterprise FastAPI Backend (FastAPI + Prisma)

Production-ready backend built with **FastAPI** and **Prisma ORM (`prisma-client-py`)** following a **Feature-based Modular Architecture**.

---

## 🏗️ Project Architecture

```text
project/
├── app/
│   ├── main.py                  # Application entrypoint & Prisma lifespan
│   │
│   ├── core/
│   │   ├── config.py            # Pydantic Settings & environment config
│   │   ├── security.py          # Password hashing (bcrypt) & JWT tokens
│   │   └── database.py          # Prisma client lifecycle & FastAPI dependency
│   │
│   ├── modules/
│   │   ├── auth/                # Authentication & Token Management
│   │   │   ├── router.py
│   │   │   ├── service.py
│   │   │   ├── repository.py
│   │   │   ├── schema.py
│   │   │   └── dependencies.py  # JWT decoding, user extraction & RBAC
│   │   │
│   │   ├── users/               # User Management & Profiles
│   │   │   ├── router.py
│   │   │   ├── service.py
│   │   │   ├── repository.py
│   │   │   └── schema.py
│   │   │
│   │   └── products/            # Product Catalog & Inventory
│   │       ├── router.py
│   │       ├── service.py
│   │       ├── repository.py
│   │       └── schema.py
│   │
│   └── shared/
│       ├── responses.py         # Standard API envelopes (APIResponse, APIListResponse)
│       ├── pagination.py        # Pagination models and query parameters
│       └── exceptions.py        # Custom AppException hierarchy & error handlers
│
├── prisma/
│   └── schema.prisma            # Declarative Prisma database schema
│
├── tests/                       # Pytest asynchronous test suite
│   ├── conftest.py
│   ├── test_auth.py
│   ├── test_users.py
│   ├── test_products.py
│   └── test_health.py
│
├── .env
├── .env.example
├── Dockerfile                   # Multi-stage production container
├── docker-compose.yml           # App, PostgreSQL 16 & Redis 7 stack
└── pyproject.toml
```

---

## Quick Start

### 1. Prerequisites

- Python 3.12+
- Node.js (for Prisma CLI engine management) or Docker

### 2. Environment Setup

```bash
cp .env.example .env
```

### 3. Install Dependencies

```bash
pip install -e ".[dev]"
```

### 4. Prisma Setup

```bash
# Generate the Prisma Python client
prisma generate

# Push schema directly to database (development)
prisma db push

# Launch visual Prisma Studio UI (optional)
prisma studio
```

### 5. Run the Server

```bash
uvicorn app.main:app --reload --port 8000
```

- Interactive API docs (Swagger): [http://localhost:8000/docs](http://localhost:8000/docs)
- Alternative docs (ReDoc): [http://localhost:8000/redoc](http://localhost:8000/redoc)
- Health Check: [http://localhost:8000/health](http://localhost:8000/health)

---

## 🐳 Docker Deployment

Run the complete multi-container stack (FastAPI app + PostgreSQL 16 + Redis 7):

```bash
docker compose up --build -d
```

View application logs:

```bash
docker compose logs -f web
```

---

## 🧪 Testing

Execute the test suite with pytest:

```bash
pytest -v
```

With coverage:

```bash
pytest --cov=app --cov-report=term-missing
```'''
