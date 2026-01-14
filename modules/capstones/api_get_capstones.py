from fastapi import FastAPI
from fastapi.params import Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from db import get_db
from dtos import PaginatedProjectOutput, ProjectOut
from models import Analytics
from sqlalchemy import text
from datetime import datetime

def register_api_get_capstones_route(app: FastAPI):
    @app.get("/api/capstones", response_model=PaginatedProjectOutput)
    def list_projects(q: Optional[str] = Query(None), per_page: Optional[int] = 10, page: Optional[int] = 1, db: Session = Depends(get_db)):
        total = 0
        offset = per_page * (page-1)
        
        if q:
            sql = """
                SELECT p.id, p.title, p.year, p.abstract, p.course, p.host, p.doc_type, p.external_links
                FROM projects p JOIN projects_fts f ON f.project_id = p.id
                WHERE projects_fts MATCH :q AND p.status = 'approved'
                        """
            rows = db.execute(
                text(f"""{sql} ORDER BY bm25(projects_fts) LIMIT :lim OFFSET :off"""),
                {"q": q, "lim": per_page, "off": offset}
            ).fetchall()
            
            total = db.execute(text(f"""SELECT COUNT(*) as total FROM ({sql}) x"""), {"q": q}).scalar_one()
        else:
            sql = """
                SELECT id, title, year, abstract, course, host, doc_type, external_links FROM projects WHERE status = 'approved'
                """
            rows = db.execute(
                text(f"{sql} ORDER BY id DESC LIMIT :lim OFFSET :off"),
                {"lim": per_page, "off": offset}
            ).fetchall()
            
            total = db.execute(text(f"""SELECT COUNT(*) as total FROM ({sql}) x"""), {"q": q}).scalar_one()

        out = []
        for pid, title, year, abstract, course, host, doc_type, external_links in rows:
            authors = [r[0] for r in db.execute(text("SELECT full_name FROM authors WHERE project_id=:pid"), {"pid": pid}).fetchall()]
            keywords = [r[0] for r in db.execute(text("SELECT keyword FROM project_keywords WHERE project_id=:pid"), {"pid": pid}).fetchall()]
            out.append(ProjectOut(id=pid, title=title, year=year, abstract=abstract, authors=authors,
                                course=course, host=host, doc_type=doc_type, keywords=keywords, external_links=external_links))
            
            # Record search analytics only if search query is provided
            if q:
                try:
                    analytics = Analytics(
                        project_id=pid,
                        event_type="search",
                        search_query=q,
                        created_at=datetime.utcnow()
                    )
                    db.add(analytics)
                except Exception as e:
                    # Don't fail the request if analytics recording fails
                    pass
        
        # Commit analytics records
        if q:
            try:
                db.commit()
            except Exception as e:
                db.rollback()

        print(f"q: {q} | per_page: {per_page} | offset: {offset} | page: {page}")
        
        return {
            "total": total,
            "page": page,
            "per_page": per_page,
            "results": out,
        }