# plant_disease_backend/app/database.py

import os
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime
from dotenv import load_dotenv

from passlib.context import CryptContext

# Add a password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
# Load environment variables from your .env file
load_dotenv()

# --- THIS IS THE MAIN CHANGE ---
# Get the database URL from the environment variable
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")

if not SQLALCHEMY_DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable not found. Please set it in your .env file.")

# Create the SQLAlchemy engine for PostgreSQL
# The 'connect_args' is for SQLite only, so we remove it.
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
    connect_args={"sslmode": "require"}
)

# --- The rest of the file is the same ---
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    
# Your database model remains unchanged
class DiagnosisLog(Base):
    __tablename__ = "diagnosis_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    disease_name = Column(String, index=True)
    severity = Column(Float)
    latitude = Column(Float)
    longitude = Column(Float)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)  
    owner_id = Column(Integer, ForeignKey("users.id")) # <-- ADD THIS LINE

# plant_disease_backend/app/database.py

# 1. UPDATE THIS LINE at the top to include 'Text'
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Text

# ... (keep all your existing code, engine, User, DiagnosisLog, etc.) ...

# 2. ADD THIS CLASS at the bottom
class Feedback(Base):
    __tablename__ = "feedbacks"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

    
def create_db_and_tables():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

otp_store={}