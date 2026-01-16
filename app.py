import streamlit as st
from auth import register_user, login_user
from database import SessionLocal
from models import Skill, StudySession, User
import datetime
import pandas as pd
import plotly.express as px
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO



# Session state
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "name" not in st.session_state:
    st.session_state.name = None
if "role" not in st.session_state:
    st.session_state.role = None
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "page" not in st.session_state:
    st.session_state.page = "login"

st.title("Study & Skill Management System")

# ---------------- LOGIN / REGISTER ----------------
if not st.session_state.logged_in:

    if st.session_state.page == "login":
        st.subheader("Login")

        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submit_login = st.form_submit_button("Login")

        if submit_login:
            if not email or not password:
                st.warning("Please enter both email and password.")
            else:
                success, name, role, user_id = login_user(email, password)
                if success:
                    st.session_state.logged_in = True
                    st.session_state.name = name
                    st.session_state.role = role
                    st.session_state.user_id = user_id
                    st.rerun()
                else:
                    st.error(role)

        if st.button("Go to Register"):
            st.session_state.page = "register"
            st.rerun()

    else:
        st.subheader("Register")

        with st.form("register_form"):
            name = st.text_input("Name")
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submit_register = st.form_submit_button("Register")

        if submit_register:
            if not name or not email or not password:
                st.warning("All fields are required.")
            else:
                success, msg = register_user(name, email, password)
                if success:
                    st.success(msg)
                    st.session_state.page = "login"
                    st.rerun()
                else:
                    st.error(msg)

        if st.button("Back to Login"):
            st.session_state.page = "login"
            st.rerun()

