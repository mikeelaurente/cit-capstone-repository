import os
from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from db import get_db
from dtos import ForgotPasswordRequest
from models import Student, PasswordReset
from helpers.email_helper import generate_reset_token, send_password_reset_email, get_reset_token_expiry

def register_api_forgot_password_route(app: FastAPI):
    @app.post("/api/student/forgot-password")
    def forgot_password(
        request: ForgotPasswordRequest,
        db: Session = Depends(get_db)
    ):
        # Find student
        student = db.query(Student).filter(Student.email == request.email).first()
        if not student:
            # Don't reveal if email exists or not (security best practice)
            return {
                "message": "If the email exists, a password reset link has been sent.",
                "status": "success"
            }
        
        # Delete old reset tokens for this student
        db.query(PasswordReset).filter(
            PasswordReset.student_id == student.id
        ).delete()
        
        # Generate reset token
        token = generate_reset_token()
        password_reset = PasswordReset(
            student_id=student.id,
            token=token,
            expires_at=get_reset_token_expiry()
        )
        
        db.add(password_reset)
        db.commit()
        
        base_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
        # Send email with reset link
        send_password_reset_email(request.email, token, base_url)
        
        return {
            "message": "If the email exists, a password reset link has been sent.",
            "status": "success"
        }
