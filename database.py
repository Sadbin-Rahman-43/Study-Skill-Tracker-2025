from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import streamlit as st

# Read MySQL credentials
db = st.secrets["mysql"]

DATABASE_URL = (
    f"mysql+mysqlconnector://{db.user}:"
    f"{db.password}@{db.host}:{db.port}/study_tracker"
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine)
