from sqlalchemy import Column, Integer, String, DateTime, Enum, Text, ForeignKey, Date, Float, CheckConstraint, Index
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
        Index('idx_skill_date', 'skill_id', 'date'),  # Composite index for filtering by skill and date
    )

    skill = relationship("Skill", back_populates="sessions")


class StudyTask(Base):
    __tablename__ = "study_tasks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    skill_id = Column(Integer, ForeignKey("skills.id"), nullable=True) # Nullable for general tasks
    goal_id = Column(Integer, ForeignKey("goals.id"), nullable=True) # Link task to a goal
    task = Column(String(255), nullable=False)
    due_date = Column(Date, nullable=False, index=True)
    status = Column(Enum("Pending", "Completed", "Incomplete"), default="Pending")
    
    __table_args__ = (
        Index('idx_user_due_date', 'user_id', 'due_date'),  # Composite index for user's tasks by date
        Index('idx_user_status', 'user_id', 'status'),  # Index for filtering by user and completion status
    )
    
    user = relationship("User", back_populates="tasks")
    skill = relationship("Skill")
    goal = relationship("Goal", back_populates="tasks")


class Goal(Base):
    __tablename__ = "goals"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    goal_name = Column(String(255), nullable=False)
    target_date = Column(Date, nullable=False)
    status = Column(Enum("In Progress", "Achieved", "Missed"), default="In Progress")
    progress = Column(Integer, default=0) # 0 to 100

    user = relationship("User", back_populates="goals")
    tasks = relationship("StudyTask", back_populates="goal")


class Semester(Base):
    __tablename__ = "semesters"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(100), nullable=False)
    
    user = relationship("User", back_populates="semesters")
    subjects = relationship("Subject", back_populates="semester", cascade="all, delete-orphan")


class Subject(Base):
    __tablename__ = "subjects"

    id = Column(Integer, primary_key=True, index=True)
    semester_id = Column(Integer, ForeignKey("semesters.id"), nullable=False)
    name = Column(String(100), nullable=False)

    semester = relationship("Semester", back_populates="subjects")
    topics = relationship("Topic", back_populates="subject", cascade="all, delete-orphan")


class Topic(Base):
    __tablename__ = "topics"

    id = Column(Integer, primary_key=True, index=True)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False)
    name = Column(String(255), nullable=False)
    status = Column(Enum("Pending", "Completed"), default="Pending")

    subject = relationship("Subject", back_populates="topics")


class AuditLog(Base):
    """
    Audit Log table to track all important database operations
    Demonstrates transaction logging and accountability
    """
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Nullable for system operations
    action = Column(String(50), nullable=False)  # CREATE, UPDATE, DELETE
    table_name = Column(String(50), nullable=False)  # Which table was affected
    record_id = Column(Integer, nullable=True)  # ID of affected record
    details = Column(Text, nullable=True)  # Additional context (JSON format)
    timestamp = Column(DateTime, server_default=func.now(), index=True)
    
    __table_args__ = (
        Index('idx_user_timestamp', 'user_id', 'timestamp'),  # Audit queries by user and time
    )
    
    user = relationship("User")



User.skills = relationship("Skill", back_populates="user", cascade="all, delete-orphan")
User.tasks = relationship("StudyTask", back_populates="user", cascade="all, delete-orphan")
User.goals = relationship("Goal", back_populates="user", cascade="all, delete-orphan")
User.semesters = relationship("Semester", back_populates="user", cascade="all, delete-orphan")

# CREATE TABLE IF NOT EXISTS (SAFE)
Base.metadata.create_all(engine)
