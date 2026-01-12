from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from db import get_db
from dtos import ResetPasswordRequest
from models import Student, PasswordReset
from helpers.password import hash_password
from datetime import datetime
import re

def register_api_reset_password_route(app: FastAPI):
    @app.post("/api/student/reset-password")
    def reset_password(
        request: ResetPasswordRequest,
        db: Session = Depends(get_db)
    ):
        # Validate passwords match
        if request.new_password != request.confirm_password:
            raise HTTPException(status_code=400, detail="Passwords do not match")
        
        # Validate password strength
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', request.new_password):
            raise HTTPException(
                status_code=400,
                detail="Password must contain at least one special character"
            )
        
        if len(request.new_password) < 8:
            raise HTTPException(
                status_code=400,
                detail="Password must be at least 8 characters long"
            )
        
        # Find reset token
        reset_token = db.query(PasswordReset).filter(
            PasswordReset.token == request.token
        ).first()
        
        if not reset_token:
            raise HTTPException(status_code=400, detail="Invalid or expired reset token")
        
        # Check if token expired
        if datetime.utcnow() > reset_token.expires_at:
            db.delete(reset_token)
            db.commit()
            raise HTTPException(status_code=400, detail="Reset token has expired")
        
        # Find student
        student = db.query(Student).filter(Student.id == reset_token.student_id).first()
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")
        
        # Update password
        student.password = hash_password(request.new_password)
        
        # Delete reset token
        db.delete(reset_token)
        
        db.commit()
        
        return {
            "message": "Password reset successfully. You can now login with your new password.",
            "status": "success"
        }
