from datetime import timedelta
from fastapi import FastAPI, HTTPException, Response
from fastapi.params import Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from config import AuthConfig
from db import get_db
from models import User, Student
from helpers.session import authenticate_user, create_access_token
from helpers.password import verify_password


class LoginRequest(BaseModel):
    identifier: str  # email for admin/staff, student_number/email for student
    password: str
    type: str  # "student", "admin", or "staff"


def register_api_login_route(app: FastAPI):
    @app.post("/api/login")
    def login(
        request: LoginRequest,
        db: Session = Depends(get_db)
    ):
        valid_types = ["student", "admin", "staff"]
        
        if request.type not in valid_types:
            raise HTTPException(status_code=400, detail="Invalid login type. Must be 'student', 'admin', or 'staff'")
        
        if request.type in ["admin", "staff"]:
            return admin_login(db, request.identifier, request.password, request.type)
        else:
            return student_login(db, request.identifier, request.password)


def admin_login(db: Session, identifier: str, password: str, login_type: str = "admin"):
    """Handle admin/staff login"""
    user = authenticate_user(db, identifier, password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # Validate user role matches login type
    if login_type == "admin" and user.role != "Admin":
        raise HTTPException(status_code=401, detail="Invalid credentials")
    elif login_type == "staff" and user.role != "Staff":
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token_expires = timedelta(minutes=AuthConfig.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email, "role": user.role, "user_id": user.id},
        expires_delta=access_token_expires
    )

    return {
        "message": "Login successful",
        "status": "success",
        "data": {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": access_token_expires.total_seconds(),
            "user": {
                "id": user.id,
                "email": user.email,
                "role": user.role
            }
        }
    }


def student_login(db: Session, identifier: str, password: str):
    """Handle student login"""
    
    print("Login attempt for student:", identifier)
    
    # Try to find student by email or student number
    student = db.query(Student).filter(
        (Student.email == identifier) | 
        (Student.student_number == identifier)
    ).first()
    
    print("Found student:", student)
    
    if not student:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Verify password from User table
    if not verify_password(password, student.user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Check if account is verified
    if not student.is_verified:
        raise HTTPException(
            status_code=403, 
            detail="Account not verified. Please check your email for verification code."
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=AuthConfig.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": student.email,
            "role": "Student",
            "user_id": student.user_id,
            "student_number": student.student_number
        },
        expires_delta=access_token_expires
    )
    
    return {
        "message": "Login successful",
        "status": "success",
        "data": {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": access_token_expires.total_seconds(),
            "student": {
                "id": student.id,
                "full_name": student.full_name,
                "student_number": student.student_number,
                "email": student.email,
                "year": student.year
            }
        }
    }

