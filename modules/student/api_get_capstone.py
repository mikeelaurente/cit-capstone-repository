from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from db import get_db
from models import Student, Project, Author
from helpers.session import get_current_user_jwt

def register_api_get_capstone_route(app: FastAPI):
    @app.get("/api/student/capstones/{project_id}")
    def get_capstone_details(
        project_id: int,
        db: Session = Depends(get_db),
        claims = Depends(get_current_user_jwt)
    ):
        # Check authentication
        if not claims or claims.get("role") != "Student":
            raise HTTPException(status_code=401, detail="Not authenticated as student")
        
        user_id = claims.get("user_id")
        
        # Get project by user
        project = db.query(Project).filter(
            Project.id == project_id,
            Project.user_id == user_id
        ).first()
        
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        result = {
            "id": project.id,
            "status": project.status,
            "submitted_at": project.submitted_at.isoformat(),
            "reviewed_at": project.reviewed_at.isoformat() if project.reviewed_at else None,
            "admin_notes": project.admin_notes,
            "title": project.title,
            "year": project.year,
            "abstract": project.abstract,
            "category": project.category,
            "adviser": project.adviser,
            "authors": [a.full_name for a in project.authors],
            "keywords": [k.keyword for k in project.keywords],
            "course": project.course,
            "host": project.host,
            "doc_type": project.doc_type,
            "external_links": project.external_links
        }
        
        return {
            "status": "success",
            "capstone": result
        }
