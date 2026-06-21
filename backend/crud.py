"""
All database access and business rules (leave-day calculation, balance
deduction, statistics aggregation) live here, kept separate from the route
handlers in routers/. This keeps endpoints thin and makes the logic unit
testable independent of FastAPI.
"""
from datetime import datetime, date
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import func

from . import models, schemas
from .security import get_password_hash


# ---------- Users ----------

def get_user_by_username(db: Session, username: str) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.username == username).first()


def get_user(db: Session, user_id: int) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.id == user_id).first()


def list_users(db: Session, role: Optional[str] = None):
    q = db.query(models.User)
    if role:
        q = q.filter(models.User.role == role)
    return q.order_by(models.User.id).all()


def create_user(db: Session, user_in: schemas.UserCreate) -> Optional[models.User]:
    if get_user_by_username(db, user_in.username):
        return None
    db_user = models.User(
        username=user_in.username,
        hashed_password=get_password_hash(user_in.password),
        full_name=user_in.full_name,
        email=user_in.email,
        role=user_in.role,
        department=user_in.department,
        designation=user_in.designation,
        phone=user_in.phone,
        manager_id=user_in.manager_id,
        annual_leave_balance=user_in.annual_leave_balance,
        sick_leave_balance=user_in.sick_leave_balance,
        casual_leave_balance=user_in.casual_leave_balance,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


# ---------- Leaves ----------

def calculate_days(start_date: date, end_date: date) -> float:
    """Inclusive day count, e.g. Mon-Mon = 1 day, Mon-Tue = 2 days."""
    delta = (end_date - start_date).days + 1
    return float(max(delta, 0))


def get_balance_field(leave_type: models.LeaveTypeEnum) -> Optional[str]:
    mapping = {
        models.LeaveTypeEnum.annual: "annual_leave_balance",
        models.LeaveTypeEnum.sick: "sick_leave_balance",
        models.LeaveTypeEnum.casual: "casual_leave_balance",
    }
    return mapping.get(leave_type)  # Unpaid leave has no balance to deduct


def create_leave(db: Session, employee_id: int, leave_in: schemas.LeaveCreate) -> models.Leave:
    days = calculate_days(leave_in.start_date, leave_in.end_date)
    db_leave = models.Leave(
        employee_id=employee_id,
        leave_type=leave_in.leave_type,
        start_date=leave_in.start_date,
        end_date=leave_in.end_date,
        days=days,
        reason=leave_in.reason,
        status=models.LeaveStatusEnum.pending,
    )
    db.add(db_leave)
    db.commit()
    db.refresh(db_leave)
    return db_leave


def get_leave(db: Session, leave_id: int) -> Optional[models.Leave]:
    return db.query(models.Leave).filter(models.Leave.id == leave_id).first()


def list_leaves_for_employee(db: Session, employee_id: int):
    return (
        db.query(models.Leave)
        .filter(models.Leave.employee_id == employee_id)
        .order_by(models.Leave.applied_on.desc())
        .all()
    )


def list_all_leaves(db: Session, status: Optional[str] = None):
    q = db.query(models.Leave)
    if status:
        q = q.filter(models.Leave.status == status)
    return q.order_by(models.Leave.applied_on.desc()).all()


def review_leave(
    db: Session, leave: models.Leave, reviewer_id: int, review: schemas.LeaveReview
) -> models.Leave:
    leave.status = review.status
    leave.review_comment = review.review_comment
    leave.reviewed_by = reviewer_id
    leave.reviewed_on = datetime.utcnow()

    if review.status == models.LeaveStatusEnum.approved:
        employee = get_user(db, leave.employee_id)
        field = get_balance_field(leave.leave_type)
        if field and employee:
            current = getattr(employee, field)
            setattr(employee, field, max(current - leave.days, 0))

    db.commit()
    db.refresh(leave)
    return leave


def leave_statistics(db: Session) -> dict:
    total = db.query(models.Leave).count()
    pending = db.query(models.Leave).filter(
        models.Leave.status == models.LeaveStatusEnum.pending
    ).count()
    approved = db.query(models.Leave).filter(
        models.Leave.status == models.LeaveStatusEnum.approved
    ).count()
    rejected = db.query(models.Leave).filter(
        models.Leave.status == models.LeaveStatusEnum.rejected
    ).count()

    by_type = (
        db.query(models.Leave.leave_type, func.count(models.Leave.id))
        .group_by(models.Leave.leave_type)
        .all()
    )
    by_dept = (
        db.query(models.User.department, func.count(models.Leave.id))
        .join(models.Leave, models.Leave.employee_id == models.User.id)
        .group_by(models.User.department)
        .all()
    )

    return {
        "total": total,
        "pending": pending,
        "approved": approved,
        "rejected": rejected,
        "by_type": {str(k.value if hasattr(k, "value") else k): v for k, v in by_type},
        "by_department": {str(k): v for k, v in by_dept},
    }
