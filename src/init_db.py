from database.database import engine, SessionLocal, Base
from models.models import Member, Book, Loan, Reservation
import bcrypt

def init_db():
    Base.metadata.drop_all(bind=engine)
    print("Creating database tables...")
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # Create admin user with bcrypt directly
        password = "admin123".encode('utf-8')
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(password, salt).decode('utf-8')
        
        admin = Member(
            name="Admin User",
            email="admin@library.com",
            phone="+1234567890",
            hashed_password=hashed_password,
            is_admin=True
        )
        db.add(admin)
        db.commit()
        print("Admin user created successfully")
    except Exception as e:
        print(f"Error creating admin user: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("Initializing database...")
    init_db()
    print("Database initialization completed")