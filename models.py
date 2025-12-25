
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, Date, DECIMAL, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum('admin', 'student'), default='student')
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Skill(Base):
    __tablename__ = "skills"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'))
    skill_name = Column(String(100), nullable=False)
    target_hours = Column(Integer, default=0)

class StudySession(Base):
    __tablename__ = "study_sessions"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'))
    skill_id = Column(Integer, ForeignKey('skills.id', ondelete='SET NULL'), nullable=True)
    session_date = Column(Date, nullable=False)
    hours = Column(DECIMAL(4,2), nullable=False)
    notes = Column(Text)

class DailyLog(Base):
    __tablename__ = "daily_logs"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'))
    log_date = Column(Date, nullable=False)
    task_done = Column(Text)
    blocker = Column(Text)
    next_plan = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())