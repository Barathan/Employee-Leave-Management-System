from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import crud, schemas, models
from ..database import get_db
from ..deps import get_current_user, require_manager

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=schemas.UserOut)
def read_me(current_user: models.User = Depends(get_current_user)):
    return current_user


@router.get("", response_model=List[schemas.UserOut])
def list_employees(
    role: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_manager),
):
    """Manager-only: full employee directory, optionally filtered by role."""
    return crud.list_users(db, role=role)


@router.get("/{user_id}", response_model=schemas.UserOut)
def get_user_detail(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    # A manager can view anyone; an employee can only view their own profile.
    if current_user.role != models.RoleEnum.manager and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    user = crud.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.post("/register", response_model=schemas.UserOut)
def register_employee(
    user_in: schemas.UserCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_manager),
):
    """Manager-only: register a new employee (or manager) account."""
    existing = crud.get_user_by_username(db, user_in.username)
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")
    if user_in.manager_id is None and user_in.role == models.RoleEnum.employee:
        user_in.manager_id = current_user.id

    new_user = crud.create_user(db, user_in)
    if not new_user:
        raise HTTPException(status_code=400, detail="Could not create user")
    return new_user
