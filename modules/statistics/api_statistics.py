from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from datetime import datetime, timedelta
from db import get_db
from models import Project, Analytics

def register_api_statistics_route(app: FastAPI):
    @app.get("/api/statistics/dashboard")
    def get_dashboard_statistics(db: Session = Depends(get_db)):
        """Get dashboard statistics including views, searches, and project counts"""
        try:
            # Get total approved capstones
            total_capstones = db.query(func.count(Project.id)).filter(Project.status == "approved").scalar() or 0
            
            # Get total views
            total_views = db.query(func.count(Analytics.id)).filter(Analytics.event_type == "view").scalar() or 0
            
            # Get total searches
            total_searches = db.query(func.count(Analytics.id)).filter(Analytics.event_type == "search").scalar() or 0
            
            # Get recently added capstones (last 5 days)
            five_days_ago = datetime.utcnow() - timedelta(days=5)
            recent_capstones = db.query(func.count(Project.id)).filter(
                Project.status == "approved",
                Project.submitted_at >= five_days_ago
            ).scalar() or 0
            
            # Get most searched capstones (by title)
            most_searched = db.query(
                Project.title,
                func.count(Analytics.id).label("count")
            ).join(
                Analytics, Analytics.project_id == Project.id
            ).filter(
                Analytics.event_type == "search"
            ).group_by(
                Project.id, Project.title
            ).order_by(
                func.count(Analytics.id).desc()
            ).limit(10).all()
            
            most_searched_dict = {title: count for title, count in most_searched}
            
            # Get most viewed capstones (by title)
            most_viewed = db.query(
                Project.title,
                func.count(Analytics.id).label("count")
            ).join(
                Analytics, Analytics.project_id == Project.id
            ).filter(
                Analytics.event_type == "view"
            ).group_by(
                Project.id, Project.title
            ).order_by(
                func.count(Analytics.id).desc()
            ).limit(10).all()
            
            most_viewed_dict = {title: count for title, count in most_viewed}
            
            # Get capstones grouped by category
            categories = db.query(
                Project.category,
                func.count(Project.id).label("count")
            ).filter(
                Project.status == "approved",
                Project.category != None
            ).group_by(
                Project.category
            ).order_by(
                func.count(Project.id).desc()
            ).all()
            
            categories_dict = {category: count for category, count in categories}
            
            return {
                "status": "success",
                "cards": {
                    "total_capstones": total_capstones,
                    "total_views": total_views,
                    "total_search": total_searches,
                    "recent_capstones_total": recent_capstones
                },
                "most_searched": most_searched_dict,
                "most_viewed": most_viewed_dict,
                "categories": categories_dict
            }
        
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error fetching statistics: {str(e)}")
