from fastapi import FastAPI, HTTPException, Depends, Response
from sqlalchemy.orm import Session
from datetime import timedelta
from db import get_db
from dtos import StudentLoginRequest
from models import Student
from helpers.password import verify_password
from helpers.session import create_access_token
from config import AuthConfig

def register_api_student_login_route(app: FastAPI):
    @app.post("/api/student/login")
    def student_login(
        request: StudentLoginRequest,
        response: Response,
        db: Session = Depends(get_db)
    ):
        # Try to find student by email or student number
        student = db.query(Student).filter(
            (Student.email == request.identifier) | 
            (Student.student_number == request.identifier)
        ).first()
        
        if not student:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Verify password
        if not verify_password(request.password, student.password):
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
                "role": "student",
                "student_id": student.id,
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
