"""
Run this once to create the database tables and a default Manager account
so you have something to log in with on first run.

Usage (from the project root, leave_management/):
    python seed_data.py
"""
from backend.database import SessionLocal, Base, engine
from backend import models
from backend.security import get_password_hash

Base.metadata.create_all(bind=engine)


def seed():
    db = SessionLocal()
    existing = db.query(models.User).filter(models.User.username == "admin").first()
    if existing:
        print("Default manager account already exists (username: admin).")
        db.close()
        return

    manager = models.User(
        username="admin",
        hashed_password=get_password_hash("admin123"),
        full_name="System Administrator",
        email="admin@company.com",
        role=models.RoleEnum.manager,
        department="Management",
        designation="HR Manager",
        annual_leave_balance=24,
        sick_leave_balance=12,
        casual_leave_balance=10,
    )
    db.add(manager)
    db.commit()
    print("Default manager created:")
    print("  username: admin")
    print("  password: admin123")
    print("Please change this password / create your own manager after first login.")
    db.close()


if __name__ == "__main__":
    seed()
