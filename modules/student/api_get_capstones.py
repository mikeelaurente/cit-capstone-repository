from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List
from db import get_db
from models import Student, Project, Author
from helpers.session import get_current_user_jwt

def register_api_get_capstones_route(app: FastAPI):
    @app.get("/api/student/capstones")
    def get_student_capstones(
        status: str = None,  # Filter: pending, approved, rejected
        db: Session = Depends(get_db),
        claims = Depends(get_current_user_jwt)
    ):
        # Check authentication
        if not claims or claims.get("role") != "Student":
            raise HTTPException(status_code=401, detail="Not authenticated as student")
        
        user_id = claims.get("user_id")
        
        # Query projects by user
        query = db.query(Project).filter(Project.user_id == user_id)
        
        if status:
            query = query.filter(Project.status == status.lower())
        
        projects = query.order_by(Project.submitted_at.desc()).all()
        
        result = []
        for project in projects:
            project_data = {
                "id": project.id,
                "status": project.status,
                "submitted_at": project.submitted_at.isoformat(),
                "reviewed_at": project.reviewed_at.isoformat() if project.reviewed_at else None,
                "admin_notes": project.admin_notes,
                "title": project.title,
                "year": project.year,
                "abstract": project.abstract,
                "authors": [a.full_name for a in project.authors],
                "course": project.course,
                "host": project.host,
                "doc_type": project.doc_type
            }
            
            result.append(project_data)
        
        return {
            "status": "success",
            "total": len(result),
            "capstones": result
        }
