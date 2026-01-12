from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from db import get_db
from models import Student, EmailVerification
from helpers.email_helper import generate_verification_code, send_verification_email, get_verification_expiry

class ResendCodeRequest(BaseModel):
    email: EmailStr

def register_api_resend_code_route(app: FastAPI):
    @app.post("/api/student/resend-code")
    def resend_verification_code(
        request: ResendCodeRequest,
        db: Session = Depends(get_db)
    ):
        # Find student
        student = db.query(Student).filter(Student.email == request.email).first()
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")
        
        if student.is_verified:
            raise HTTPException(status_code=400, detail="Account already verified")
        
        # Delete old verification codes
        db.query(EmailVerification).filter(
            EmailVerification.student_id == student.id
        ).delete()
        
        # Generate new code
        code = generate_verification_code()
        verification = EmailVerification(
            student_id=student.id,
            code=code,
            expires_at=get_verification_expiry()
        )
        
        db.add(verification)
        db.commit()
        
        # Send email
        send_verification_email(request.email, code)
        
        return {
            "message": "Verification code sent successfully. Please check your email.",
            "status": "success"
        }
