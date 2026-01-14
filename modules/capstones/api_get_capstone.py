from fastapi import FastAPI
from fastapi.params import Depends
from sqlalchemy.orm import Session
from db import get_db
from dtos import ProjectOut
from models import Analytics
from sqlalchemy import text
from http.client import HTTPException
from datetime import datetime

def register_api_get_capstone_route(app: FastAPI):
    @app.get("/api/capstones/{project_id}")
    def get_project(project_id: int, db: Session = Depends(get_db)):
        p = db.execute(
            text("SELECT id, title, year, abstract, filename, sha256, course, host, doc_type, external_links FROM projects WHERE id=:pid AND status='approved'"),
            {"pid": project_id}
        ).fetchone()
        if not p: raise HTTPException(404, "Not found or not approved")
        pid, title, year, abstract, filename, sha, course, host, doc_type, external_links = p
        authors = [r[0] for r in db.execute(text("SELECT full_name FROM authors WHERE project_id=:pid"), {"pid": pid}).fetchall()]
        sections = db.execute(
            text("SELECT heading, content, order_no FROM sections WHERE project_id=:pid ORDER BY order_no"),
            {"pid": pid}
        ).fetchall()
        keywords = [r[0] for r in db.execute(text("SELECT keyword FROM project_keywords WHERE project_id=:pid"), {"pid": pid}).fetchall()]
        
        # Record view analytics
        try:
            analytics = Analytics(
                project_id=pid,
                event_type="view",
                created_at=datetime.utcnow()
            )
            db.add(analytics)
            db.commit()
        except Exception as e:
            # Don't fail the request if analytics recording fails
            db.rollback()
        
        return {
            "id": pid, "title": title, "year": year, "abstract": abstract, "external_links": external_links,
            "authors": authors, "sections": [{"heading": h, "content": c, "order": o} for (h,c,o) in sections],
            "course": course, "host": host, "doc_type": doc_type, "keywords": keywords,
            "docx": f"/files/{sha}.docx", "filename": filename
        }
