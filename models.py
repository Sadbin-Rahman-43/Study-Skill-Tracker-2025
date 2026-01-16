from sqlalchemy import Column, Integer, String, DateTime, Enum, Text, ForeignKey, Date, Float
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
    sessions = relationship("StudySession", back_populates="skill")


class StudySession(Base):
    __tablename__ = "study_sessions"

    id = Column(Integer, primary_key=True, index=True)
    skill_id = Column(Integer, ForeignKey("skills.id"), nullable=False)
    date = Column(Date, nullable=False)
    hours = Column(Float, nullable=False)
    notes = Column(Text, nullable=True)

    skill = relationship("Skill", back_populates="sessions")


User.skills = relationship("Skill", back_populates="user")

# CREATE TABLE IF NOT EXISTS (SAFE)
Base.metadata.create_all(engine)
