from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List
from app import economic_service
# We removed BaseModel from here because it's now in schemas.py
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema

import traceback
from fastapi.responses import JSONResponse
import random
from app.database import otp_store
import os
# Import services, database components, AND the new schemas
from app import prediction_service, severity_service, treatment_service, database, schemas, auth

# This line remains the same
database.create_db_and_tables()

app = FastAPI(title="AgroDoctor API", description="API for Plant Disease Prediction and Analysis")
# --- ADD THIS CORS MIDDLEWARE SECTION ---
# This allows your frontend (running on any port) to communicate with your backend.
origins = ["*"]  # For development, allow all origins.

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], # Allow all methods
    allow_headers=["*"], # Allow all headers
)

# --- NEW: Mail Sending Configuration ---
conf = None
if os.getenv("MAIL_USERNAME"):
    conf = ConnectionConfig(
        MAIL_USERNAME=os.getenv("MAIL_USERNAME"),
        MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),
        MAIL_FROM=os.getenv("MAIL_FROM"),
        MAIL_PORT=int(os.getenv("MAIL_PORT", 587)),
        MAIL_SERVER=os.getenv("MAIL_SERVER"),
        MAIL_STARTTLS=True,
        MAIL_SSL_TLS=False,
        USE_CREDENTIALS=True,
        VALIDATE_CERTS=True
    )

# --- END NEW ---

# plant_disease_backend/main.py

# Change your import to this:
from app.database import Feedback, get_db  # Import Feedback from database.py

# ... (keep schemas import) ...
from app.schemas import FeedbackCreate

# ... (rest of the code) ...

@app.post("/submit-feedback/")
async def submit_feedback(feedback_data: FeedbackCreate, db: Session = Depends(get_db)):
    # Create the database object
    new_feedback = Feedback(
        name=feedback_data.name,
        email=feedback_data.email,
        message=feedback_data.message
    )
    
    db.add(new_feedback)
    db.commit()
    db.refresh(new_feedback)
    
    return {"message": "Feedback saved successfully"}
