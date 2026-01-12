from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from db import get_db
from models import Student, Submission, Project, Author
from helpers.session import get_current_user_jwt

def register_api_get_submission_route(app: FastAPI):
    @app.get("/api/student/submissions/{submission_id}")
    def get_submission_details(
        submission_id: int,
        db: Session = Depends(get_db),
        claims = Depends(get_current_user_jwt)
    ):
        # Check authentication
        if not claims or claims.get("role") != "student":
            raise HTTPException(status_code=401, detail="Not authenticated as student")
        
        student_id = claims.get("student_id")
        
        # Get submission
        submission = db.query(Submission).filter(
            Submission.id == submission_id,
            Submission.student_id == student_id
        ).first()
        
        if not submission:
            raise HTTPException(status_code=404, detail="Submission not found")
        
        project = submission.project
        
        result = {
            "id": submission.id,
            "status": submission.status,
            "submitted_at": submission.submitted_at.isoformat(),
            "reviewed_at": submission.reviewed_at.isoformat() if submission.reviewed_at else None,
            "admin_notes": submission.admin_notes,
            "project": None
        }
        
        if project:
            result["project"] = {
                "id": project.id,
                "title": project.title,
                "year": project.year,
                "abstract": project.abstract,
                "authors": [a.full_name for a in project.authors],
                "course": project.course,
                "host": project.host,
                "doc_type": project.doc_type,
                "external_links": project.external_links
            }
        
        return {
            "status": "success",
            "submission": result
        }
