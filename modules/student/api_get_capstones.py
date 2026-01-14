from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional
from db import get_db
from models import Student, Project, Author
from helpers.session import get_current_user_jwt

def register_api_get_capstones_route(app: FastAPI):
    @app.get("/api/student/capstones")
    def get_student_capstones(
        status: Optional[str] = None,  # Filter: pending, approved, rejected
        search: Optional[str] = None,  # Search in title, abstract, or author names
        page: int = 1,  # Page number (1-indexed)
        limit: int = 10,  # Items per page
        db: Session = Depends(get_db),
        claims = Depends(get_current_user_jwt)
    ):
        # Check authentication
        if not claims or claims.get("role") != "Student":
            raise HTTPException(status_code=401, detail="Not authenticated as student")
        
        # Validate pagination parameters
        if page < 1:
            raise HTTPException(status_code=400, detail="Page must be >= 1")
        if limit < 1 or limit > 100:
            raise HTTPException(status_code=400, detail="Limit must be between 1 and 100")
        
        user_id = claims.get("user_id")
        
        # Query projects by user
        query = db.query(Project).filter(Project.user_id == user_id)
        
        if status:
            query = query.filter(Project.status == status.lower())
        
        # Apply search filter if provided
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    Project.title.ilike(search_term),
                    Project.abstract.ilike(search_term),
                    Project.authors.any(Author.full_name.ilike(search_term))
                )
            )
        
        # Get total count before pagination
        total = query.count()
        
        # Apply pagination
        offset = (page - 1) * limit
        projects = query.order_by(Project.submitted_at.desc()).offset(offset).limit(limit).all()
        
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
                "adviser": project.adviser,
                "host": project.host,
                "doc_type": project.doc_type
            }
            
            result.append(project_data)
        
        # Calculate pagination metadata
        total_pages = (total + limit - 1) // limit  # Ceiling division
        
        return {
            "status": "success",
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1
            },
            "capstones": result
        }
