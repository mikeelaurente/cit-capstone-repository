from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from db import get_db
from dtos import StudentVerifyRequest
from models import Student, EmailVerification
from datetime import datetime

def register_api_verify_route(app: FastAPI):
    @app.post("/api/student/verify")
    def verify_account(
        request: StudentVerifyRequest,
        db: Session = Depends(get_db)
    ):
        # Find student
        student = db.query(Student).filter(Student.email == request.email).first()
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")
        
        if student.is_verified:
            raise HTTPException(status_code=400, detail="Account already verified")
        
        # Find verification code
        verification = db.query(EmailVerification).filter(
            EmailVerification.student_id == student.id,
            EmailVerification.code == request.code
        ).order_by(EmailVerification.created_at.desc()).first()
        
        if not verification:
            raise HTTPException(status_code=400, detail="Invalid verification code")
        
        # Check if code expired
        if datetime.utcnow() > verification.expires_at:
            raise HTTPException(status_code=400, detail="Verification code has expired")
        
        # Verify student
        student.is_verified = True
        db.commit()
        
        # Delete used verification code
        db.delete(verification)
        db.commit()
        
        return {
            "message": "Account verified successfully. You can now login.",
            "status": "success"
        }
