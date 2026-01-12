from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from db import get_db
from models import Project, Author
from dtos import CitationRequest

def format_authors_apa(authors: list) -> str:
    """Format authors for APA citation"""
    if not authors:
        return ""
    if len(authors) == 1:
        return authors[0]
    if len(authors) == 2:
        return f"{authors[0]}, & {authors[1]}"
    # For 3+ authors in APA 7th edition
    return f"{authors[0]} et al."

def format_authors_mla(authors: list) -> str:
    """Format authors for MLA citation"""
    if not authors:
        return ""
    if len(authors) == 1:
        return authors[0]
    # For multiple authors, use first author + "et al."
    return f"{authors[0]}, et al."

def format_authors_chicago(authors: list) -> str:
    """Format authors for Chicago citation"""
    if not authors:
        return ""
    if len(authors) == 1:
        return authors[0]
    if len(authors) == 2:
        return f"{authors[0]} and {authors[1]}"
    if len(authors) == 3:
        return f"{authors[0]}, {authors[1]}, and {authors[2]}"
    # For 4+ authors
    return f"{authors[0]} et al."

def format_authors_ieee(authors: list) -> str:
    """Format authors for IEEE citation"""
    if not authors:
        return ""
    if len(authors) <= 3:
        return ", ".join(authors)
    # For 4+ authors
    return f"{authors[0]} et al."

def register_api_get_citation_route(app: FastAPI):
    @app.post("/api/student/capstones/{project_id}/citation")
    def get_citation(
        project_id: int,
        request: CitationRequest,
        db: Session = Depends(get_db)
    ):
        # Get project
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Capstone not found")
        
        # Get authors
        authors = [author.full_name for author in project.authors]
        title = project.title or "Untitled"
        year = project.year or "n.d."
        
        citation = ""
        format_type = request.format.upper()
        
        if format_type == "APA":
            # APA 7th Edition format
            author_str = format_authors_apa(authors)
            citation = f"{author_str}. ({year}). {title}. CIT Capstone Repository."
            
        elif format_type == "MLA":
            # MLA 9th Edition format
            author_str = format_authors_mla(authors)
            citation = f'{author_str}. "{title}." CIT Capstone Repository, {year}.'
            
        elif format_type == "CHICAGO":
            # Chicago 17th Edition format
            author_str = format_authors_chicago(authors)
            citation = f'{author_str}. "{title}." CIT Capstone Repository. {year}.'
            
        elif format_type == "IEEE":
            # IEEE format
            author_str = format_authors_ieee(authors)
            citation = f'{author_str}, "{title}," CIT Capstone Repository, {year}.'
            
        else:
            raise HTTPException(
                status_code=400, 
                detail="Invalid format. Supported formats: APA, MLA, Chicago, IEEE"
            )
        
        return {
            "status": "success",
            "format": format_type,
            "citation": citation,
            "project": {
                "id": project.id,
                "title": title,
                "authors": authors,
                "year": year
            }
        }
    
    @app.get("/api/student/capstones/{project_id}/citations")
    def get_all_citations(
        project_id: int,
        db: Session = Depends(get_db)
    ):
        """Get citations in all formats"""
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Capstone not found")
        
        authors = [author.full_name for author in project.authors]
        title = project.title or "Untitled"
        year = project.year or "n.d."
        
        citations = {
            "APA": f"{format_authors_apa(authors)}. ({year}). {title}. CIT Capstone Repository.",
            "MLA": f'{format_authors_mla(authors)}. "{title}." CIT Capstone Repository, {year}.',
            "Chicago": f'{format_authors_chicago(authors)}. "{title}." CIT Capstone Repository. {year}.',
            "IEEE": f'{format_authors_ieee(authors)}, "{title}," CIT Capstone Repository, {year}.'
        }
        
        return {
            "status": "success",
            "project": {
                "id": project.id,
                "title": title,
                "authors": authors,
                "year": year
            },
            "citations": citations
        }
