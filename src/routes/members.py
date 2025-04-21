import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.database import get_db
from models.models import Member, pwd_context
from pydantic import BaseModel, EmailStr, constr
from auth.auth_utils import get_current_user

router = APIRouter()


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MemberCreate(BaseModel):
    name: constr(min_length=2, max_length=50, strip_whitespace=True)
    email: EmailStr
    phone: constr(pattern=r'^\+?1?\d{9,15}$', strip_whitespace=True)
    password: constr(min_length=8, max_length=50)
    is_admin: bool = False  # Default to regular user

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "John Doe",
                "email": "john.doe@example.com",
                "phone": "+1234567890",
                "password": "securepass123",
                "is_admin": False
            }
        }
    }

@router.post("/")
def create_member(
    member: MemberCreate, 
    db: Session = Depends(get_db)
):
    # Check if user exists with same email
    existing_member = db.query(Member).filter(Member.email == member.email).first()
    if existing_member:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Only allow admin creation if request comes from an existing admin
    if member.is_admin:
        if not current_user:
            raise HTTPException(status_code=403, detail="Not authorized to create admin users")
        requesting_user = db.query(Member).filter(Member.id == current_user).first()
        if not requesting_user or not requesting_user.is_admin:
            raise HTTPException(status_code=403, detail="Only admins can create other admin users")

    db_member = Member(
        name=member.name,
        email=member.email,
        phone=member.phone,
        hashed_password=pwd_context.hash(member.password),
        is_admin=member.is_admin
    )
    db.add(db_member)
    db.commit()
    db.refresh(db_member)
    return f"User {db_member.name} created successfully"


class MemberResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    phone: str
    is_admin: bool

    class Config:
        from_attributes = True

@router.get("/")
def get_members(
    db: Session = Depends(get_db),
    current_user: Member = Depends(get_current_user)
):
    if not current_user.is_admin:
        raise HTTPException(status_code=404, detail="Only admin can view members")

    if current_user.is_admin:
        members = db.query(Member).all()
        return [MemberResponse.model_validate(member) for member in members]
    return [MemberResponse.model_validate(current_user)]


@router.get("/{member_id}")
def get_member(
    member_id: int,
    db: Session = Depends(get_db),
    current_user: Member = Depends(get_current_user)
):

    if current_user.is_admin or str(member_id) == current_user.id:
        member = db.query(Member).filter(Member.id == member_id).first()
        if member is None:
            raise HTTPException(status_code=404, detail="Member not found")
        return MemberResponse.model_validate(member)
    raise HTTPException(
        status_code=403,
        detail="Not authorized to access this member's data"
    )
