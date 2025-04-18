from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Book(Base):
    __tablename__ = "books"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    author = Column(String, index=True)
    isbn = Column(String, unique=True, index=True)
    quantity = Column(Integer, default=1)
    available_quantity = Column(Integer, default=1)
    loans = relationship("Loan", back_populates="book")
    reservations = relationship("Reservation", back_populates="book")

class Member(Base):
    __tablename__ = "members"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    phone = Column(String)
    loans = relationship("Loan", back_populates="member")
    reservations = relationship("Reservation", back_populates="member")

class Loan(Base):
    __tablename__ = "loans"
    
    id = Column(Integer, primary_key=True, index=True)
    book_id = Column(Integer, ForeignKey("books.id"))
    member_id = Column(Integer, ForeignKey("members.id"))
    loan_date = Column(DateTime, default=datetime.utcnow)
    return_date = Column(DateTime, nullable=True)
    is_returned = Column(Boolean, default=False)
    book = relationship("Book", back_populates="loans")
    member = relationship("Member", back_populates="loans")

class Reservation(Base):
    __tablename__ = "reservations"
    
    id = Column(Integer, primary_key=True, index=True)
    book_id = Column(Integer, ForeignKey("books.id"))
    member_id = Column(Integer, ForeignKey("members.id"))
    reservation_date = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    book = relationship("Book", back_populates="reservations")
    member = relationship("Member", back_populates="reservations")