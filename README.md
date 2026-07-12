# TransitOps

> Fleet & Transport Operations Management System — REST API backend.

---

## Table of Contents

1. [Overview](#overview)
2. [Tech Stack](#tech-stack)
3. [Project Structure](#project-structure)
4. [Local Development (without Docker)](#local-development-without-docker)
5. [Docker Setup](#docker-setup)
6. [Environment Variables](#environment-variables)
7. [Database Migrations](#database-migrations)
8. [Running Tests](#running-tests)
9. [API Documentation](#api-documentation)
10. [Roles & Permissions](#roles--permissions)
11. [Phase 9 — Security Hardening (Deferred)](#phase-9--security-hardening-deferred)

---

## Overview

TransitOps is a back-end API for managing a commercial vehicle fleet. It covers:

- **Master data** — Vehicles and Drivers registries  
- **Trip lifecycle** — Draft → Dispatch → Complete / Cancel with atomic state transitions  
- **Maintenance workflow** — Open / close shop logs with multiple concurrent logs supported  
- **Fuel & expense tracking** — Per-vehicle fuel logs and ad-hoc expenses  
- **Dashboard KPIs** — Real-time fleet metrics (utilization, efficiency, ROI) with role-filtered views  
- **Reports & analytics** — Per-vehicle fuel efficiency, daily utilization, operational cost, and ROI with CSV export  

---

## Tech Stack

| Layer | Technology |
|---|---|
| Runtime | Python 3.12 |
| Framework | FastAPI |
| ORM | SQLAlchemy 2 (async) |
| Database | PostgreSQL 15 |
| Migrations | Alembic |
| Auth | JWT (python-jose) + bcrypt |
| Testing | pytest + pytest-asyncio + HTTPX |
| Container | Docker / Docker Compose |

---

## Project Structure

```
TransitOps/
├── backend/
│   ├── app/
│   │   ├── api/          # FastAPI routers
│   │   ├── core/         # Config, DB, auth, RBAC
│   │   ├── models/       # SQLAlchemy ORM models
│   │   ├── schemas/      # Pydantic request/response schemas
│   │   └── services/     # Business logic layer
│   ├── alembic/          # Migration scripts
│   ├── tests/            # Integration tests
│   ├── Dockerfile
│   └── requirements.txt
├── docker-compose.yml
├── .env.example
└── docs/
```

---

## Local Development (without Docker)

### Prerequisites

- Python 3.12+
- PostgreSQL 15 running locally on port **5435**

### Setup

```bash
# 1. Clone the repo
git clone https://github.com/your-org/TransitOps.git
cd TransitOps/backend

# 2. Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp ../.env.example .env
# Edit .env — set POSTGRES_PASSWORD and SECRET_KEY at minimum

# 5. Run database migrations
python -m alembic upgrade head

# 6. Start the development server
uvicorn app.main:app --reload --port 8000
```

The API will be available at **http://localhost:8000**.

---

## Docker Setup

The root `docker-compose.yml` brings up Postgres and the backend in one command.

```bash
# From the project root:
cp .env.example .env
# Edit .env with your values

docker compose up --build
```

- **PostgreSQL** → `localhost:5435`
- **Backend API** → `http://localhost:8000`

Alembic migrations run automatically before the server starts.

### Stopping

```bash
docker compose down          # keeps the volume
docker compose down -v       # also removes the Postgres data volume
```

---

## Environment Variables

All required variables are documented in [`.env.example`](.env.example).  
Copy it to `.env` and fill in your values:

| Variable | Required | Default | Description |
|---|---|---|---|
| `POSTGRES_SERVER` | Yes | `localhost` | DB hostname |
| `POSTGRES_PORT` | Yes | `5435` | DB port |
| `POSTGRES_USER` | Yes | `postgres` | DB username |
| `POSTGRES_PASSWORD` | Yes | `postgres` | DB password |
| `POSTGRES_DB` | Yes | `transitops` | DB name |
| `DATABASE_URL` | No | Auto-assembled | Full asyncpg URL (overrides individual fields) |
| `SECRET_KEY` | **Critical** | — | JWT signing secret. **Must be changed in production.** |
| `ALGORITHM` | No | `HS256` | JWT algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | `30` | Access token TTL in minutes |
| `REFRESH_TOKEN_EXPIRE_DAYS` | No | `7` | Refresh token TTL in days |
| `BACKEND_CORS_ORIGINS` | No | `http://localhost:3000,...` | Comma-separated allowed origins |

---

## Database Migrations

Migrations are managed with **Alembic**, located in `backend/alembic/`.

```bash
# From backend/ directory

# Apply all pending migrations
python -m alembic upgrade head

# Roll back one step
python -m alembic downgrade -1

# Check current revision
python -m alembic current

# Generate a new migration (after modifying models)
python -m alembic revision --autogenerate -m "describe change"
```

---

## Running Tests

Tests require a live PostgreSQL database (uses the same `DATABASE_URL` from `.env`).

```bash
cd backend

# Run all tests
pytest

# Run with coverage report
pytest --cov=app --cov-report=term-missing

# Run a specific test file
pytest tests/test_dashboard.py -v

# Run a specific test
pytest tests/test_reports.py::test_reports_vehicle_roi -v
```

### Test Coverage by Module

| Test File | Covers |
|---|---|
| `test_auth.py` | Registration, login, token refresh, JWT edge cases |
| `test_vehicles.py` | Vehicle CRUD, uniqueness, RBAC |
| `test_drivers.py` | Driver CRUD, license expiry, availability endpoint |
| `test_trips.py` | Trip creation, dispatch, complete, cancel, business rules |
| `test_maintenance.py` | Shop logs, multiple concurrent logs, close log |
| `test_finance.py` | Fuel logs, expenses |
| `test_security.py` | SQL injection probes, auth header edge cases |
| `test_dashboard.py` | KPI calculations, role filtering, chart data |
| `test_reports.py` | All report types, ROI fallback, CSV export, RBAC |

---

## API Documentation

When the server is running, visit:

- **Swagger UI** → http://localhost:8000/docs  
- **ReDoc** → http://localhost:8000/redoc  
- **OpenAPI JSON** → http://localhost:8000/api/openapi.json  

---

## Roles & Permissions

| Role | Key Capabilities |
|---|---|
| `fleet_manager` | Full CRUD on vehicles, maintenance, expenses; read-only trips/drivers; full dashboard & reports |
| `driver` | Create/update own trips; read vehicles/drivers; own-view dashboard only |
| `safety_officer` | Full CRUD on drivers (compliance); read vehicles/trips/maintenance; dashboard (no cost fields) |
| `financial_analyst` | Read-only all resources; full dashboard & reports including ROI |

---

## Phase 9 — Security Hardening (Deferred)

> **⚠️ Phase 9 is intentionally deferred and NOT implemented in this version.**

The following items are scoped for a dedicated security hardening pass:

- [ ] Rate limiting on authentication endpoints (`/api/auth/login`, `/api/auth/register`)
- [ ] Structured audit-trail logging for state-changing actions (dispatch, cancel, maintenance close)
- [ ] Full RBAC coverage sweep — automated matrix tests for every endpoint × role combination
- [ ] Input sanitisation review and SQL injection hardening beyond current scope
- [ ] Secrets management integration (e.g., AWS Secrets Manager / Vault) for production deployments
- [ ] HTTPS / TLS termination configuration guidance

These items will be addressed in a follow-up PR labelled **`phase/9-hardening`**.
