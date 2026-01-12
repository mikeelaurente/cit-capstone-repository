import json
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, ForeignKey, Integer, LargeBinary, String, Text, event
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from sqlalchemy import DateTime
from typing import List, Optional

from helpers.embedding import encode_text

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    role = Column(String, default="Staff")

class Student(Base):
    __tablename__ = "students"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    full_name: Mapped[str] = mapped_column(String, nullable=False)
    student_number: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    password: Mapped[str] = mapped_column(String, nullable=False)
    year: Mapped[str] = mapped_column(String, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Integer, default=0)  # SQLite uses 0/1 for bool
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    submissions: Mapped[List["Submission"]] = relationship(back_populates="student", cascade="all, delete-orphan")

class EmailVerification(Base):
    __tablename__ = "email_verifications"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"))
    code: Mapped[str] = mapped_column(String, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class PasswordReset(Base):
    __tablename__ = "password_resets"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"))
    token: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class Submission(Base):
    __tablename__ = "submissions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"))
    project_id: Mapped[Optional[int]] = mapped_column(ForeignKey("projects.id", ondelete="SET NULL"), nullable=True)
    status: Mapped[str] = mapped_column(String, default="pending")  # pending, approved, rejected
    submitted_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    admin_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    student: Mapped["Student"] = relationship(back_populates="submissions")
    project: Mapped[Optional["Project"]] = relationship()

class Project(Base):
    __tablename__ = "projects"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sha256: Mapped[str] = mapped_column(String, unique=True, index=True)
    filename: Mapped[str] = mapped_column(String)
    title: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    external_links: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    abstract: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    status: Mapped[str] = mapped_column(String, default="pending")  # pending, approved, rejected

    # DOCX metadata fields
    course: Mapped[Optional[str]]   = mapped_column(String, nullable=True)
    host: Mapped[Optional[str]]     = mapped_column(String, nullable=True)
    doc_type: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    authors:  Mapped[List["Author"]]         = relationship(back_populates="project", cascade="all, delete-orphan")
    sections: Mapped[List["Section"]]        = relationship(back_populates="project", cascade="all, delete-orphan")
    chunks:   Mapped[List["Chunk"]]          = relationship(back_populates="project", cascade="all, delete-orphan")
    keywords: Mapped[List["ProjectKeyword"]] = relationship(back_populates="project", cascade="all, delete-orphan")

class ProjectKeyword(Base):
    __tablename__ = "project_keywords"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))
    keyword: Mapped[str] = mapped_column(String, index=True)
    project: Mapped[Project] = relationship(back_populates="keywords")

class Section(Base):
    __tablename__ = "sections"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))
    heading: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    content: Mapped[str] = mapped_column(Text)
    order_no: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    project: Mapped[Project] = relationship(back_populates="sections")
    chunks: Mapped[List["Chunk"]] = relationship(back_populates="section", cascade="all, delete-orphan")

class Chunk(Base):
    __tablename__ = "chunks"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))
    section_id: Mapped[Optional[int]] = mapped_column(ForeignKey("sections.id", ondelete="SET NULL"), nullable=True)
    content: Mapped[str] = mapped_column(Text)
    ord_in_sec: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    project: Mapped[Project] = relationship(back_populates="chunks")
    section: Mapped[Optional[Section]] = relationship(back_populates="chunks")
    embedding: Mapped[Optional["Embedding"]] = relationship(back_populates="chunk", uselist=False, cascade="all, delete-orphan")


class Author(Base):
    __tablename__ = "authors"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))
    full_name: Mapped[str] = mapped_column(String)
    project: Mapped[Project] = relationship(back_populates="authors")



class Embedding(Base):
    __tablename__ = "embeddings"
    chunk_id: Mapped[int] = mapped_column(ForeignKey("chunks.id", ondelete="CASCADE"), primary_key=True)
    vector: Mapped[bytes] = mapped_column(LargeBinary)
    chunk: Mapped[Chunk] = relationship(back_populates="embedding")
    

@event.listens_for(Base.metadata, "after_create")
def create_fts(target, connection, **kw):
    connection.exec_driver_sql("""
    CREATE VIRTUAL TABLE IF NOT EXISTS projects_fts
    USING fts5(title, abstract, content, project_id UNINDEXED, tokenize="porter");
    """)
