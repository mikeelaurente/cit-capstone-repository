from fastapi import FastAPI, HTTPException, Depends, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import or_
from db import get_db, delete_fts_row, insert_fts_row
from models import Project, Author, ProjectKeyword, Section, Chunk, Embedding
from helpers.session import get_current_user_jwt
from helpers.docx_parser import parse_compilation_docx
from helpers.text import sentence_chunks
from helpers.embeddings import embed_texts, pack_vector
from rag.indexing import upsert_project_from_fields
from config import PathConfig
import hashlib
from datetime import datetime
from pydantic import BaseModel
from typing import List, Optional

class PublishCapstoneRequest(BaseModel):
    keywords: List[str]
    category: Optional[str] = None
    note: Optional[str] = None

class RejectCapstoneRequest(BaseModel):
    note: Optional[str] = None

class RevertCapstoneRequest(BaseModel):
    note: Optional[str] = None

class EditCapstoneRequest(BaseModel):
    title: Optional[str] = None
    abstract: Optional[str] = None
    year: Optional[int] = None
    authors: Optional[List[str]] = None
    keywords: Optional[List[str]] = None
    category: Optional[str] = None
    adviser: Optional[str] = None

class ManualCapstoneUploadRequest(BaseModel):
    title: str
    authors: List[str]  # List of author names
    keywords: List[str]
    year: int
    abstract: Optional[str] = None
    category: Optional[str] = None
    adviser: Optional[str] = None

def regenerate_project_embeddings(db: Session, project: Project):
    """Regenerate embeddings for a project using its current model fields (not file-based)"""
    try:
        # Delete existing embeddings, chunks, and sections
        delete_fts_row(db, project.id)
        db.query(Embedding).filter(Embedding.chunk_id.in_(
            db.query(Chunk.id).filter_by(project_id=project.id)
        )).delete(synchronize_session=False)
        db.query(Chunk).filter_by(project_id=project.id).delete()
        db.query(Section).filter_by(project_id=project.id).delete()
        
        # Create new embeddings from the abstract
        if project.abstract:
            sec = Section(project_id=project.id, heading="ABSTRACT", content=project.abstract, order_no=1)
            db.add(sec)
            db.flush()
            
            parts = sentence_chunks(project.abstract)
            if parts:
                vecs = embed_texts(parts)
                for j, (part, vec) in enumerate(zip(parts, vecs), start=1):
                    ch = Chunk(project_id=project.id, section_id=sec.id, content=part, ord_in_sec=j)
                    db.add(ch)
                    db.flush()
                    db.add(Embedding(chunk_id=ch.id, vector=pack_vector(vec)))
        
        # Update FTS index
        insert_fts_row(db, project.id, project.title or "", project.abstract or "", project.abstract or "")
        db.commit()
        return True
    except Exception as e:
        return False

