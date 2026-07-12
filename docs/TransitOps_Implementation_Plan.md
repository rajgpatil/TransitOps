# TransitOps — Implementation Plan

**Version:** 1.0  
**Date:** 2026-07-12  
**Status:** Draft for Review  

---

## 1. System Architecture

### 1.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    React + TypeScript                    │
│              (Vite · React Router · Axios)               │
│         Recharts (dashboards) · react-hook-form          │
└────────────────────────┬────────────────────────────────┘
                         │  REST / JSON (JWT Bearer)
┌────────────────────────▼────────────────────────────────┐
│                  FastAPI (Python 3.11+)                   │
│   Pydantic v2 · SQLAlchemy 2.0 (async) · Alembic         │
│   python-jose (JWT) · passlib[bcrypt] · uvicorn           │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│                   PostgreSQL 15+                         │
│          (ENUM types · CHECK constraints · indexes)      │
└─────────────────────────────────────────────────────────┘
```

### 1.2 Auth Strategy

| Aspect | Decision |
|--------|----------|
| Protocol | JWT (access + refresh tokens) |
| Library | `python-jose[cryptography]` + `passlib[bcrypt]` |
| Access token TTL | 30 minutes |
| Refresh token TTL | 7 days |
| Storage (frontend) | `httpOnly` cookie (refresh), memory (access) |
| Password hashing | bcrypt, 12 rounds |

### 1.3 RBAC Enforcement

- **Server-side**: FastAPI dependency that extracts JWT → resolves role → checks against a permission map per endpoint.
- **Frontend**: Role stored in auth context; used to conditionally render routes/buttons. **Not** a security boundary — all enforcement is backend.
- **Permission map**: A Python dict keyed by `(module, action)` → `set[Role]`. Checked via a reusable `require_permission(module, action)` dependency.

### 1.4 Additional Tech Justifications

| Tech | Why |
|------|-----|
| **JWT** (`python-jose`) | Stateless auth; standard for SPA ↔ API |
| **Recharts** | Lightweight React charting for KPI dashboard |
| **react-hook-form** | Performant form handling with validation |
| **Alembic** | DB migration management for SQLAlchemy |
| **uvicorn** | ASGI server for FastAPI |
| **pytest + httpx** | Async test client for FastAPI integration tests |
| **React Router v6** | Client-side routing with role guards |

### 1.5 Project Structure

```
TransitOps/
├── backend/
│   ├── alembic/              # migrations
│   ├── app/
│   │   ├── api/              # route modules
│   │   │   ├── auth.py
│   │   │   ├── vehicles.py
│   │   │   ├── drivers.py
│   │   │   ├── trips.py
│   │   │   ├── maintenance.py
│   │   │   ├── fuel.py
│   │   │   ├── expenses.py
│   │   │   ├── dashboard.py
│   │   │   └── reports.py
│   │   ├── core/             # config, security, deps
│   │   │   ├── config.py
│   │   │   ├── security.py
│   │   │   ├── permissions.py
│   │   │   └── dependencies.py
│   │   ├── models/           # SQLAlchemy models
│   │   ├── schemas/          # Pydantic v2 schemas
│   │   ├── services/         # business logic layer
│   │   └── main.py
│   ├── tests/
│   ├── alembic.ini
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── api/              # Axios clients
│   │   ├── components/       # shared UI components
│   │   ├── contexts/         # AuthContext
│   │   ├── hooks/            # custom hooks
│   │   ├── pages/            # route pages
│   │   ├── types/            # TypeScript interfaces
│   │   ├── utils/            # helpers
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── package.json
│   └── vite.config.ts
├── docs/
│   ├── TransitOps_PRD.md
│   └── TransitOps_Implementation_Plan.md
└── schemas/                  # JSON Schema files
```

---

## 2. Open Question Resolutions (Confirmed)

> ✅ **All open questions have been confirmed by stakeholders.**

| # | Open Question | Decision |
|---|---------------|----------|
| OQ-1 | **Revenue field** for ROI formula | **Confirmed.** Add a `revenue` decimal field to the Trip entity. Populated at trip completion. ROI = `(sum(trip.revenue) − (maintenance_cost + fuel_cost)) / acquisition_cost`. If null, ROI shows "N/A". |
| OQ-2 | **Driver persona scope** | **Confirmed.** Treat "Driver" as "Driver/Dispatcher" — a single role named `driver` that can create/dispatch trips, assign vehicles and drivers. No separate dispatcher role. |
| OQ-3 | **Cancelling a Draft trip** | **Confirmed.** Draft → Cancelled is allowed. No status restoration needed (vehicle/driver were never set to On Trip). Trip simply moves to Cancelled. |
| OQ-4 | **Concurrent maintenance records** | **Confirmed.** Multiple active maintenance records are allowed for one vehicle. Vehicle stays In Shop until ALL active records are closed. |
| OQ-5 | **Fleet Utilization formula** | **Confirmed.** `(Vehicles with status On Trip / Total non-Retired vehicles) × 100`. Snapshot at query time. |
| OQ-6 | **Region field** | **Confirmed.** Add a `region` string field to Vehicle. Drivers inherit region from their currently assigned vehicle for dashboard filters. |
| OQ-7 | **Numeric success targets** | **Not required.** KPIs are displayed for visibility only; no target thresholds enforced in the system. |

---

## 3. Phase Breakdown

---

### Phase 0: Project Setup & Infrastructure

**Objectives:** Initialize repos, install dependencies, configure DB, set up dev tooling.

**Backend Tasks:**
- [ ] Initialize Python project with `requirements.txt` (FastAPI, SQLAlchemy 2.0, Alembic, Pydantic v2, python-jose, passlib, uvicorn, pytest, httpx)
- [ ] Configure `app/core/config.py` (env-based settings via Pydantic `BaseSettings`)
- [ ] Set up SQLAlchemy async engine + session factory
- [ ] Initialize Alembic with async template
- [ ] Create `main.py` with CORS, exception handlers, health-check endpoint

**Frontend Tasks:**
- [ ] Scaffold React+TS app with Vite (`npx create-vite`)
- [ ] Install dependencies: react-router-dom, axios, recharts, react-hook-form
- [ ] Configure Vite proxy to backend (`/api` → `localhost:8000`)
- [ ] Set up folder structure (api/, components/, contexts/, pages/, types/)

**DB Changes:** PostgreSQL database created; no tables yet.

**API Endpoints:**
| Method | Path | Purpose |
|--------|------|---------|
| GET | `/health` | Health check |

**Edge Cases:** None.

---

### Phase 1: Authentication & RBAC

**Objectives:** Secure login, JWT issuance, role-based route protection (server + client).

**Backend Tasks:**
- [ ] Create `User` model (id, email unique, hashed_password, role enum, is_active, created_at, updated_at)
- [ ] Create Role enum: `fleet_manager`, `driver`, `safety_officer`, `financial_analyst`
- [ ] Implement password hashing (bcrypt via passlib)
- [ ] Implement JWT creation/validation (`core/security.py`)
- [ ] Implement `get_current_user` dependency
- [ ] Build permission map (`core/permissions.py`) per PRD Section 6
- [ ] Build `require_permission(module, action)` dependency
- [ ] Seed script for default admin/test users
- [ ] Alembic migration: users table

**Frontend Tasks:**
- [ ] Login page with email/password form
- [ ] AuthContext (stores user, role, tokens; provides login/logout)
- [ ] Axios interceptor for JWT attachment + refresh
- [ ] ProtectedRoute component (checks auth + role)
- [ ] Sidebar/nav showing only role-permitted modules
- [ ] Redirect unauthenticated users to login

**API Endpoints:**
| Method | Path | Purpose | Auth |
|--------|------|---------|------|
| POST | `/api/auth/login` | Login, return JWT pair | Public |
| POST | `/api/auth/refresh` | Refresh access token | Refresh token |
| GET | `/api/auth/me` | Current user profile | Bearer |

**DB Changes:** `users` table with role ENUM type.

**Business Rules Addressed:**
- BR: Only authenticated users access the app (PRD 7.1)
- BR: RBAC restricts modules/actions per role (PRD 6)

**Edge Cases:**
- Invalid credentials → 401 with generic error (no email enumeration)
- Expired token → 401, frontend triggers refresh flow
- Missing/malformed token → 401

---

### Phase 2: Core Master Data — Vehicles

**Objectives:** Full CRUD for Vehicle Registry with validation.

**Backend Tasks:**
- [ ] Create `Vehicle` model (id, registration_number unique, name, type, max_load_capacity, odometer, acquisition_cost, status enum, region, created_at, updated_at)
- [ ] Vehicle status enum: `available`, `on_trip`, `in_shop`, `retired`
- [ ] Pydantic schemas: VehicleCreate, VehicleUpdate, VehicleResponse
- [ ] CRUD service with uniqueness check on registration_number
- [ ] API routes with RBAC (Fleet Manager: full; others: read-only)
- [ ] Alembic migration: vehicles table

**Frontend Tasks:**
- [ ] Vehicle list page (table with sort/filter/search)
- [ ] Vehicle create/edit form (Fleet Manager only)
- [ ] Status badge component (color-coded per status)
- [ ] Validation: registration number required, numeric fields > 0

**API Endpoints:**
| Method | Path | Purpose | Roles |
|--------|------|---------|-------|
| GET | `/api/vehicles` | List vehicles (paginated, filterable) | All |
| GET | `/api/vehicles/{id}` | Get vehicle detail | All |
| POST | `/api/vehicles` | Create vehicle | Fleet Manager |
| PUT | `/api/vehicles/{id}` | Update vehicle | Fleet Manager |
| DELETE | `/api/vehicles/{id}` | Soft-delete / retire | Fleet Manager |

**DB Changes:** `vehicles` table with unique constraint on `registration_number`, CHECK on `max_load_capacity > 0`.

**Business Rules Addressed:**
- BR-1: Registration Number must be unique (PRD 9.1)
- BR (PRD 7.3): Status enum enforced at DB level

**Edge Cases:**
- Duplicate registration number → 409 Conflict
- Negative/zero capacity or cost → 422 Validation Error
- Attempt to delete a vehicle that is On Trip → reject

---

### Phase 3: Core Master Data — Drivers

**Objectives:** Full CRUD for Driver Management with compliance validation.

**Backend Tasks:**
- [ ] Create `Driver` model (id, name, license_number unique, license_category, license_expiry, contact_number, safety_score, status enum, created_at, updated_at)
- [ ] Driver status enum: `available`, `on_trip`, `off_duty`, `suspended`
- [ ] Pydantic schemas: DriverCreate, DriverUpdate, DriverResponse
- [ ] CRUD service with license expiry check utility
- [ ] API routes with RBAC (Safety Officer: full on compliance fields; Fleet Manager: view/edit; others: read-only)
- [ ] Alembic migration: drivers table

**Frontend Tasks:**
- [ ] Driver list page (table with compliance indicators)
- [ ] Driver create/edit form
- [ ] License expiry warning indicator (red if expired, yellow if < 30 days)
- [ ] Safety score display

**API Endpoints:**
| Method | Path | Purpose | Roles |
|--------|------|---------|-------|
| GET | `/api/drivers` | List drivers (paginated, filterable) | All |
| GET | `/api/drivers/{id}` | Get driver detail | All |
| POST | `/api/drivers` | Create driver | Safety Officer |
| PUT | `/api/drivers/{id}` | Update driver | Safety Officer, Fleet Manager |
| DELETE | `/api/drivers/{id}` | Deactivate driver | Safety Officer |
| GET | `/api/drivers/available` | Available + valid license drivers | Driver (for trip creation) |

**DB Changes:** `drivers` table with unique constraint on `license_number`.

**Business Rules Addressed:**
- BR-3: Expired license / Suspended drivers excluded from trip pool (PRD 9.3)

**Edge Cases:**
- License expiry date in the past at creation → allowed (driver exists but won't be assignable)
- Safety score bounds: 0–100, enforced via CHECK constraint

---

### Phase 4: Trip Lifecycle

**Objectives:** Full trip CRUD with dispatch validation, status transitions, and cascading vehicle/driver status changes.

**Backend Tasks:**
- [ ] Create `Trip` model (id, source, destination, vehicle_id FK, driver_id FK, cargo_weight, planned_distance, actual_distance, fuel_consumed, revenue, status enum, dispatched_at, completed_at, cancelled_at, created_at, updated_at)
- [ ] Trip status enum: `draft`, `dispatched`, `completed`, `cancelled`
- [ ] Trip service with validation logic:
  - Cargo weight ≤ vehicle max_load_capacity
  - Vehicle must be `available` (not retired/in_shop/on_trip)
  - Driver must be `available` with valid (non-expired) license, not suspended
- [ ] Dispatch action: set trip→dispatched, vehicle→on_trip, driver→on_trip (atomic transaction)
- [ ] Complete action: set trip→completed, vehicle→available, driver→available, capture final odometer/fuel/revenue
- [ ] Cancel action: if dispatched → revert vehicle/driver to available; if draft → just mark cancelled
- [ ] Alembic migration: trips table

**Frontend Tasks:**
- [ ] Trip list page (filterable by status)
- [ ] Trip creation form with:
  - Vehicle dropdown (only available, non-retired, non-in_shop)
  - Driver dropdown (only available, valid license, non-suspended)
  - Cargo weight input with live validation against selected vehicle capacity
- [ ] Trip detail page with action buttons (Dispatch / Complete / Cancel) based on current status
- [ ] Trip completion form (final odometer, fuel consumed, revenue)

**API Endpoints:**
| Method | Path | Purpose | Roles |
|--------|------|---------|-------|
| GET | `/api/trips` | List trips (paginated, filterable) | All |
| GET | `/api/trips/{id}` | Trip detail | All |
| POST | `/api/trips` | Create trip (draft) | Driver |
| PUT | `/api/trips/{id}` | Update draft trip | Driver |
| POST | `/api/trips/{id}/dispatch` | Dispatch trip | Driver |
| POST | `/api/trips/{id}/complete` | Complete trip | Driver |
| POST | `/api/trips/{id}/cancel` | Cancel trip | Driver |

**DB Changes:** `trips` table with FKs to vehicles, drivers.

**Business Rules Addressed:**
- BR-2: Retired/In Shop vehicles excluded from dispatch (PRD 9.2)
- BR-3: Expired license / Suspended drivers blocked (PRD 9.3)
- BR-4: On Trip vehicle/driver cannot be double-assigned (PRD 9.4)
- BR-5: Cargo weight ≤ max load capacity (PRD 9.5)
- BR-6: Dispatch → vehicle+driver status = On Trip (PRD 9.6)
- BR-7: Complete → vehicle+driver status = Available (PRD 9.7)
- BR-8: Cancel dispatched trip → restore vehicle+driver to Available (PRD 9.8)
- OQ-3: Cancel draft trip → just mark Cancelled, no status restoration needed

**Edge Cases:**
- Race condition: two users try to dispatch with same vehicle → DB-level check + transaction isolation
- Dispatching a trip whose vehicle was put In Shop between creation and dispatch → re-validate at dispatch time
- Completing a trip that was already completed → 409 Conflict
- Cargo weight = 0 → allowed (empty run); cargo weight < 0 → rejected

---

### Phase 5: Maintenance Workflow

**Objectives:** Maintenance log CRUD with automatic vehicle status transitions.

**Backend Tasks:**
- [ ] Create `MaintenanceLog` model (id, vehicle_id FK, description, maintenance_type, cost, status enum [active/closed], started_at, closed_at, created_at, updated_at)
- [ ] Service logic:
  - On create (active): set vehicle status → `in_shop`
  - On close: if no other active records for vehicle AND vehicle not retired → set vehicle → `available`
  - If vehicle is retired → remain retired
- [ ] Alembic migration: maintenance_logs table

**Frontend Tasks:**
- [ ] Maintenance log list page (filterable by vehicle, status)
- [ ] Create maintenance record form
- [ ] Close maintenance action button
- [ ] Visual indicator on vehicle list showing active maintenance count

**API Endpoints:**
| Method | Path | Purpose | Roles |
|--------|------|---------|-------|
| GET | `/api/maintenance` | List logs (paginated) | FM, SO, FA |
| GET | `/api/maintenance/{id}` | Log detail | FM, SO, FA |
| POST | `/api/maintenance` | Create log | Fleet Manager |
| PUT | `/api/maintenance/{id}` | Update log | Fleet Manager |
| POST | `/api/maintenance/{id}/close` | Close log | Fleet Manager |

**DB Changes:** `maintenance_logs` table with FK to vehicles.

**Business Rules Addressed:**
- BR-9: Active maintenance → vehicle In Shop (PRD 9.9)
- BR-10: Close maintenance → vehicle Available unless Retired (PRD 9.10)
- OQ-4: Multiple active records allowed; vehicle stays In Shop until all closed

**Edge Cases:**
- Creating maintenance for a vehicle already In Shop → allowed (OQ-4)
- Closing maintenance on Retired vehicle → vehicle stays Retired
- Creating maintenance for a vehicle On Trip → should block (vehicle must be available or already in shop)

---

### Phase 6: Fuel & Expense Tracking

**Objectives:** Fuel log and expense entry with per-vehicle cost aggregation.

**Backend Tasks:**
- [ ] Create `FuelLog` model (id, vehicle_id FK, trip_id FK nullable, liters, cost, date, created_by, created_at)
- [ ] Create `Expense` model (id, vehicle_id FK, trip_id FK nullable, expense_type, description, cost, date, created_by, created_at)
- [ ] Service: compute total operational cost per vehicle = sum(fuel.cost) + sum(maintenance.cost)
- [ ] Alembic migration: fuel_logs, expenses tables

**Frontend Tasks:**
- [ ] Fuel log list & entry form
- [ ] Expense list & entry form
- [ ] Per-vehicle cost summary card

**API Endpoints:**
| Method | Path | Purpose | Roles |
|--------|------|---------|-------|
| GET | `/api/fuel-logs` | List fuel logs | FM, FA, Driver |
| POST | `/api/fuel-logs` | Create fuel log | Driver, FA |
| GET | `/api/expenses` | List expenses | FM, FA |
| POST | `/api/expenses` | Create expense | FA |
| GET | `/api/vehicles/{id}/costs` | Vehicle cost summary | FM, FA |

**DB Changes:** `fuel_logs` and `expenses` tables with FKs.

**Business Rules Addressed:**
- PRD 7.7: Fuel + maintenance cost = operational cost per vehicle

**Edge Cases:**
- Negative cost/liters → rejected (CHECK constraint)
- Future date → allowed (pre-booking expenses)

---

### Phase 7: Dashboard & KPIs

**Objectives:** Real-time KPI dashboard with filters.

**Backend Tasks:**
- [ ] Dashboard service computing all KPIs:
  - Active vehicles (status = available or on_trip)
  - Available vehicles (status = available)
  - Vehicles in maintenance (status = in_shop)
  - Active trips (status = dispatched)
  - Pending trips (status = draft)
  - Drivers on duty (status = on_trip or available)
  - Fleet utilization % (OQ-5 formula)
  - Fuel efficiency = total distance / total fuel consumed
  - Operational cost = fuel + maintenance
  - Vehicle ROI (OQ-1 formula)
- [ ] Filter support: vehicle type, vehicle status, region

**Frontend Tasks:**
- [ ] Dashboard page with KPI cards (animated counters)
- [ ] Filter bar (vehicle type, status, region dropdowns)
- [ ] Recharts: utilization gauge, cost trend line, trip status pie chart
- [ ] Role-based dashboard views:
  - Fleet Manager: full view
  - Driver: own trips only
  - Safety Officer: compliance metrics
  - Financial Analyst: cost metrics

**API Endpoints:**
| Method | Path | Purpose | Roles |
|--------|------|---------|-------|
| GET | `/api/dashboard/kpis` | All KPI values (with filters) | All (role-filtered) |
| GET | `/api/dashboard/charts` | Chart data (trends) | All |

**DB Changes:** None (computed queries on existing tables).

**Business Rules Addressed:**
- PRD 7.2: Dashboard KPIs listed
- OQ-5: Utilization = on_trip / non-retired vehicles
- OQ-6: Region filter uses vehicle.region field

---

### Phase 8: Reports & Analytics

**Objectives:** Computed reports with CSV export.

**Backend Tasks:**
- [ ] Reports service:
  - Fuel efficiency per vehicle
  - Fleet utilization over time
  - Operational cost breakdown
  - Vehicle ROI (OQ-1)
- [ ] CSV export endpoint (streaming response)
- [ ] Date range filtering

**Frontend Tasks:**
- [ ] Reports page with tabbed views (Fuel, Utilization, Cost, ROI)
- [ ] Data tables with sortable columns
- [ ] Recharts visualizations per report
- [ ] CSV download button
- [ ] Date range picker

**API Endpoints:**
| Method | Path | Purpose | Roles |
|--------|------|---------|-------|
| GET | `/api/reports/fuel-efficiency` | Fuel efficiency report | FM, FA |
| GET | `/api/reports/utilization` | Fleet utilization report | FM, FA |
| GET | `/api/reports/operational-cost` | Cost report | FM, FA |
| GET | `/api/reports/vehicle-roi` | ROI report | FM, FA |
| GET | `/api/reports/export` | CSV export | FM, FA |

**DB Changes:** None.

**Business Rules Addressed:**
- PRD 7.8: Report formulas
- OQ-1: Revenue field on Trip used for ROI

**Edge Cases:**
- ROI with no revenue data → display "N/A"
- Division by zero (fuel efficiency with 0 fuel) → handle gracefully

---

### Phase 9: Hardening, Testing & Security

**Objectives:** Comprehensive test coverage, security audit, performance tuning.

**Backend Testing:**
- [ ] Unit tests for all service-layer business rules (pytest)
- [ ] Integration tests for all API endpoints (httpx AsyncClient)
- [ ] Test cases mapped to every BR (1–10) and edge case from PRD Section 14
- [ ] RBAC tests: verify each role can/cannot access each endpoint
- [ ] Input validation tests: SQL injection, XSS payloads rejected

**Frontend Testing:**
- [ ] Component unit tests (Vitest + React Testing Library)
- [ ] E2E tests for critical flows (Playwright):
  - Login → Dashboard
  - Create Vehicle → Create Trip → Dispatch → Complete
  - Maintenance → Vehicle status change
  - Report export

**Security Hardening:**
- [ ] Rate limiting on auth endpoints
- [ ] CORS restricted to frontend origin
- [ ] Input sanitization on all text fields
- [ ] SQL injection prevention (parameterized queries via SQLAlchemy)
- [ ] Audit trail: log all status transitions (who, when, from, to)
- [ ] Server-side RBAC on every endpoint (not just UI hiding)

**Non-Functional:**
- [ ] Responsive layout tested: mobile (375px), tablet (768px), desktop (1440px)
- [ ] Dashboard load time < 2s
- [ ] API response time < 500ms for list endpoints

---

### Phase 10: Deployment & Documentation

**Objectives:** Production deployment configuration and documentation.

**Tasks:**
- [ ] Dockerfile for backend (multi-stage)
- [ ] Dockerfile for frontend (nginx static serve)
- [ ] docker-compose.yml (backend + frontend + postgres)
- [ ] Environment configuration (.env.example)
- [ ] README with setup, run, and test instructions
- [ ] API documentation (FastAPI auto-generated Swagger/OpenAPI)

---

## 4. Business Rules Traceability Matrix

| BR # | Rule | Implemented In | Enforcement Layer |
|------|------|---------------|-------------------|
| BR-1 | Unique registration number | Phase 2 | DB UNIQUE + service check |
| BR-2 | Retired/In Shop excluded from dispatch | Phase 4 | Service query filter + API validation |
| BR-3 | Expired license/Suspended excluded | Phase 4 | Service validation at dispatch |
| BR-4 | On Trip vehicle/driver can't double-assign | Phase 4 | Service check + DB transaction |
| BR-5 | Cargo weight ≤ max load | Phase 4 | Service validation |
| BR-6 | Dispatch → On Trip status | Phase 4 | Service atomic transaction |
| BR-7 | Complete → Available status | Phase 4 | Service atomic transaction |
| BR-8 | Cancel dispatched → Available | Phase 4 | Service atomic transaction |
| BR-9 | Active maintenance → In Shop | Phase 5 | Service on create |
| BR-10 | Close maintenance → Available (unless Retired) | Phase 5 | Service on close |

## 5. Edge Cases Traceability (PRD Section 14)

| Edge Case | Phase | Resolution |
|-----------|-------|------------|
| Duplicate vehicle reg number | Phase 2 | 409 Conflict error |
| Dispatch with Retired/In Shop vehicle | Phase 4 | Vehicle excluded from selection; API rejects |
| Assign driver with expired license | Phase 4 | Driver excluded from pool; API rejects |
| Assign Suspended driver | Phase 4 | Driver excluded from pool; API rejects |
| Assign On Trip vehicle/driver | Phase 4 | API rejects with conflict error |
| Cargo weight > max capacity | Phase 4 | 422 Validation error |
| Cancel Draft trip | Phase 4 | Allowed; no status restoration (OQ-3) |
| Close maintenance on Retired vehicle | Phase 5 | Vehicle stays Retired |
| Second active maintenance on In Shop vehicle | Phase 5 | Allowed; stays In Shop until all closed (OQ-4) |

## 6. Testing Strategy

### Test Pyramid

```
        ┌─────────┐
        │   E2E   │  Playwright — 5-10 critical user flows
        ├─────────┤
        │  Integ  │  httpx + pytest — all API endpoints + RBAC
        ├─────────┤
        │  Unit   │  pytest (backend services) + Vitest (frontend)
        └─────────┘
```

### Coverage Targets

| Layer | Target | Tool |
|-------|--------|------|
| Backend unit (services) | 90%+ | pytest |
| Backend integration (API) | 100% of endpoints | pytest + httpx |
| Frontend unit | Key components | Vitest + RTL |
| E2E | Critical flows | Playwright |
| RBAC | Every role × every endpoint | pytest parametrize |

### Test Data Strategy
- Seed script creates test users (one per role), sample vehicles, drivers
- Each test uses isolated transactions (rolled back after test)
- Factory functions for creating test entities

---

*End of Implementation Plan*
