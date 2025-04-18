from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.database import get_db
from models.models import Loan, Book, Member
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()

class LoanCreate(BaseModel):
    book_id: int
    member_id: int

@router.post("/")
def create_loan(loan: LoanCreate, db: Session = Depends(get_db)):
    book = db.query(Book).filter(Book.id == loan.book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    if book.available_quantity <= 0:
        raise HTTPException(status_code=400, detail="Book not available")
    
    member = db.query(Member).filter(Member.id == loan.member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    db_loan = Loan(**loan.dict())
    book.available_quantity -= 1
    
    db.add(db_loan)
    db.commit()
    db.refresh(db_loan)
    return db_loan

@router.put("/{loan_id}/return")
def return_book(loan_id: int, db: Session = Depends(get_db)):
    loan = db.query(Loan).filter(Loan.id == loan_id).first()
    if not loan:
        raise HTTPException(status_code=404, detail="Loan not found")
    if loan.is_returned:
        raise HTTPException(status_code=400, detail="Book already returned")

    loan.return_date = datetime.utcnow()
    loan.is_returned = True
    loan.book.available_quantity += 1
    
    db.commit()
    db.refresh(loan)
    return loan

@router.get("/borrowed")
def get_borrowed_books(db: Session = Depends(get_db)):
    return db.query(Loan).filter(Loan.is_returned == False).all()