# --- API Endpoints ---
# --- AUTHENTICATION ENDPOINTS ---
@app.post("/token", response_model=schemas.Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    user = auth.get_user(db, username=form_data.username)
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/users/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(database.get_db)):
    db_user_by_username = auth.get_user(db, username=user.username)
    if db_user_by_username:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    # Check for existing email
    db_user_by_email = db.query(database.User).filter(database.User.email == user.email).first()
    if db_user_by_email:
        raise HTTPException(status_code=400, detail="Email already registered")
        
    hashed_password = auth.get_password_hash(user.password)
    db_user = database.User(
        username=user.username, 
        hashed_password=hashed_password,
        email=user.email,
        name=user.name
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# --- NEW: Password Recovery Endpoints ---
@app.post("/password-recovery/{email}")
async def recover_password(email: str, background_tasks: BackgroundTasks, db: Session = Depends(database.get_db)):
    user = db.query(database.User).filter(database.User.email == email).first()
    if not conf:
        raise HTTPException(status_code=500, detail="Mail service not configured")

    if not user:
        raise HTTPException(status_code=404, detail="The user with this email does not exist in the system.")

    password_reset_token = auth.create_access_token(
        data={"sub": user.username}, expires_delta=timedelta(minutes=30)
    )
    
    message = MessageSchema(
        subject="Password recovery for AgroDoctor AI",
        recipients=[email],
        body=f"Click the link to reset your password: http://127.0.0.1:5000/reset-password?token={password_reset_token}",
        subtype="html",
        sender=("AgroDoctor AI", os.getenv("MAIL_FROM"))  # <-- ADD THIS LINE
    )

    fm = FastMail(conf)
    background_tasks.add_task(fm.send_message, message)
    return {"message": "Password recovery email sent"}

@app.post("/reset-password/")
async def reset_password(token: str, new_password: str, db: Session = Depends(database.get_db)):
    user = await auth.get_current_user(token=token, db=db)
    if not user:
        raise HTTPException(status_code=400, detail="Invalid token")
    
    user.hashed_password = auth.get_password_hash(new_password)
    db.commit()
    return {"message": "Password updated successfully"}
# --- END NEW ---

# --- CORE APP ENDPOINTS (some are now protected) ---
@app.get("/users/me/", response_model=schemas.User)
async def read_users_me(current_user: schemas.User = Depends(auth.get_current_user)):
    return current_user


@app.post("/analyze-plant/")
async def analyze_plant_image(file: UploadFile = File(...)):
    image_bytes = await file.read()
    result = prediction_service.predict_disease(image_bytes)
    severity = severity_service.analyze_severity(image_bytes)

    return {
        "disease_name": result["disease_name"],
        "confidence": f"{result['confidence']:.2%}",
        "severity_percentage": f"{severity:.2f}%"
    }


@app.get("/get-treatment/", summary="Get treatment plan for a disease")
async def get_treatment(disease_name: str, severity: float, language: str = "English"):
    """
    Generates a treatment plan from the Gemini API based on the disease name and its severity.
    """
    # Now we pass the severity to the service function
    plan = treatment_service.get_treatment_plan(disease_name, severity, language)
    return {"treatment_plan": plan}
# --- UPDATED MAPPING ENDPOINTS ---

@app.post("/log-diagnosis/", summary="Log a diagnosis for a user")
async def log_diagnosis(log: schemas.DiagnosisLogCreate, db: Session = Depends(database.get_db), current_user: schemas.User = Depends(auth.get_current_user)):
    db_log = database.DiagnosisLog(
        disease_name=log.disease_name,
        severity=log.severity,
        latitude=log.latitude,
        longitude=log.longitude,
        timestamp=datetime.utcnow(),
        owner_id=current_user.id
    )
    db.add(db_log)
    db.commit()
    db.refresh(db_log)
    return {"status": "success", "log_id": db_log.id}


@app.get("/get-hotspots/", summary="Get disease hotspots from the last 7 days", response_model=List[schemas.DiagnosisLog])
# THIS IS THE LINE THAT FIXES THE ERROR.
# We changed database.DiagnosisLog to schemas.DiagnosisLog
async def get_hotspots(db: Session = Depends(database.get_db)):
    time_threshold = datetime.utcnow() - timedelta(days=7)
    hotspots = db.query(database.DiagnosisLog).filter(database.DiagnosisLog.timestamp >= time_threshold).all()
    return hotspots

@app.get("/history/me/", summary="Get diagnosis history for the current user", response_model=List[schemas.DiagnosisLog])
async def get_my_history(db: Session = Depends(database.get_db), current_user: schemas.User = Depends(auth.get_current_user)):
    history = db.query(database.DiagnosisLog).filter(database.DiagnosisLog.owner_id == current_user.id).order_by(database.DiagnosisLog.timestamp.desc()).all()
    return history

@app.get("/calculate-impact/", summary="Calculate potential financial impact of a disease")
async def calculate_impact(disease_name: str, severity: float):
    """
    Takes disease name and severity percentage to calculate potential yield
    and financial loss.
    """
    impact_data = economic_service.calculate_economic_impact(disease_name, severity)
    return impact_data

@app.get("/view-feedbacks/")
def read_feedbacks(db: Session = Depends(get_db)):
    feedbacks = db.query(Feedback).all()
    return [
        {
            "id": f.id,
            "name": f.name,
            "email": f.email,
            "message": f.message
        }
        for f in feedbacks
    ]
@app.post("/forgot-password-otp")
def forgot_password_otp(email: str, db: Session = Depends(database.get_db)):
    user = db.query(database.User).filter(database.User.email == email).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    otp = random.randint(100000, 999999)

    database.otp_store[email] = {
        "otp": otp,
        "expires": datetime.utcnow() + timedelta(minutes=5)
    }

    # 🔥 IMPORTANT FOR TESTING (CHECK RENDER LOGS)
    print("🔐 PASSWORD RESET OTP:", otp)

    return {"message": "OTP generated successfully"}


@app.post("/reset-password-otp")
def reset_password_otp(
    email: str,
    otp: int,
    new_password: str,
    db: Session = Depends(database.get_db)
):
    data = database.otp_store.get(email)

    if not data:
        raise HTTPException(status_code=400, detail="OTP not requested")

    if datetime.utcnow() > data["expires"]:
        del database.otp_store[email]
        raise HTTPException(status_code=400, detail="OTP expired")

    if data["otp"] != otp:
        raise HTTPException(status_code=400, detail="Invalid OTP")

    user = db.query(database.User).filter(database.User.email == email).first()
    user.hashed_password = auth.get_password_hash(new_password)
    db.commit()

    del database.otp_store[email]

    return {"message": "Password reset successful"}
