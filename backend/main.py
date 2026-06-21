from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import Base, engine
from .routers import auth, users, leaves

# Create tables on startup (fine for SQLite/demo; use Alembic migrations
# for production schema changes against Postgres/MySQL).
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Employee Leave Management System",
    description="Backend API for managing employees, leave applications and approvals.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(leaves.router)


@app.get("/", tags=["Health"])
def root():
    return {"message": "Employee Leave Management API is running", "docs": "/docs"}
