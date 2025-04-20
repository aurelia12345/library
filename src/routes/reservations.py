from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.database import get_db
from models.models import Reservation, Book, Member
from pydantic import BaseModel
from auth.auth_utils import get_current_user

router = APIRouter()

class ReservationCreate(BaseModel):
    book_id: int
    member_id: int

@router.post("/")
def create_reservation(
    reservation: ReservationCreate, 
    db: Session = Depends(get_db),
    current_user: Member = Depends(get_current_user)
):
    # Ensure member can only create reservations for themselves
    if str(reservation.member_id) != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You can only create reservations for yourself"
        )

    book = db.query(Book).filter(Book.id == reservation.book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    existing_reservation = db.query(Reservation).filter(
        Reservation.book_id == reservation.book_id,
        Reservation.member_id == reservation.member_id,
        Reservation.is_active == True
    ).first()
    
    if existing_reservation:
        raise HTTPException(status_code=400, detail="Book already reserved by you")

    db_reservation = Reservation(**reservation.dict())
    db.add(db_reservation)
    db.commit()
    db.refresh(db_reservation)
    return db_reservation

@router.get("/")
def get_reservations(
    db: Session = Depends(get_db),
    current_user: Member = Depends(get_current_user)
):
    # Admin can see all active reservations
    if current_user.is_admin:
        return db.query(Reservation).all()
    
    # Regular users see only their reservations
    return db.query(Reservation).filter(
        Reservation.member_id == current_user.id
    ).all()

@router.get("/active")
def get_active_reservations(
    db: Session = Depends(get_db),
    current_user: Member = Depends(get_current_user)
):
    if current_user.is_admin:
        return db.query(Reservation).filter(Reservation.is_active == True).all()
    
    return db.query(Reservation).filter(
        Reservation.member_id == current_user.id,
        Reservation.is_active == True
    ).all()

# Fix the cancel reservation endpoint
@router.put("/{reservation_id}/cancel")
def cancel_reservation(
    reservation_id: int, 
    db: Session = Depends(get_db),
    current_user: Member = Depends(get_current_user)
):
    reservation = db.query(Reservation).filter(Reservation.id == reservation_id).first()
    if not reservation:
        raise HTTPException(status_code=404, detail="Reservation not found")
    
    # Allow both admin and reservation owner to cancel
    if not current_user.is_admin and reservation.member_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Not authorized to cancel this reservation"
        )

    if not reservation.is_active:
        raise HTTPException(status_code=400, detail="Reservation already cancelled")

    reservation.is_active = False
    db.commit()
    db.refresh(reservation)
    return reservation