from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from db import get_db
from models import Project
from helpers.session import get_current_user_jwt

def register_api_student_dashboard_route(app: FastAPI):
    @app.get("/api/student/dashboard")
    def get_student_dashboard(
        db: Session = Depends(get_db),
        claims = Depends(get_current_user_jwt)
    ):
        """Get student dashboard with submission statistics"""
        if not claims or claims.get("role") != "Student":
            raise HTTPException(status_code=403, detail="Student access required")
        
        user_id = claims.get("user_id")
        
        try:
            # Get total submissions
            total_submissions = db.query(func.count(Project.id)).filter(
                Project.user_id == user_id
            ).scalar() or 0
            
            # Get approved submissions
            approved_count = db.query(func.count(Project.id)).filter(
                Project.user_id == user_id,
                Project.status == "approved"
            ).scalar() or 0
            
            # Get rejected submissions
            rejected_count = db.query(func.count(Project.id)).filter(
                Project.user_id == user_id,
                Project.status == "rejected"
            ).scalar() or 0
            
            # Get pending submissions
            pending_count = db.query(func.count(Project.id)).filter(
                Project.user_id == user_id,
                Project.status == "pending"
            ).scalar() or 0
            
            return {
                "status": "success",
                "data": {
                    "submissions": total_submissions,
                    "approved": approved_count,
                    "rejected": rejected_count,
                    "pending": pending_count
                }
            }
        
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error fetching dashboard: {str(e)}")
