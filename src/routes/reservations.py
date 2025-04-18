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
    current_user: str = Depends(get_current_user)
):
    book = db.query(Book).filter(Book.id == reservation.book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    member = db.query(Member).filter(Member.id == reservation.member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    # Add authorization check
    if str(member.id) != current_user:
        raise HTTPException(
            status_code=403,
            detail="Not authorized to make reservation for this member"
        )

    existing_reservation = db.query(Reservation).filter(
        Reservation.book_id == reservation.book_id,
        Reservation.member_id == reservation.member_id,
        Reservation.is_active == True
    ).first()
    
    if existing_reservation:
        raise HTTPException(status_code=400, detail="Book already reserved by this member")

    db_reservation = Reservation(**reservation.dict())
    db.add(db_reservation)
    db.commit()
    db.refresh(db_reservation)
    return db_reservation

@router.put("/{reservation_id}/cancel")
def cancel_reservation(
    reservation_id: int, 
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    reservation = db.query(Reservation).filter(Reservation.id == reservation_id).first()
    if not reservation:
        raise HTTPException(status_code=404, detail="Reservation not found")
    
    # Add authorization check
    if str(reservation.member_id) != current_user:
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