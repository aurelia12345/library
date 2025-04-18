from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.database import get_db
from models.models import Book
from pydantic import BaseModel

router = APIRouter()

class BookCreate(BaseModel):
    title: str
    author: str
    isbn: str
    quantity: int = 1

@router.post("/")
def create_book(book: BookCreate, db: Session = Depends(get_db)):
    db_book = Book(**book.dict())
    db_book.available_quantity = book.quantity
    db.add(db_book)
    db.commit()
    db.refresh(db_book)
    return db_book

@router.get("/")
def get_books(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(Book).offset(skip).limit(limit).all()

@router.get("/search")
def search_books(query: str, db: Session = Depends(get_db)):
    return db.query(Book).filter(
        (Book.title.ilike(f"%{query}%")) |
        (Book.author.ilike(f"%{query}%")) |
        (Book.isbn.ilike(f"%{query}%"))
    ).all()