from pydantic import BaseModel
from datetime import datetime
from typing import Optional

# ---------------- USERS ----------------
class UserBase(BaseModel):
    username: str
    email: str
    name: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int

    class Config:
        orm_mode = True


# ---------------- AUTH ----------------
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None


# ---------------- DIAGNOSIS LOGS ----------------
class DiagnosisLogCreate(BaseModel):
    disease_name: str
    severity: float
    latitude: float
    longitude: float

class DiagnosisLog(BaseModel):
    id: int
    disease_name: str
    severity: float
    latitude: Optional[float]
    longitude: Optional[float]
    timestamp: datetime

    class Config:
        orm_mode = True


# ---------------- FEEDBACK ----------------
class FeedbackCreate(BaseModel):
    name: str
    email: str
    message: str
