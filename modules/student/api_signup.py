from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from db import get_db
from dtos import StudentSignupRequest
from models import Student, EmailVerification, User
from helpers.password import hash_password
from helpers.email_helper import generate_verification_code, send_verification_email, get_verification_expiry
import re

def register_api_signup_route(app: FastAPI):
    @app.post("/api/student/signup")
    def student_signup(
        request: StudentSignupRequest,
        db: Session = Depends(get_db)
    ):
        # Validate password (must contain special characters)
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', request.password):
            raise HTTPException(
                status_code=400, 
                detail="Password must contain at least one special character"
            )
        
        if len(request.password) < 8:
            raise HTTPException(
                status_code=400,
                detail="Password must be at least 8 characters long"
            )
        
        # Check if email already exists (in User table for students)
        existing_user = db.query(User).filter(User.email == request.email).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Check if student number already exists
        existing_student_num = db.query(Student).filter(
            Student.student_number == request.student_number
        ).first()
        if existing_student_num:
            raise HTTPException(status_code=400, detail="Student number already registered")
        
        # Validate institutional email (optional: customize domain)
        # if not request.email.endswith("@cbsua.edu.ph"):
        #     raise HTTPException(status_code=400, detail="Must use institutional email")
        
        # Create User account first
        hashed_password = hash_password(request.password)
        new_user = User(
            email=request.email,
            password=hashed_password,
            role="Student"
        )
        
        db.add(new_user)
        db.flush()  # Flush to get the user ID without committing
        
        # Create Student profile linked to User
        new_student = Student(
            user_id=new_user.id,
            full_name=request.full_name,
            student_number=request.student_number,
            email=request.email,
            year=request.year,
            is_verified=False
        )
        
        db.add(new_student)
        db.commit()
        db.refresh(new_student)
        
        # Generate and send verification code
        code = generate_verification_code()
        verification = EmailVerification(
            student_id=new_student.id,
            code=code,
            expires_at=get_verification_expiry()
        )
        
        db.add(verification)
        db.commit()
        
        # Send email
        send_verification_email(request.email, code)
        
        return {
            "message": "Account created successfully. Please check your email for verification code.",
            "status": "success",
            "student_id": new_student.id,
            "email": new_student.email
        }

