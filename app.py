
import streamlit as st
from database import engine
from models import Base

st.set_page_config(page_title="Study Tracker", layout="centered")
st.title("Study & Skill Management System")
st.write("Day 1 – Database Creation")

if st.button("Create All Tables in MySQL"):
    with st.spinner("Creating database and tables..."):
        Base.metadata.create_all(bind=engine)
    st.success("Database + All tables created successfully!")
    st.balloons()