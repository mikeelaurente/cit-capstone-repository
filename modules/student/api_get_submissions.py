from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List
from db import get_db
from models import Student, Submission, Project, Author
from helpers.session import get_current_user_jwt

def register_api_get_submissions_route(app: FastAPI):
    @app.get("/api/student/submissions")
    def get_student_submissions(
        status: str = None,  # Filter: pending, approved, rejected
        db: Session = Depends(get_db),
        claims = Depends(get_current_user_jwt)
    ):
        # Check authentication
        if not claims or claims.get("role") != "student":
            raise HTTPException(status_code=401, detail="Not authenticated as student")
        
        student_id = claims.get("student_id")
        
        # Query submissions
        query = db.query(Submission).filter(Submission.student_id == student_id)
        
        if status:
            query = query.filter(Submission.status == status.lower())
        
        submissions = query.order_by(Submission.submitted_at.desc()).all()
        
        result = []
        for submission in submissions:
            project = submission.project
            submission_data = {
                "id": submission.id,
                "status": submission.status,
                "submitted_at": submission.submitted_at.isoformat(),
                "reviewed_at": submission.reviewed_at.isoformat() if submission.reviewed_at else None,
                "admin_notes": submission.admin_notes,
                "project": None
            }
            
            if project:
                submission_data["project"] = {
                    "id": project.id,
                    "title": project.title,
                    "year": project.year,
                    "abstract": project.abstract,
                    "authors": [a.full_name for a in project.authors],
                    "course": project.course,
                    "host": project.host,
                    "doc_type": project.doc_type
                }
            
            result.append(submission_data)
        
        return {
            "status": "success",
            "total": len(result),
            "submissions": result
        }