# ---------------- DASHBOARD ----------------
else:
    st.success(f"Welcome {st.session_state.name} ({st.session_state.role})")

    st.sidebar.title(f"Welcome {st.session_state.name} ({st.session_state.role})")
    
    if st.session_state.role == "admin":
        menu = st.sidebar.radio("Navigation", ["Dashboard", "Admin Panel", "Add Skill", "My Skills", "Log Study", "History", "Analytics"])
    else:
        menu = st.sidebar.radio("Navigation", ["Dashboard", "Add Skill", "My Skills", "Log Study", "History", "Analytics"])

    if st.sidebar.button("Logout"):

        st.session_state.logged_in = False
        st.session_state.page = "login"
        st.rerun()

    # ------------------ PAGES ------------------
    
    if menu == "Dashboard":
        st.subheader("Your Dashboard")
        st.write("Welcome to your study tracker!")

    elif menu == "Add Skill":
        st.subheader("Add a New Skill")
        
        with st.form("add_skill_form"):
            name = st.text_input("Skill Name (e.g. Python)")
            description = st.text_area("Description (optional)")
            submit = st.form_submit_button("Add Skill")


            if submit:
                if name:
                    db = SessionLocal()
                    new_skill = Skill(user_id=st.session_state.user_id, name=name, description=description)
                    db.add(new_skill)
                    db.commit()
                    db.close()
                    st.success(f"Added skill: {name}")
                else:
                    st.error("Skill name is required")

    elif menu == "My Skills":
        st.subheader("My Skills")
        
        db = SessionLocal()
        skills = db.query(Skill).filter(Skill.user_id == st.session_state.user_id).all()
        db.close()

        if skills:
            for skill in skills:
                with st.expander(f"📘 {skill.name}"):
                    st.write(skill.description)
                    st.write(f"ID: {skill.id}")
        else:
            st.info("No skills added yet. Go to 'Add Skill' to get started!")

    elif menu == "Log Study":
        st.subheader("Log Study Session")

        db = SessionLocal()
        skills = db.query(Skill).filter(Skill.user_id == st.session_state.user_id).all()
        db.close()

        if not skills:
            st.warning("You need to add skills before you can log study time.")
        else:
            skill_names = {skill.name: skill.id for skill in skills}
            
            with st.form("log_study_form"):
                selected_skill = st.selectbox("Select Skill", list(skill_names.keys()))
                date = st.date_input("Date", datetime.date.today())
                hours = st.number_input("Hours Studied", min_value=0.1, step=0.5)
                notes = st.text_area("Notes (What did you learn?)")
                submit = st.form_submit_button("Log Session")

                if submit:
                    db = SessionLocal()
                    new_session = StudySession(
                        skill_id=skill_names[selected_skill],
                        date=date,
                        hours=hours,
                        notes=notes
                    )
                    db.add(new_session)
                    db.commit()
                    db.close()
                    st.success(f"Logged {hours} hours for {selected_skill}!")

    elif menu == "History":
        st.subheader("Study History")

        db = SessionLocal()
        # Join StudySession and Skill to get skill name, filter by user_id
        sessions = db.query(StudySession, Skill.name).join(Skill).filter(Skill.user_id == st.session_state.user_id).all()
        db.close()

        if sessions:
            # Prepare data for display
            history_data = []
            for session, skill_name in sessions:
                history_data.append({
                    "ID": session.id,
                    "Date": session.date,
                    "Skill": skill_name,
                    "Hours": session.hours,
                    "Notes": session.notes
                })
            
            st.table(history_data)

            # Delete Functionality
            st.divider()
            st.subheader("Delete a Session")
            session_ids = [s["ID"] for s in history_data]
            selected_id = st.selectbox("Select Session ID to Delete", session_ids)

            if st.button("Delete Session"):
                db = SessionLocal()
                session_to_delete = db.query(StudySession).filter(StudySession.id == selected_id).first()
                if session_to_delete:
                    db.delete(session_to_delete)
                    db.commit()
                    st.success(f"Deleted session {selected_id}")
                    st.rerun()
                else:
                    st.error("Session not found.")
                db.close()

        else:
            st.info("No study sessions logged yet.")

    elif menu == "Analytics":
        st.subheader("Analytics Dashboard")
        
        db = SessionLocal()
        # 1. Get all skills for the user
        all_skills = db.query(Skill.name).filter(Skill.user_id == st.session_state.user_id).all()
        skill_list = [s[0] for s in all_skills]

        # 2. Get study sessions
        sessions = db.query(StudySession.date, Skill.name, StudySession.hours).join(Skill).filter(Skill.user_id == st.session_state.user_id).all()
        db.close()

        if skill_list:
            # Create a base DataFrame with all skills (initialized to 0 hours)
            # This ensures even skills with no sessions appear
            if sessions:
                df_sessions = pd.DataFrame(sessions, columns=["Date", "Skill", "Hours"])
            else:
                df_sessions = pd.DataFrame(columns=["Date", "Skill", "Hours"])

            # Metric: Total Hours
            total_hours = df_sessions["Hours"].sum() if not df_sessions.empty else 0
            st.metric("Total Hours Studied", f"{total_hours} hrs")

            # Chart 1: Hours by Skill (Include 0 hours)
            # Group by skill from sessions
            if not df_sessions.empty:
                skill_group = df_sessions.groupby("Skill")["Hours"].sum().reset_index()
            else:
                skill_group = pd.DataFrame(columns=["Skill", "Hours"])
            
            # Merge with full skill list to ensure all are present
            df_all_skills = pd.DataFrame(skill_list, columns=["Skill"])
            final_df = pd.merge(df_all_skills, skill_group, on="Skill", how="left").fillna(0)

            fig_bar = px.bar(final_df, x="Skill", y="Hours", color="Skill", title="Total Hours per Subject")
            st.plotly_chart(fig_bar)

            # Chart 2: Study Trend (over time)
            st.subheader("Study Trend")
            if not df_sessions.empty:
                date_group = df_sessions.groupby("Date")["Hours"].sum().reset_index()
                fig_line = px.line(date_group, x="Date", y="Hours", markers=True, title="Daily Study Hours")
                st.plotly_chart(fig_line)
            else:
                st.info("Log some study sessions to see your daily trend!")

            # PDF Export
            st.divider()
            st.subheader("Export Report")
            if st.button("Generate PDF Report"):
                buffer = BytesIO()
                p = canvas.Canvas(buffer, pagesize=letter)
                p.drawString(100, 750, f"Study Report for {st.session_state.name}")
                p.drawString(100, 730, f"Date: {datetime.date.today()}")
                
                y = 700
                if sessions:
                    p.drawString(100, y, "Summary:")
                    y -= 20
                    # Reuse total hours
                    p.drawString(120, y, f"Total Hours Studied: {total_hours}")
                    y -= 30
                    
                    p.drawString(100, y, "Details:")
                    y -= 20
                    # Simple list of sessions
                    for session in sessions:
                        # session is a tuple: (date, skill_name, hours)
                        p.drawString(120, y, f"- {session[0]}: {session[1]} ({session[2]} hrs)")
                        y -= 15
                        if y < 50: # New page if needed
                            p.showPage()
                            y = 750
                else:
                    p.drawString(100, y, "No sessions found.")

                p.save()
                buffer.seek(0)
                st.download_button(label="Download PDF", data=buffer, file_name="study_report.pdf", mime="application/pdf")
        
        else:
            st.info("No skills added yet. Go to 'Add Skill' to get started!")

    elif menu == "Admin Panel":
        st.subheader("Admin Panel 🛠️")
        if st.session_state.role != "admin":
            st.error("Access Denied")
        else:
            db = SessionLocal()
            users = db.query(User).all()
            total_users = len(users)
            
            # Global stats
            total_sessions = db.query(StudySession).count()
            
            col1, col2 = st.columns(2)
            col1.metric("Total Users", total_users)
            col2.metric("Total Study Sessions", total_sessions)
            
            st.subheader("User List")
            user_data = [{"ID": u.id, "Name": u.name, "Email": u.email, "Role": u.role} for u in users]
            st.table(user_data)
            db.close()
