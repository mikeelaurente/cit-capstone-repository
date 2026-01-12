from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Request
from sqlalchemy.orm import Session
from db import get_db
from models import Student, Submission, Project, Author
from helpers.session import get_current_user_jwt
from helpers.docx_parser import parse_compilation_docx
from config import PathConfig
import hashlib
from datetime import datetime

def register_api_upload_capstone_route(app: FastAPI):
    @app.post("/api/student/upload-capstone")
    async def upload_capstone(
        file: UploadFile = File(...),
        db: Session = Depends(get_db),
        claims = Depends(get_current_user_jwt)
    ):
        # Check authentication
        if not claims or claims.get("role") != "student":
            raise HTTPException(status_code=401, detail="Not authenticated as student")
        
        student_id = claims.get("student_id")
        
        # Verify student exists
        student = db.query(Student).filter(Student.id == student_id).first()
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")
        
        # Validate file type
        if not file.filename.endswith('.docx'):
            raise HTTPException(status_code=400, detail="Only .docx files are accepted")
        
        # Read file content
        content = await file.read()
        
        # Generate file hash
        file_hash = hashlib.sha256(content).hexdigest()
        
        # Check if file already exists
        existing_project = db.query(Project).filter(Project.sha256 == file_hash).first()
        if existing_project:
            # Check if this student already submitted this
            existing_submission = db.query(Submission).filter(
                Submission.student_id == student_id,
                Submission.project_id == existing_project.id
            ).first()
            if existing_submission:
                raise HTTPException(
                    status_code=400, 
                    detail="You have already submitted this capstone"
                )
        
        # Parse the document to extract metadata
        try:
            parsed_data = parse_compilation_docx(content)
            if not parsed_data or len(parsed_data) == 0:
                raise HTTPException(
                    status_code=400,
                    detail="Could not extract capstone information from document"
                )
            
            # Use the first entry
            entry = parsed_data[0]
            
            # Save file
            file_path = PathConfig.UPLOAD_DIR / f"{file_hash}.docx"
            with open(file_path, "wb") as f:
                f.write(content)
            
            # Create project (not yet visible to public - pending approval)
            project = Project(
                sha256=file_hash,
                filename=file.filename,
                title=entry.get("title"),
                year=entry.get("year"),
                abstract=entry.get("abstract"),
                course=entry.get("course"),
                host=entry.get("host"),
                doc_type=entry.get("doc_type"),
                status="pending"  # Start as pending, will be approved by admin
            )
            
            db.add(project)
            db.flush()  # Get project ID without committing
            
            # Add authors
            researchers = entry.get("researchers", [])
            for researcher_name in researchers:
                author = Author(
                    project_id=project.id,
                    full_name=researcher_name
                )
                db.add(author)
            
            # Create submission with pending status
            submission = Submission(
                student_id=student_id,
                project_id=project.id,
                status="pending"
            )
            
            db.add(submission)
            db.commit()
            db.refresh(submission)
            db.refresh(project)
            
            return {
                "message": "Capstone uploaded successfully and is pending review",
                "status": "success",
                "data": {
                    "submission_id": submission.id,
                    "project_id": project.id,
                    "title": project.title,
                    "authors": [a.full_name for a in project.authors],
                    "year": project.year,
                    "abstract": project.abstract,
                    "status": submission.status,
                    "submitted_at": submission.submitted_at.isoformat()
                }
            }
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error processing document: {str(e)}"
            )
