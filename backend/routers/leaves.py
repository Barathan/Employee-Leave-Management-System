from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import crud, schemas, models
from ..database import get_db
from ..deps import get_current_user, require_manager

router = APIRouter(prefix="/leaves", tags=["Leaves"])


def _to_leave_out(leave: models.Leave, db: Session) -> schemas.LeaveOut:
    employee = crud.get_user(db, leave.employee_id)
    data = schemas.LeaveOut.model_validate(leave)
    data.employee_name = employee.full_name if employee else None
    return data


@router.post("/apply", response_model=schemas.LeaveOut)
def apply_leave(
    leave_in: schemas.LeaveCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if leave_in.end_date < leave_in.start_date:
        raise HTTPException(status_code=400, detail="End date cannot be before start date")

    days = crud.calculate_days(leave_in.start_date, leave_in.end_date)
    field = crud.get_balance_field(leave_in.leave_type)
    if field:
        balance = getattr(current_user, field)
        if days > balance:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient {leave_in.leave_type.value} leave balance. "
                       f"Available: {balance} day(s), requested: {days} day(s)",
            )

    leave = crud.create_leave(db, current_user.id, leave_in)
    return _to_leave_out(leave, db)


@router.get("/my", response_model=List[schemas.LeaveOut])
def my_leaves(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    leaves = crud.list_leaves_for_employee(db, current_user.id)
    return [_to_leave_out(l, db) for l in leaves]


@router.get("/pending", response_model=List[schemas.LeaveOut])
def pending_leaves(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_manager),
):
    leaves = crud.list_all_leaves(db, status=models.LeaveStatusEnum.pending)
    return [_to_leave_out(l, db) for l in leaves]


@router.get("/all", response_model=List[schemas.LeaveOut])
def all_leaves(
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_manager),
):
    leaves = crud.list_all_leaves(db, status=status)
    return [_to_leave_out(l, db) for l in leaves]


@router.put("/{leave_id}/review", response_model=schemas.LeaveOut)
def review_leave_request(
    leave_id: int,
    review: schemas.LeaveReview,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_manager),
):
    leave = crud.get_leave(db, leave_id)
    if not leave:
        raise HTTPException(status_code=404, detail="Leave request not found")
    if leave.status != models.LeaveStatusEnum.pending:
        raise HTTPException(status_code=400, detail="Leave request has already been reviewed")

    leave = crud.review_leave(db, leave, current_user.id, review)
    return _to_leave_out(leave, db)


@router.get("/statistics")
def statistics(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_manager),
):
    return crud.leave_statistics(db)
