from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from passlib.context import CryptContext
import enum  # Add this import

Base = declarative_base()

class Book(Base):
    __tablename__ = "books"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    author = Column(String, index=True)
    quantity = Column(Integer, default=1)
    available_quantity = Column(Integer, default=1)
    loans = relationship("Loan", back_populates="book")
    reservations = relationship("Reservation", back_populates="book")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class Member(Base):
    __tablename__ = "members"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    phone = Column(String(15))
    hashed_password = Column(String)
    is_admin = Column(Boolean, default=False)
    loans = relationship("Loan", back_populates="member", foreign_keys="[Loan.member_id]")
    reservations = relationship("Reservation", back_populates="member", foreign_keys="[Reservation.member_id]")

class Loan(Base):
    __tablename__ = "loans"
    
    id = Column(Integer, primary_key=True, index=True)
    book_id = Column(Integer, ForeignKey("books.id"))
    member_id = Column(Integer, ForeignKey("members.id"))
    loan_date = Column(DateTime, default=datetime.utcnow)
    return_date = Column(DateTime, nullable=False)
    is_returned = Column(Boolean, default=False)
    created_by = Column(Integer, ForeignKey("members.id"))  # Track who created the loan
    book = relationship("Book", back_populates="loans")
    member = relationship("Member", back_populates="loans", foreign_keys=[member_id])

class ReservationStatus(enum.Enum):
    WAITING = "WAITING"
    AVAILABLE = "AVAILABLE"
    COLLECTED = "COLLECTED"
    CANCELLED = "CANCELLED"

class Reservation(Base):
    __tablename__ = "reservations"
    
    id = Column(Integer, primary_key=True, index=True)
    book_id = Column(Integer, ForeignKey("books.id"))
    member_id = Column(Integer, ForeignKey("members.id"))
    reservation_date = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    status = Column(Enum(ReservationStatus), default=ReservationStatus.WAITING)
    notification_date = Column(DateTime, nullable=True)
    created_by = Column(Integer, ForeignKey("members.id"))
    book = relationship("Book", back_populates="reservations")
    member = relationship("Member", back_populates="reservations", foreign_keys=[member_id])