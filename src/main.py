from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from auth.auth_utils import create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from datetime import timedelta
from sqlalchemy.orm import Session
from database.database import get_db, engine
from models import models
from routes import books, members, loans, reservations
from models.models import Member, pwd_context

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Library Management System")

app.include_router(books.router, prefix="/books", tags=["books"])
app.include_router(members.router, prefix="/members", tags=["members"])
app.include_router(loans.router, prefix="/loans", tags=["loans"])
app.include_router(reservations.router, prefix="/reservations", tags=["reservations"])

@app.get("/")
def read_root():
    return {"message": "Welcome to Library Management System"}

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def authenticate_user(db: Session, email: str, password: str):
    member = db.query(Member).filter(Member.email == email).first()
    if not member:
        return False
    if not verify_password(password, member.hashed_password):
        return False
    return member

@app.post("/token")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    member = authenticate_user(db, form_data.username, form_data.password)
    if not member:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(member.id)}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}