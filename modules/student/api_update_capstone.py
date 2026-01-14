from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from db import get_db
from models import Project, Author, ProjectKeyword
from helpers.session import get_current_user_jwt
from pydantic import BaseModel
from typing import Optional, List

class UpdateCapstonePayload(BaseModel):
    title: Optional[str] = None
    year: Optional[int] = None
    abstract: Optional[str] = None
    category: Optional[str] = None
    adviser: Optional[str] = None
    authors: Optional[List[str]] = None
    keywords: Optional[List[str]] = None

def register_api_update_capstone_route(app: FastAPI):
    @app.put("/api/student/capstones/{project_id}")
    async def update_capstone(
        project_id: int,
        payload: UpdateCapstonePayload,
        db: Session = Depends(get_db),
        claims = Depends(get_current_user_jwt)
    ):
        # Check authentication
        if not claims or claims.get("role") != "Student":
            raise HTTPException(status_code=401, detail="Not authenticated as student")
        
        user_id = claims.get("user_id")
        
        # Get the project
        project = db.query(Project).filter(
            Project.id == project_id,
            Project.user_id == user_id
        ).first()
        
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Check if project is already approved
        if project.status == "approved":
            raise HTTPException(status_code=400, detail="Cannot update an approved capstone")
        
        # Update fields from payload
        if payload.title:
            project.title = payload.title
        if payload.year:
            project.year = payload.year
        if payload.abstract:
            project.abstract = payload.abstract
        if payload.category:
            project.category = payload.category
        if payload.adviser:
            project.adviser = payload.adviser
        
        # Update authors if provided
        if payload.authors is not None:
            db.query(Author).filter(Author.project_id == project_id).delete()
            for author_name in payload.authors:
                author = Author(
                    project_id=project.id,
                    full_name=author_name
                )
                db.add(author)
        
        # Update keywords if provided
        if payload.keywords is not None:
            db.query(ProjectKeyword).filter(ProjectKeyword.project_id == project_id).delete()
            for keyword_text in payload.keywords:
                keyword = ProjectKeyword(
                    project_id=project.id,
                    keyword=keyword_text
                )
                db.add(keyword)
        
        db.commit()
        db.refresh(project)
        
        return {
            "message": "Capstone updated successfully",
            "status": "success",
            "data": {
                "project_id": project.id,
                "title": project.title,
                "authors": [a.full_name for a in project.authors],
                "keywords": [k.keyword for k in project.keywords],
                "year": project.year,
                "abstract": project.abstract,
                "category": project.category,
                "adviser": project.adviser,
                "status": project.status,
                "submitted_at": project.submitted_at.isoformat()
            }
        }
