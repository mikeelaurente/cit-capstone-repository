from typing import Dict
from fastapi import Depends, FastAPI, Query
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session
from datetime import datetime

from db import get_db
from models import Analytics
from rag.retrieval import hybrid_retrieve


def register_api_search_capstones_routes(app: FastAPI):
    @app.get("/api/search")
    def search(q: str = Query(...), k: int = 30, page: int = Query(default=1, ge=1), limit: int = Query(default=10, ge=1, le=100), db: Session = Depends(get_db)):
        # Validate pagination parameters
        if page < 1:
            raise ValueError("Page must be >= 1")
        if limit < 1 or limit > 100:
            raise ValueError("Limit must be between 1 and 100")
        
        hits = hybrid_retrieve(db, q, k=k)
        grouped: Dict[int, Dict] = {}
        for h in hits:
            # Check if project is approved before including in results
            project_status = db.execute(text("SELECT status FROM projects WHERE id=:pid"), {"pid": h["project_id"]}).scalar()
            if project_status != "approved":
                continue
            
            grouped.setdefault(h["project_id"], {"title": h["title"], "similarity": h["sim"], "year": h["year"], "snippets": []})
            grouped[h["project_id"]]["snippets"].append(h["content"])
            authors = [r[0] for r in db.execute(text("SELECT full_name FROM authors WHERE project_id=:pid"), {"pid": h["project_id"]}).fetchall()]
            keywords = [r[0] for r in db.execute(text("SELECT keyword FROM project_keywords WHERE project_id=:pid"), {"pid": h["project_id"]}).fetchall()]
            grouped[h["project_id"]]["authors"] = authors
            grouped[h["project_id"]]["keywords"] = keywords
        
        # Get total count before pagination
        total = len(grouped)
        
        # Apply pagination
        offset = (page - 1) * limit
        paginated_grouped = dict(list(grouped.items())[offset:offset + limit])
        
        results = [{"project_id": pid, **meta} for pid, meta in paginated_grouped.items()]
        
        # Record search analytics for each result in this page
        try:
            for pid in paginated_grouped.keys():
                analytics = Analytics(
                    project_id=pid,
                    event_type="search",
                    search_query=q,
                    created_at=datetime.utcnow()
                )
                db.add(analytics)
            db.commit()
        except Exception as e:
            # Don't fail the request if analytics recording fails
            db.rollback()
        
        # Calculate pagination metadata
        total_pages = (total + limit - 1) // limit  # Ceiling division
        
        return {
            "query": q,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1
            },
            "results": results
        }
