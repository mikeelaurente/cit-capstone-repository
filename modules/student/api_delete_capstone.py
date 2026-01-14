from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from db import get_db
from models import Project
from helpers.session import get_current_user_jwt

def register_api_delete_capstone_route(app: FastAPI):
    @app.delete("/api/student/capstones/{project_id}")
    def delete_capstone(
        project_id: int,
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
        
        # Only allow deletion if status is pending
        if project.status != "pending":
            raise HTTPException(
                status_code=400, 
                detail="Can only delete capstones with pending status"
            )
        
        # Delete the project (cascade will delete authors and keywords)
        db.delete(project)
        db.commit()
        
        return {
            "message": "Capstone deleted successfully",
            "status": "success"
        }
