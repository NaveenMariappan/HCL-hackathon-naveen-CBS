from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr

from app import models
from app.database import get_db
from app.security import hash_password, verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["Authentication"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str

@router.post("/register")
def register_user(request: RegisterRequest, db: Session = Depends(get_db)):
    # Check if user already exists
    existing_user = db.query(models.User).filter(models.User.email == request.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")

    # Validate password length
    if len(request.password) > 72:
        raise HTTPException(status_code=400, detail="Password too long. Max 72 characters allowed.")

    # Create new user
    new_user = models.User(
        email=request.email,
        full_name=request.full_name,
        password=hash_password(request.password)
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"message": "User registered successfully", "user_id": new_user.id}
#Admin Creation Endpoint
class AdminCreateRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str = "Admin User"

@router.post("/create-admin")
def create_admin(request: AdminCreateRequest, db: Session = Depends(get_db)):
    # Check if admin already exists
    existing_user = db.query(models.User).filter(models.User.email == request.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Admin already exists")

    # Create admin user
    new_admin = models.User(
        email=request.email,
        full_name=request.full_name,
        password=hash_password(request.password),
        role="admin"
    )
    db.add(new_admin)
    db.commit()
    return {"message": "Admin created successfully", "admin_email": new_admin.email}

@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # Fetch user by email
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token({"sub": user.email})
    return {"access_token": token, "token_type": "bearer"}

@router.get("/me")
def get_profile(token: str = Depends(oauth2_scheme)):
    return {"message": "Protected route accessed!", "your_token": token}
