# ClinicQ - Outpatient Appointment & Queue Management System

A full-stack, enterprise-grade outpatient clinic appointment booking and real-time queue management system built with **FastAPI**, **PostgreSQL / SQLite**, **Redis**, and **React 18 / TypeScript / Tailwind CSS**.

---

## 🌟 Key Features

1. **Patient Appointment Booking**
   - Doctor directory by specialty and consultation room.
   - Slot generation engine: 15–20 minute consultation intervals respecting doctor operating hours.
   - **Concurrency Safe**: Concurrency protection against double-booking race conditions using partial unique constraints and database locking.

2. **Receptionist Check-In & Queue Management**
   - Fast patient lookup by appointment reference code, patient name, or phone number.
   - 1-click check-in converting scheduled appointments into numbered queue tickets (`A-001`, `B-002`, etc.).
   - Support for emergency priority tickets and manual status overrides.

3. **Doctor Consultation Console**
   - Active queue list for the authenticated doctor's department.
   - 1-click action buttons: **Call Patient**, **Start Consultation**, **Mark Completed**, **Flag No-Show**.
   - Real-time updates push notifications without manual page refresh.

4. **Public Waiting Room Live Display**
   - High-contrast, large-screen waiting room display view.
   - Shows **Currently Serving** tickets, **Next in Line**, and average estimated wait time.
   - Live WebSocket connection pushes ticket status transitions instantly.

5. **Admin Analytics Dashboard**
   - Key operational metrics: Total appointments, served patients, no-show rate, and average wait time.
   - Doctor performance breakdown (completed consultations vs avg consultation duration).
   - Real-time audit log tracking state changes.

---

## 🚀 Running Locally (Without Docker)

### Prerequisites
- Python 3.11+
- Node.js 18+ & npm
- (Optional) Redis server

### 1. Backend Setup

```bash
cd backend

# Create and activate virtual environment (if not already done)
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables (SQLite is used out of the box)
cp ../.env.example .env

# Run database migrations and seed initial data
python scripts/seed.py

# Start FastAPI backend server
python -m uvicorn app.main:app --reload --port 8000
```

The FastAPI backend will be live at:
- API Root: `http://localhost:8000`
- Interactive Swagger Docs: `http://localhost:8000/docs`
- Health Check: `http://localhost:8000/api/v1/health`

### 2. Frontend Setup

```bash
cd frontend

# Install npm packages
npm install

# Start Vite dev server on port 3000
npm run dev -- --port 3000
```

The frontend will be live at:
- Application: `http://localhost:3000`

---

## 🐳 Running with Docker Compose

When Docker is preferred:

```bash
# Build and start PostgreSQL, Redis, Backend, and Frontend
docker compose up -d --build

# Run seed data in backend container
docker compose exec backend python scripts/seed.py
```

- Frontend: `http://localhost:3000`
- Backend API: `http://localhost:8000`
- Redis: `localhost:6380`
- Postgres: `localhost:5434`

---

## 🔐 Seed User Credentials

| Role | Email | Password |
|---|---|---|
| **Admin** | `admin@clinicq.com` | `AdminPass123!` |
| **Receptionist** | `receptionist1@clinicq.com` | `ReceptPass123!` |
| **Doctor (Cardiology)** | `dr.smith@clinicq.com` | `DocPass123!` |
| **Doctor (Pediatrics)** | `dr.patel@clinicq.com` | `DocPass123!` |
| **Doctor (General Medicine)** | `dr.chen@clinicq.com` | `DocPass123!` |

*(A demo role switcher is also available in the navigation bar for instant 1-click role testing).*

---

## 🧪 Running Automated Tests

### Backend Test Suite (Pytest)
Includes unit tests, integration tests, and concurrent double-booking race condition tests:

```bash
backend/.venv/bin/pytest backend/tests -v
```

### Frontend Test Suite (Vitest)
Includes component and flow unit tests:

```bash
cd frontend && npm test
```

---

## 🛠️ Tech Stack & Architecture

- **Backend**: FastAPI, SQLAlchemy 2.0 (Async + Sync), Pydantic v2, Alembic, PostgreSQL / SQLite (aiosqlite), Redis (optional for Pub/Sub and locking), Argon2 password hashing, JWT token authentication.
- **Frontend**: React 18, Vite, TypeScript, Tailwind CSS, Lucide icons, native WebSocket hook with auto-reconnect.
- **Testing**: Pytest, Asyncio, HTTPX TestClient, Vitest, Testing Library.