def register_api_admin_capstones_route(app: FastAPI):
    
    @app.get("/api/admin/capstones")
    def list_all_capstones(
        status: Optional[str] = None,  # Filter by status: pending, approved, rejected
        search: Optional[str] = None,  # Search in title, abstract, or author names
        page: int = 1,  # Page number (1-indexed)
        limit: int = 10,  # Items per page
        db: Session = Depends(get_db),
        claims = Depends(get_current_user_jwt)
    ):
        """List all capstones (Admin/Staff) with pagination and search"""
        if not claims or claims.get("role") not in ["Admin", "Staff"]:
            raise HTTPException(status_code=403, detail="Admin or Staff access required")
        
        # Validate pagination parameters
        if page < 1:
            raise HTTPException(status_code=400, detail="Page must be >= 1")
        if limit < 1 or limit > 100:
            raise HTTPException(status_code=400, detail="Limit must be between 1 and 100")
        
        query = db.query(Project)
        
        if status and status.lower() in ["pending", "approved", "rejected"]:
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
        projects = query.order_by(Project.created_at.desc()).offset(offset).limit(limit).all()
        
        result = []
        for project in projects:
            result.append({
                "id": project.id,
                "title": project.title,
                "year": project.year,
                "abstract": project.abstract[:100] + "..." if project.abstract and len(project.abstract) > 100 else project.abstract,
                "status": project.status,
                "authors": [a.full_name for a in project.authors],
                "keywords": [k.keyword for k in project.keywords],
                "category": project.category,
                "adviser": project.adviser,
                "created_at": project.created_at.isoformat(),
                "course": project.course,
                "host": project.host,
                "doc_type": project.doc_type
            })
        
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
    
    @app.post("/api/admin/capstones/upload")
    async def admin_upload_capstone(
        file: UploadFile = File(...),
        db: Session = Depends(get_db),
        claims = Depends(get_current_user_jwt)
    ):
        """Upload capstones from .docx file (Admin/Staff) - may contain multiple capstones"""
        if not claims or claims.get("role") not in ["Admin", "Staff"]:
            raise HTTPException(status_code=403, detail="Admin or Staff access required")
        
        if not file.filename.endswith('.docx'):
            raise HTTPException(status_code=400, detail="Only .docx files are accepted")
        
        content = await file.read()
        
        if len(content) < 500:
            raise HTTPException(status_code=400, detail="File is too small or corrupt")
        
        try:
            parsed_data = parse_compilation_docx(content)
            if not parsed_data or len(parsed_data) == 0:
                raise HTTPException(status_code=400, detail="Could not extract capstone information from document")
            
            file_hash = hashlib.sha256(content).hexdigest()
            
            # Save file once
            file_path = PathConfig.UPLOAD_DIR / f"{file_hash}.docx"
            with open(file_path, "wb") as f:
                f.write(content)
            
            # Process each entry in the document
            created_projects = []
            for entry in parsed_data:
                # Generate hash for this specific capstone based on title, authors, and abstract
                title = entry.get("title") or ""
                authors = "|".join(entry.get("researchers", []))
                abstract = (entry.get("abstract") or "")[:1000]
                basis = title + "|" + authors + "|" + abstract
                entry_hash = hashlib.sha256(basis.encode()).hexdigest()
                
                # Check if this capstone already exists
                existing = db.query(Project).filter(Project.sha256 == entry_hash).first()
                if existing:
                    continue  # Skip if already exists
                
                # Create project (admin-uploaded, linked to user)
                project = Project(
                    sha256=entry_hash,
                    filename=file.filename,
                    user_id=claims.get("user_id"),  # Link to the admin/staff user who uploaded it
                    title=entry.get("title"),
                    year=entry.get("year"),
                    abstract=entry.get("abstract"),
                    course=entry.get("course"),
                    host=entry.get("host"),
                    doc_type=entry.get("doc_type"),
                    status="pending"
                )
                
                db.add(project)
                db.flush()
                
                # Add authors
                for researcher_name in entry.get("researchers", []):
                    author = Author(project_id=project.id, full_name=researcher_name)
                    db.add(author)
                
                db.commit()
                db.refresh(project)
                
                created_projects.append({
                    "project_id": project.id,
                    "title": project.title,
                    "authors": [a.full_name for a in project.authors],
                    "status": project.status
                })
            
            return {
                "message": "Capstones uploaded successfully",
                "status": "success",
                "total_entries": len(parsed_data),
                "created": len(created_projects),
                "data": created_projects
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error processing document: {str(e)}")
    
    @app.post("/api/admin/capstones/manual")
    def admin_manual_upload(
        request: ManualCapstoneUploadRequest,
        db: Session = Depends(get_db),
        claims = Depends(get_current_user_jwt)
    ):
        """Manually create capstone entry (Admin/Staff)"""
        if not claims or claims.get("role") not in ["Admin", "Staff"]:
            raise HTTPException(status_code=403, detail="Admin or Staff access required")
        
        # Generate hash using the same mechanism: title + authors + abstract
        title = request.title or ""
        authors = "|".join(request.authors)
        abstract = (request.abstract or "")[:1000]
        basis = title + "|" + authors + "|" + abstract
        entry_hash = hashlib.sha256(basis.encode()).hexdigest()
        
        # Check if this capstone already exists
        existing = db.query(Project).filter(Project.sha256 == entry_hash).first()
        if existing:
            raise HTTPException(status_code=409, detail="Capstone with this title, authors, and abstract already exists")
        
        project = Project(
            sha256=entry_hash,
            filename=f"manual_{entry_hash[:8]}.docx",
            user_id=claims.get("user_id"),  # Link to the admin/staff user who created it
            title=request.title,
            year=request.year,
            abstract=request.abstract,
            category=request.category,
            adviser=request.adviser,
            status="pending"
        )
        
        db.add(project)
        db.flush()
        
        # Add authors
        for author_name in request.authors:
            author = Author(project_id=project.id, full_name=author_name)
            db.add(author)
        
        # Add keywords
        for keyword in request.keywords:
            kw = ProjectKeyword(project_id=project.id, keyword=keyword)
            db.add(kw)
        
        db.commit()
        db.refresh(project)
        
        return {
            "message": "Capstone created successfully",
            "status": "success",
            "data": {
                "project_id": project.id,
                "title": project.title,
                "authors": [a.full_name for a in project.authors],
                "keywords": [k.keyword for k in project.keywords],
                "category": project.category,
                "status": project.status
            }
        }
    
    @app.post("/api/admin/capstones/{project_id}/process")
    def process_capstone_embeddings(
        project_id: int,
        db: Session = Depends(get_db),
        claims = Depends(get_current_user_jwt)
    ):
        """Process capstone for embeddings (Admin/Staff)"""
        if not claims or claims.get("role") not in ["Admin", "Staff"]:
            raise HTTPException(status_code=403, detail="Admin or Staff access required")
        
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Process embeddings using current model fields
        if regenerate_project_embeddings(db, project):
            return {
                "message": "Capstone embeddings processed successfully",
                "status": "success",
                "project_id": project_id,
                "title": project.title
            }
        else:
            raise HTTPException(status_code=500, detail="Error processing embeddings")
    
    @app.post("/api/admin/capstones/{project_id}/publish")
    def publish_capstone(
        project_id: int,
        request: PublishCapstoneRequest,
        db: Session = Depends(get_db),
        claims = Depends(get_current_user_jwt)
    ):
        """Publish/approve a pending capstone (Admin/Staff)"""
        if not claims or claims.get("role") not in ["Admin", "Staff"]:
            raise HTTPException(status_code=403, detail="Admin or Staff access required")
        
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        if project.status != "pending":
            raise HTTPException(status_code=400, detail=f"Can only publish pending projects, current status: {project.status}")
        
        # Update status and reviewer information
        project.status = "approved"
        project.reviewer_id = claims.get("user_id")
        project.reviewed_at = datetime.utcnow()
        if request.note:
            project.admin_notes = request.note
            
        if request.category is not None:
            project.category = request.category
        
        # Update keywords if provided
        if request.keywords:
            # Clear existing keywords
            db.query(ProjectKeyword).filter(ProjectKeyword.project_id == project.id).delete()
            
            # Add new keywords
            for keyword in request.keywords:
                kw = ProjectKeyword(project_id=project.id, keyword=keyword)
                db.add(kw)
        
        db.commit()
        db.refresh(project)
        
        # Process embeddings using current model fields
        regenerate_project_embeddings(db, project)
        
        return {
            "message": "Capstone published successfully",
            "status": "success",
            "data": {
                "project_id": project.id,
                "title": project.title,
                "new_status": project.status,
                "reviewed_at": project.reviewed_at.isoformat() if project.reviewed_at else None,
                "keywords": request.keywords
            }
        }
    
    @app.post("/api/admin/capstones/{project_id}/reject")
    def reject_capstone(
        project_id: int,
        request: RejectCapstoneRequest,
        db: Session = Depends(get_db),
        claims = Depends(get_current_user_jwt)
    ):
        """Reject a pending capstone (Admin/Staff)"""
        if not claims or claims.get("role") not in ["Admin", "Staff"]:
            raise HTTPException(status_code=403, detail="Admin or Staff access required")
        
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        if project.status != "pending":
            raise HTTPException(status_code=400, detail=f"Can only reject pending projects, current status: {project.status}")
        
        # Update status and reviewer information
        project.status = "rejected"
        project.reviewer_id = claims.get("user_id")
        project.reviewed_at = datetime.utcnow()
        if request.note:
            project.admin_notes = request.note
        
        db.commit()
        db.refresh(project)
        
        return {
            "message": "Capstone rejected",
            "status": "success",
            "data": {
                "project_id": project.id,
                "new_status": project.status,
                "reviewed_at": project.reviewed_at.isoformat() if project.reviewed_at else None,
                "note": project.admin_notes
            }
        }
    
    @app.post("/api/admin/capstones/{project_id}/revert-to-pending")
    def revert_capstone_to_pending(
        project_id: int,
        request: RevertCapstoneRequest,
        db: Session = Depends(get_db),
        claims = Depends(get_current_user_jwt)
    ):
        """Revert a capstone to pending status (Admin/Staff)"""
        if not claims or claims.get("role") not in ["Admin", "Staff"]:
            raise HTTPException(status_code=403, detail="Admin or Staff access required")
        
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        if project.status == "pending":
            raise HTTPException(status_code=400, detail="Capstone is already pending")
        
        # If reverting from approved status, delete embeddings and related records
        if project.status == "approved":
            try:
                delete_fts_row(db, project.id)
                db.query(Embedding).filter(Embedding.chunk_id.in_(
                    db.query(Chunk.id).filter_by(project_id=project.id)
                )).delete(synchronize_session=False)
                db.query(Chunk).filter_by(project_id=project.id).delete()
                db.query(Section).filter_by(project_id=project.id).delete()
            except Exception as e:
                # Log error but don't fail the revert
                pass
        
        # Revert to pending and clear reviewer information
        previous_status = project.status
        project.status = "pending"
        project.reviewer_id = None
        project.reviewed_at = None
        # Store the revert note if provided, otherwise clear notes
        if request.note:
            project.admin_notes = request.note
        else:
            project.admin_notes = None
        
        db.commit()
        db.refresh(project)
        
        return {
            "message": "Capstone reverted to pending",
            "status": "success",
            "data": {
                "project_id": project.id,
                "title": project.title,
                "previous_status": previous_status,
                "new_status": project.status,
                "note": project.admin_notes,
                "embeddings_deleted": previous_status == "approved"
            }
        }
    
    @app.put("/api/admin/capstones/{project_id}")
    def edit_capstone(
        project_id: int,
        request: EditCapstoneRequest,
        db: Session = Depends(get_db),
        claims = Depends(get_current_user_jwt)
    ):
        """Edit capstone details (Admin/Staff)"""
        if not claims or claims.get("role") not in ["Admin", "Staff"]:
            raise HTTPException(status_code=403, detail="Admin or Staff access required")
        
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Update fields if provided
        if request.title:
            project.title = request.title
        if request.abstract is not None:
            project.abstract = request.abstract
        if request.year:
            project.year = request.year
        if request.category is not None:
            project.category = request.category
        if request.adviser is not None:
            project.adviser = request.adviser
        
        # Update authors if provided
        if request.authors:
            db.query(Author).filter(Author.project_id == project.id).delete()
            for author_name in request.authors:
                author = Author(project_id=project.id, full_name=author_name)
                db.add(author)
        
        # Update keywords if provided
        if request.keywords:
            db.query(ProjectKeyword).filter(ProjectKeyword.project_id == project.id).delete()
            for keyword in request.keywords:
                kw = ProjectKeyword(project_id=project.id, keyword=keyword)
                db.add(kw)
        
        db.commit()
        db.refresh(project)
        
        # If capstone is already published, update embeddings automatically
        embeddings_updated = False
        if project.status == "approved":
            embeddings_updated = regenerate_project_embeddings(db, project)
        
        return {
            "message": "Capstone updated successfully",
            "status": "success",
            "data": {
                "project_id": project.id,
                "title": project.title,
                "authors": [a.full_name for a in project.authors],
                "keywords": [k.keyword for k in project.keywords],
                "embeddings_updated": embeddings_updated
            }
        }
    
    @app.delete("/api/admin/capstones/{project_id}")
    def delete_capstone(
        project_id: int,
        db: Session = Depends(get_db),
        claims = Depends(get_current_user_jwt)
    ):
        """Delete a capstone (Admin/Staff)"""
        if not claims or claims.get("role") not in ["Admin", "Staff"]:
            raise HTTPException(status_code=403, detail="Admin or Staff access required")
        
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        project_title = project.title
        was_approved = project.status == "approved"
        
        # Delete embeddings and related records if project was published
        if was_approved:
            try:
                delete_fts_row(db, project.id)
                db.query(Embedding).filter(Embedding.chunk_id.in_(
                    db.query(Chunk.id).filter_by(project_id=project.id)
                )).delete(synchronize_session=False)
                db.query(Chunk).filter_by(project_id=project.id).delete()
                db.query(Section).filter_by(project_id=project.id).delete()
            except Exception as e:
                # Log error but don't fail the deletion
                pass
        
        db.delete(project)
        db.commit()
        
        return {
            "message": f"Capstone '{project_title}' deleted successfully",
            "status": "success",
            "embeddings_deleted": was_approved
        }
