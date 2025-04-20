from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.database import get_db
from models.models import Loan, Book, Member
from pydantic import BaseModel
from auth.auth_utils import get_current_user

router = APIRouter()

class LoanCreate(BaseModel):
    book_id: int
    member_id: int

@router.post("/")
def create_loan(
    loan: LoanCreate, 
    db: Session = Depends(get_db),
    current_user: Member = Depends(get_current_user)
):
    # Ensure member can only create loans for themselves
    if str(loan.member_id) != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You can only create loans for yourself"
        )
    
    # Rest of the validation logic
    book = db.query(Book).filter(Book.id == loan.book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    if book.available_quantity <= 0:
        raise HTTPException(status_code=400, detail="Book not available")
    loan.return_date = datetime.utcnow() + timedelta(days=14)
    db_loan = Loan(**loan.dict())
    book.available_quantity -= 1
    db.add(db_loan)
    db.commit()
    db.refresh(db_loan)
    return db_loan

@router.put("/{loan_id}/return")
def return_book(
    loan_id: int, 
    db: Session = Depends(get_db),
    current_user: Member = Depends(get_current_user)
):
    loan = db.query(Loan).filter(Loan.id == loan_id).first()
    if not loan:
        raise HTTPException(status_code=404, detail="Loan not found")
    
    if loan.is_returned:
        raise HTTPException(status_code=400, detail="Book already returned")

    # Return the book
    loan.return_date = datetime.utcnow()
    loan.is_returned = True
    loan.book.available_quantity += 1
    
    # Check for waiting reservations
    waiting_reservation = db.query(Reservation).filter(
        Reservation.book_id == loan.book_id,
        Reservation.status == ReservationStatus.WAITING,
        Reservation.is_active == True
    ).order_by(Reservation.reservation_date).first()

    if waiting_reservation:
        waiting_reservation.status = ReservationStatus.AVAILABLE
        waiting_reservation.notification_date = datetime.utcnow()
    
    db.commit()
    db.refresh(loan)
    return loan

@router.get("/borrowed")
def get_borrowed_books(
    db: Session = Depends(get_db),
    current_user: Member = Depends(get_current_user)
):
    # Admin can see all active loans, regular users see only their loans
    if current_user.is_admin:
        return db.query(Loan).filter(Loan.is_returned == False).all()
    
    return db.query(Loan).filter(
        Loan.member_id == current_user.id,
        Loan.is_returned == False
    ).all()

# Add a new endpoint for all loans history
@router.get("/history")
def get_loans_history(
    db: Session = Depends(get_db),
    current_user: Member = Depends(get_current_user)
):
    if current_user.is_admin:
        return db.query(Loan).all()
    
    return db.query(Loan).filter(
        Loan.member_id == current_user.id
    ).all()