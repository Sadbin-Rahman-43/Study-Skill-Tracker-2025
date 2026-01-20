from sqlalchemy import Column, Integer, String, DateTime, Enum, Text, ForeignKey, Date, Float, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from database import engine

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    role = Column(Enum("admin", "student"), default="student")


class Skill(Base):
    __tablename__ = "skills"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)

    user = relationship("User", back_populates="skills")
    sessions = relationship("StudySession", back_populates="skill", cascade="all, delete-orphan")


class StudySession(Base):
    __tablename__ = "study_sessions"

    id = Column(Integer, primary_key=True, index=True)
    skill_id = Column(Integer, ForeignKey("skills.id"), nullable=False)
    date = Column(Date, nullable=False, index=True)
    hours = Column(Float, nullable=False)
    notes = Column(Text, nullable=True)

    __table_args__ = (
        CheckConstraint('hours > 0', name='check_positive_hours'),
    )

    skill = relationship("Skill", back_populates="sessions")


class StudyTask(Base):
    __tablename__ = "study_tasks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    skill_id = Column(Integer, ForeignKey("skills.id"), nullable=True) # Nullable for general tasks
    task = Column(String(255), nullable=False)
    due_date = Column(Date, nullable=False, index=True)
    status = Column(Enum("Pending", "Completed", "Incomplete"), default="Pending")
    
    user = relationship("User", back_populates="tasks")
    skill = relationship("Skill")


User.skills = relationship("Skill", back_populates="user", cascade="all, delete-orphan")
User.tasks = relationship("StudyTask", back_populates="user", cascade="all, delete-orphan")

# CREATE TABLE IF NOT EXISTS (SAFE)
Base.metadata.create_all(engine)
