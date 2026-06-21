# Employee Leave Management System

A full-stack leave management app: **FastAPI** backend (REST API + JWT auth +
SQLite via SQLAlchemy) and a **Streamlit** frontend that consumes it.

> **Note on roles:** Standard leave-management practice (and what's implemented
> here) is: **Managers approve/reject leave**, and **Employees apply for leave**.
> Both roles can view their own profile and a history dashboard. The menu
> items match what you described, mapped to that logic:
> - **Manager:** Employee Dashboard, Leave Approval Dashboard, Register
>   Employee, Leave Statistics
> - **Employee:** Apply Leave, Leave History, My Details

## Architecture

```
leave_management/
├── backend/                  FastAPI app
│   ├── main.py                App entrypoint, CORS, router registration
│   ├── database.py            SQLAlchemy engine/session (SQLite by default)
│   ├── models.py               ORM models: User, Leave
│   ├── schemas.py               Pydantic request/response models
│   ├── security.py               Password hashing (bcrypt) + JWT
│   ├── deps.py                    Auth dependencies (get_current_user, require_manager)
│   ├── crud.py                     All business logic / DB queries
│   └── routers/
│       ├── auth.py                  POST /auth/login
│       ├── users.py                  /users/me, /users, /users/register
│       └── leaves.py                 /leaves/apply, /pending, /all, /review, /statistics
├── frontend/                 Streamlit app
│   ├── app.py                 UI: login + role-based dashboards
│   └── api_client.py            All HTTP calls to the backend, in one place
├── seed_data.py               Creates the first Manager login
├── backend/requirements.txt
└── frontend/requirements.txt
```

**Why this layout:** the API is fully decoupled from the UI — `routers/`
handles HTTP only, `crud.py` holds business rules (day-count calculation,
balance deduction, statistics), and `models.py`/`schemas.py` separate the DB
shape from the wire format. You could swap Streamlit for a React app later
without touching the backend at all.

### Roles & permissions
| Action | Employee | Manager |
|---|---|---|
| Apply for leave | ✅ | ✅ (managers can also take leave) |
| View own leave history / profile | ✅ | ✅ |
| View full employee directory | ❌ | ✅ |
| Register new employees | ❌ | ✅ |
| Approve / reject leave requests | ❌ | ✅ |
| View company-wide leave statistics | ❌ | ✅ |

Leave balances (Annual/Sick/Casual) are tracked per employee and
**automatically deducted when a manager approves** a request. Insufficient
balance blocks the application at submit time.

## Setup & Run

### 1. Backend

```bash
cd leave_management
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r backend/requirements.txt

# Create tables + a default manager login (admin / admin123)
python seed_data.py

# Start the API (from the project root, so the `backend` package resolves)
uvicorn backend.main:app --reload --port 8000
```

API docs (Swagger UI) will be at **http://localhost:8000/docs**.

### 2. Frontend

In a second terminal:

```bash
cd leave_management
source venv/bin/activate
pip install -r frontend/requirements.txt

streamlit run frontend/app.py
```

Open **http://localhost:8501**, log in with `admin / admin123`, then use
**Register Employee** to create employee accounts.

### Pointing the frontend at a different backend URL
By default the frontend calls `http://localhost:8000`. To change it, create
`frontend/.streamlit/secrets.toml`:
```toml
API_BASE_URL = "http://your-backend-host:8000"
```

## Security notes for production use
- Set `LEAVE_APP_SECRET_KEY` as an environment variable (don't use the
  built-in dev default).
- Swap SQLite for Postgres by setting `DATABASE_URL`
  (e.g. `postgresql://user:pass@host/dbname`) — no code changes needed.
- Put the backend behind HTTPS and restrict CORS `allow_origins` to your
  actual frontend domain instead of `"*"`.
- Consider short-lived access tokens + refresh tokens instead of the
  8-hour static JWT used here for simplicity.
