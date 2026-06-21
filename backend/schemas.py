from datetime import date, datetime
from typing import Optional, List

from pydantic import BaseModel, EmailStr, Field

from .models import RoleEnum, LeaveTypeEnum, LeaveStatusEnum


# ---------- Auth ----------

class Token(BaseModel):
    access_token: str
    token_type: str
    role: str
    user_id: int
    full_name: str


# ---------- Users ----------

class UserBase(BaseModel):
    username: str
    full_name: str
    email: EmailStr
    department: str = "General"
    designation: str = "Staff"
    phone: str = ""


class UserCreate(UserBase):
    password: str = Field(..., min_length=4)
    role: RoleEnum = RoleEnum.employee
    manager_id: Optional[int] = None
    annual_leave_balance: float = 18.0
    sick_leave_balance: float = 10.0
    casual_leave_balance: float = 7.0


class UserOut(UserBase):
    id: int
    role: RoleEnum
    manager_id: Optional[int] = None
    joining_date: date
    is_active: int
    annual_leave_balance: float
    sick_leave_balance: float
    casual_leave_balance: float

    class Config:
        from_attributes = True


# ---------- Leaves ----------

class LeaveCreate(BaseModel):
    leave_type: LeaveTypeEnum
    start_date: date
    end_date: date
    reason: str = Field(..., min_length=3)


class LeaveReview(BaseModel):
    status: LeaveStatusEnum
    review_comment: str = ""


class LeaveOut(BaseModel):
    id: int
    employee_id: int
    employee_name: Optional[str] = None
    leave_type: LeaveTypeEnum
    start_date: date
    end_date: date
    days: float
    reason: str
    status: LeaveStatusEnum
    applied_on: datetime
    reviewed_by: Optional[int] = None
    reviewed_on: Optional[datetime] = None
    review_comment: Optional[str] = ""

    class Config:
        from_attributes = True


class LeaveStatistics(BaseModel):
    total: int
    pending: int
    approved: int
    rejected: int
    by_type: dict
    by_department: dict
