import enum
from datetime import datetime, date

from sqlalchemy import (
    Column, Integer, String, Float, Date, DateTime, Enum, ForeignKey, Text
)
from sqlalchemy.orm import relationship

from .database import Base


class RoleEnum(str, enum.Enum):
    manager = "manager"
    employee = "employee"


class LeaveTypeEnum(str, enum.Enum):
    annual = "Annual"
    sick = "Sick"
    casual = "Casual"
    unpaid = "Unpaid"


class LeaveStatusEnum(str, enum.Enum):
    pending = "Pending"
    approved = "Approved"
    rejected = "Rejected"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    role = Column(Enum(RoleEnum), nullable=False, default=RoleEnum.employee)
    department = Column(String, default="General")
    designation = Column(String, default="Staff")
    phone = Column(String, default="")
    joining_date = Column(Date, default=date.today)
    manager_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    is_active = Column(Integer, default=1)  # 1 = active, 0 = deactivated

    # Leave balances (in days), per leave type
    annual_leave_balance = Column(Float, default=18.0)
    sick_leave_balance = Column(Float, default=10.0)
    casual_leave_balance = Column(Float, default=7.0)

    leaves = relationship(
        "Leave", back_populates="employee", foreign_keys="Leave.employee_id"
    )


class Leave(Base):
    __tablename__ = "leaves"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    leave_type = Column(Enum(LeaveTypeEnum), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    days = Column(Float, nullable=False)
    reason = Column(Text, nullable=False)
    status = Column(Enum(LeaveStatusEnum), default=LeaveStatusEnum.pending)
    applied_on = Column(DateTime, default=datetime.utcnow)
    reviewed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    reviewed_on = Column(DateTime, nullable=True)
    review_comment = Column(Text, default="")

    employee = relationship(
        "User", back_populates="leaves", foreign_keys=[employee_id]
    )
