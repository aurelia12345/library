from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.database import get_db
from models.models import Book, Member
from pydantic import BaseModel
from auth.auth_utils import get_current_user
from sqlalchemy import func
from datetime import datetime
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

class BookCreate(BaseModel):
    title: str
    author: str
    quantity: int = 1

@router.post("/")
def add_book(
    book: BookCreate, 
    db: Session = Depends(get_db),
    current_user: Member = Depends(get_current_user)
):
    
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Only admins can create books")
    db_book = Book(**book.dict())
    db_book.available_quantity = book.quantity
    db.add(db_book)
    db.commit()
    db.refresh(db_book)
    return db_book

@router.get("/")
def get_books(
    db: Session = Depends(get_db),
    current_user: Member = Depends(get_current_user)
):
    return db.query(Book).all()


class BookResponse(BaseModel):
    id: int
    title: str
    author: str
    quantity: int
    available_quantity: int
    next_available_date: Optional[datetime] = None

    class Config:
        from_attributes = True

@router.get("/search")
def search_books(
    query: str, 
    db: Session = Depends(get_db),
    current_user: Member = Depends(get_current_user)
):
    books = db.query(Book).filter(
        (Book.title.ilike(f"%{query}%")) |
        (Book.author.ilike(f"%{query}%"))
    ).all()

    response = []
    for book in books:
        next_return = None
        if book.available_quantity == 0:  # Only check loans if no copies available
            next_return = db.query(func.min(Loan.return_date))\
                .filter(Loan.book_id == book.id)\
                .filter(Loan.is_returned == False)\
                .scalar()

        book_response = BookResponse(
            id=book.id,
            title=book.title,
            author=book.author,
            quantity=book.quantity,
            available_quantity=book.available_quantity,
            next_available_date=next_return if next_return else "Available now" if book.available_quantity > 0 else None
        )
        response.append(book_response)

    return response

@router.delete("/{book_id}")
def delete_book(
    book_id: int,
    db: Session = Depends(get_db),
    current_user: Member = Depends(get_current_user)
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Only admins can delete books")
    
    # Check if book exists
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    # Check if book has active loans
    if any(not loan.is_returned for loan in book.loans):
        raise HTTPException(status_code=400, detail="Cannot delete book with active loans")
    
    # Check if book has active reservations
    if any(reservation.is_active for reservation in book.reservations):
        raise HTTPException(status_code=400, detail="Cannot delete book with active reservations")
    
    # Delete the book
    db.delete(book)
    db.commit()
    return {"message": f"Book '{book.title}' deleted successfully"}