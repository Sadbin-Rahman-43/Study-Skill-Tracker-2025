# database.py  ← REPLACE YOUR OLD FILE WITH THIS
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import streamlit as st

secrets = st.secrets["mysql"]
DATABASE_URL = f"mysql+mysqlconnector://{secrets.user}:{secrets.password}@{secrets.host}:{secrets.port}"

# Step 1: Connect without database name to create the DB if missing
engine_no_db = create_engine(DATABASE_URL)
with engine_no_db.connect() as conn:
    conn.execute(text("CREATE DATABASE IF NOT EXISTS study_tracker"))
    conn.execute(text("COMMIT"))

# Step 2: Now connect to the actual database
DATABASE_URL_WITH_DB = f"{DATABASE_URL}/study_tracker"
engine = create_engine(DATABASE_URL_WITH_DB, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()