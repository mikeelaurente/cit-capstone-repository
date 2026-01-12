from typing import List, Optional
from pydantic import BaseModel, EmailStr

# ------------------------------
# Pydantic schemas
# ------------------------------

# Student DTOs
class StudentSignupRequest(BaseModel):
    full_name: str
    student_number: str
    email: EmailStr
    year: str  # Can include "Irregular"
    password: str

class StudentVerifyRequest(BaseModel):
    email: EmailStr
    code: str

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str
    confirm_password: str

class StudentResponse(BaseModel):
    id: int
    full_name: str
    student_number: str
    email: str
    year: str
    is_verified: bool
    
    class Config:
        from_attributes = True

class SubmissionCreate(BaseModel):
    title: str
    authors: str
    adviser: Optional[str] = None
    year: int

class SubmissionResponse(BaseModel):
    id: int
    status: str
    submitted_at: str
    reviewed_at: Optional[str] = None
    admin_notes: Optional[str] = None
    project_id: Optional[int] = None
    
    class Config:
        from_attributes = True

class CitationRequest(BaseModel):
    format: str  # APA, MLA, Chicago, IEEE

# Existing DTOs
class CapstoneCreate(BaseModel):
    title: str
    abstract: Optional[str] = None
    authors: str
    year: int
    external_link: Optional[str] = None

class CapstoneResponse(BaseModel):
    id: int
    title: str
    abstract: Optional[str]
    authors: List[str]
    keywords: List[str]
    year: int

class UserCreate(BaseModel):
    email: str
    password: str
    role: str = "Staff"

class UserUpdate(BaseModel):
    email: Optional[str]
    password: Optional[str]
    role: Optional[str]

class UserResponse(BaseModel):
    id: int
    email: str
    role: str
    
    class Config:
        from_attributes = True


class SearchQuery(BaseModel):
    text: str

class ProjectOut(BaseModel):
    id: int
    title: Optional[str]
    year: Optional[int]
    abstract: Optional[str]
    authors: List[str]
    course: Optional[str] = None
    host: Optional[str] = None
    doc_type: Optional[str] = None
    external_links: Optional[str] = None
    keywords: List[str] = []
    
class PaginatedProjectOutput(BaseModel):
    total: int
    page: int
    per_page: int
    results: List[ProjectOut] = []
    
class SummarizeIn(BaseModel):
    query: str
    k: int = 12