from fastapi import FastAPI, HTTPException, Depends, Query
from sqlalchemy.orm import Session, selectinload
from pydantic import BaseModel
from db import get_db
from models import User, Student
from helpers.password import hash_password, verify_password
from helpers.session import get_current_user_jwt
from typing import Optional

class CreateUserRequest(BaseModel):
    full_name: Optional[str] = None  # For reference
    email: str
    password: str
    confirm_password: str
    role: str = "Staff"  # Admin or Staff

class UpdateUserRequest(BaseModel):
    full_name: Optional[str] = None  # For reference
    email: Optional[str] = None
    role: Optional[str] = None
    password: Optional[str] = None
    confirm_password: Optional[str] = None

def register_api_admin_users_route(app: FastAPI):
    
    @app.get("/api/admin/users")
    def list_users(
        page: int = Query(default=1, ge=1),
        limit: int = Query(default=10, ge=1, le=100),
        role: str = Query(default="All"),
        search: Optional[str] = Query(default=None),
        db: Session = Depends(get_db),
        claims = Depends(get_current_user_jwt)
    ):
        """List all users (Admin only) with pagination, role filter, and search - includes student info if role is Student"""
        if not claims or claims.get("role") != "Admin":
            raise HTTPException(status_code=403, detail="Admin access required")
        
        # Validate pagination parameters
        if page < 1:
            raise HTTPException(status_code=400, detail="Page must be >= 1")
        if limit < 1 or limit > 100:
            raise HTTPException(status_code=400, detail="Limit must be between 1 and 100")
        
        # Validate role filter
        valid_roles = ["All", "Admin", "Staff", "Student"]
        if role not in valid_roles:
            raise HTTPException(status_code=400, detail=f"Role must be one of: {', '.join(valid_roles)}")
        
        # Build query
        query = db.query(User)
        
        # Apply role filter
        if role != "All":
            query = query.filter(User.role == role)
        
        # Apply search filter if provided
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                (User.email.ilike(search_term)) | (User.full_name.ilike(search_term))
            )
        
        # Get total count
        total = query.count()
        
        # Eager load student relationship to avoid N+1 queries and apply pagination
        users = query.options(selectinload(User.student)).offset((page - 1) * limit).limit(limit).all()
        
        result = []
        for u in users:
            user_data = {
                "id": u.id,
                "email": u.email,
                "full_name": u.full_name,
                "role": u.role,
                "status": "Active"  # Can be extended with actual status field
            }
            
            # Include student information if role is Student
            if u.role == "Student" and u.student:
                user_data["student"] = {
                    "id": u.student.id,
                    "full_name": u.student.full_name,
                    "student_number": u.student.student_number,
                    "email": u.student.email,
                    "year": u.student.year,
                    "is_verified": bool(u.student.is_verified),
                    "created_at": u.student.created_at.isoformat()
                }
            
            result.append(user_data)
        
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
            "filter": {
                "role": role,
                "search": search
            },
            "users": result
        }
    
    @app.post("/api/admin/users")
    def create_user(
        request: CreateUserRequest,
        db: Session = Depends(get_db),
        claims = Depends(get_current_user_jwt)
    ):
        """Create new admin/staff account (Admin only)"""
        if not claims or claims.get("role") != "Admin":
            raise HTTPException(status_code=403, detail="Admin access required")
        
        # Validate passwords match
        if request.password != request.confirm_password:
            raise HTTPException(status_code=400, detail="Passwords do not match")
        
        # Validate password strength
        if len(request.password) < 8:
            raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
        
        # Check if email already exists
        existing = db.query(User).filter(User.email == request.email).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Validate role
        if request.role not in ["Admin", "Staff"]:
            raise HTTPException(status_code=400, detail="Role must be 'Admin' or 'Staff'")
        
        # Create user
        hashed_password = hash_password(request.password)
        new_user = User(
            email=request.email,
            password=hashed_password,
            role=request.role,
            full_name=request.full_name
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        return {
            "message": "User account created successfully",
            "status": "success",
            "data": {
                "id": new_user.id,
                "email": new_user.email,
                "full_name": new_user.full_name,
                "role": new_user.role,
                "account_status": "Inactive"  # Requires verification
            }
        }
    
    @app.put("/api/admin/users/{user_id}")
    def update_user(
        user_id: int,
        request: UpdateUserRequest,
        db: Session = Depends(get_db),
        claims = Depends(get_current_user_jwt)
    ):
        """Update admin/staff account details (Admin only)"""
        if not claims or claims.get("role") != "Admin":
            raise HTTPException(status_code=403, detail="Admin access required")
        
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Update email if provided
        if request.email:
            # Check if new email already exists
            existing = db.query(User).filter(
                User.email == request.email,
                User.id != user_id
            ).first()
            if existing:
                raise HTTPException(status_code=400, detail="Email already in use")
            user.email = request.email
        
        # Update role if provided
        if request.role:
            if request.role not in ["Admin", "Staff", "Student"]:
                raise HTTPException(status_code=400, detail="Role must be 'Admin' or 'Staff'")
            # If the current user is Student, prevent changing to Admin/Staff directly
            if user.role == "Student" and request.role in ["Admin", "Staff"]:
                raise HTTPException(status_code=400, detail="Cannot change Student role to Admin/Staff directly")
            # If the current user is Admin/Staff, prevent changing to Student directly
            if user.role in ["Admin", "Staff"] and request.role == "Student":
                raise HTTPException(status_code=400, detail="Cannot change Admin/Staff role to Student directly")
            user.role = request.role
        
        # Update password if provided
        if request.password:
            if request.password != request.confirm_password:
                raise HTTPException(status_code=400, detail="Passwords do not match")
            if len(request.password) < 8:
                raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
            user.password = hash_password(request.password)
        
        # Update full_name if provided
        if request.full_name:
            if user.role == "Student" and user.student:
                user.student.full_name = request.full_name
            else:
                user.full_name = request.full_name
            
        db.commit()
        db.refresh(user)
        
        return {
            "message": "User account updated successfully",
            "status": "success",
            "data": {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role
            }
        }
    
    @app.delete("/api/admin/users/{user_id}")
    def delete_user(
        user_id: int,
        db: Session = Depends(get_db),
        claims = Depends(get_current_user_jwt)
    ):
        """Deactivate/delete an admin account (Admin only)"""
        if not claims or claims.get("role") != "Admin":
            raise HTTPException(status_code=403, detail="Admin access required")
        
        # Prevent self-deletion
        if claims.get("sub") == db.query(User).filter(User.id == user_id).first().email:
            raise HTTPException(status_code=400, detail="Cannot delete your own account")
        
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        user_email = user.email
        db.delete(user)
        db.commit()
        
        return {
            "message": f"User account '{user_email}' has been deactivated",
            "status": "success"
        }
