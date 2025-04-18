from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.database import get_db
from models.models import Member
from pydantic import BaseModel, EmailStr

router = APIRouter()

class MemberCreate(BaseModel):
    name: str
    email: str
    phone: str

@router.post("/")
def create_member(member: MemberCreate, db: Session = Depends(get_db)):
    db_member = Member(**member.dict())
    db.add(db_member)
    db.commit()
    db.refresh(db_member)
    return db_member

@router.get("/")
def get_members(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(Member).offset(skip).limit(limit).all()