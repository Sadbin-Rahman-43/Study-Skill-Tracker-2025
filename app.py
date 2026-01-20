import streamlit as st
from auth import register_user, login_user
from database_utils import get_db
from sqlalchemy import func
from models import Skill, StudySession, User, StudyTask, Goal
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
        menu = st.sidebar.radio("Navigation", ["Dashboard", "Study Plan", "Goals", "Admin Panel", "Manage Skills", "Log Study", "History", "Analytics"])
    else:
        menu = st.sidebar.radio("Navigation", ["Dashboard", "Study Plan", "Goals", "Manage Skills", "Log Study", "History", "Analytics"])

    if st.sidebar.button("Logout"):

        st.session_state.logged_in = False
        st.session_state.page = "login"
        st.rerun()

    # ------------------ PAGES ------------------
    
    if menu == "Dashboard":
        st.subheader("Your Dashboard")
        st.write("Welcome to your study tracker!")
        st.info("Check your 'Study Plan' to manage daily tasks!")

    elif menu == "Study Plan":
        st.subheader("Study Plan & To-Do 📝")
        
        with get_db() as db:
            # --- 1. BACKLOG CHECKER ---
            today = datetime.date.today()
            backlog_query = db.query(StudyTask).filter(
                StudyTask.user_id == st.session_state.user_id,
                StudyTask.due_date < today,
                StudyTask.status == "Pending"
            ).all()

            if backlog_query:
                st.error(f"⚠️ You have {len(backlog_query)} Overdue Tasks! (Backlog)")
                with st.expander("View Backlog"):
                    for task in backlog_query:
                        col1, col2 = st.columns([3, 1])
                        col1.write(f"❌ {task.task} (Due: {task.due_date})")
                        if col2.button("Complete", key=f"backlog_{task.id}"):
                            task.status = "Completed"
                            db.commit()
                            st.rerun()

            
            # --- 2. ADD NEW TASK ---
            with st.expander("➕ Add New Task"):
                with st.form("new_task_form"):
                    t_desc = st.text_input("Task Description (e.g., Read Chapter 4)")
                    t_skill = st.selectbox("Related Skill (Optional)", ["None"] + [s.name for s in db.query(Skill).filter(Skill.user_id == st.session_state.user_id).all()])
                    t_date = st.date_input("Due Date", today)
                    t_submit = st.form_submit_button("Add Task")

                    if t_submit and t_desc:
                        skill_id = None
                        if t_skill != "None":
                             # Find skill ID
                             sk = db.query(Skill).filter(Skill.name == t_skill, Skill.user_id == st.session_state.user_id).first()
                             if sk: skill_id = sk.id
                        
                        new_task = StudyTask(
                            user_id=st.session_state.user_id,
                            skill_id=skill_id, 
                            task=t_desc,
                            due_date=t_date,
                            status="Pending"
                        )
                        db.add(new_task)
                        db.commit()
                        st.success("Task Added!")
                        st.rerun()

            # --- 3. TODAY'S TASKS ---
            st.divider()
            st.write(f"### Today's Tasks ({today})")
            
            todays_tasks = db.query(StudyTask).filter(
                StudyTask.user_id == st.session_state.user_id,
                StudyTask.due_date == today
            ).all()

            if todays_tasks:
                # Progress Bar
                completed_count = sum(1 for t in todays_tasks if t.status == "Completed")
                total_count = len(todays_tasks)
                progress = completed_count / total_count
                st.progress(progress)
                st.caption(f"{completed_count}/{total_count} Completed")

                for task in todays_tasks:
                    col1, col2 = st.columns([0.1, 0.9])
                    
                    # Checkbox logic (Using session state to handle instant updates)
                    is_done = task.status == "Completed"
                    checked = col1.checkbox("Done", value=is_done, key=f"check_{task.id}", label_visibility="hidden")
                    
                    if checked != is_done:
                        task.status = "Completed" if checked else "Pending"
                        db.commit()
                        st.rerun()
                    
                    if is_done:
                        col2.markdown(f"~~{task.task}~~")
                    else:
                        col2.write(task.task)

            else:
                st.info("No tasks scheduled for today. Add one above! 👆")

    elif menu == "Goals":
        st.subheader("Goal Tracking 🎯")
        
        tab1, tab2 = st.tabs(["Active Goals", "Set New Goal"])
        
        # --- TAB 1: ACTIVE GOALS ---
        with tab1:
            with get_db() as db:
                goals = db.query(Goal).filter(Goal.user_id == st.session_state.user_id).all()
                if goals:
                    for goal in goals:
                        with st.expander(f"{goal.goal_name} ({goal.progress}%) - {goal.status}"):
                            # 1. Update Progress
                            new_prog = st.slider(f"Progress (%) for {goal.goal_name}", 0, 100, goal.progress, key=f"prog_{goal.id}")
                            if new_prog != goal.progress:
                                goal.progress = new_prog
                                if new_prog == 100: goal.status = "Achieved"
                                db.commit()
                                st.rerun()

                            # 2. Mark Achieved Button
                            if goal.status != "Achieved":
                                if st.button("Mark as Achieved 🏆", key=f"achieve_{goal.id}"):
                                    goal.status = "Achieved"
                                    goal.progress = 100
                                    db.commit()
                                    st.balloons()
                                    st.rerun()
                            else:
                                st.success("Goal Achieved! 🎉")

                else:
                    st.info("No active goals. Set one in the next tab!")

        # --- TAB 2: SET NEW GOAL ---
        with tab2:
            with st.form("new_goal_form"):
                g_name = st.text_input("Goal Name (e.g., Complete Python Course)")
                g_date = st.date_input("Target Date", datetime.date.today() + datetime.timedelta(days=30))
                g_submit = st.form_submit_button("Set Goal")
                
                if g_submit and g_name:
                    with get_db() as db:
                        new_goal = Goal(
                            user_id=st.session_state.user_id,
                            goal_name=g_name,
                            target_date=g_date
                        )
                        db.add(new_goal)
                        db.commit()
                    st.success("New Goal Set!")
                    st.rerun()

    elif menu == "Manage Skills":
        st.subheader("Manage Skills 🛠️")
        
        tab1, tab2 = st.tabs(["My Skills (View/Edit/Delete)", "Add New Skill"])
        
        # --- TAB 1: VIEW / EDIT / DELETE ---
        with tab1:
            with get_db() as db:
                skills = db.query(Skill).filter(Skill.user_id == st.session_state.user_id).all()
                
                if skills:
                    for skill in skills:
                        with st.expander(f"📘 {skill.name}", expanded=False):
                            col1, col2 = st.columns([3, 1])
                            with col1:
                                st.write(f"**Description:** {skill.description}")
                                st.caption(f"Skill ID: {skill.id}")
                            
                            with col2:
                                # Edit Button Toggle
                                if st.button("Edit", key=f"edit_btn_{skill.id}"):
                                    st.session_state[f"edit_mode_{skill.id}"] = True
                                
                                # Delete Button
                                if st.button("Delete", key=f"del_btn_{skill.id}", type="primary"):
                                    db.delete(skill)
                                    db.commit()
                                    st.success(f"Deleted {skill.name}")
                                    st.rerun()

                            # --- EDIT FORM (Visible if Edit clicked) ---
                            if st.session_state.get(f"edit_mode_{skill.id}", False):
                                st.info(f"Editing {skill.name}")
                                with st.form(f"edit_skill_{skill.id}"):
                                    new_name = st.text_input("New Name", value=skill.name)
                                    new_desc = st.text_area("New Description", value=skill.description)
                                    
                                    if st.form_submit_button("Save Changes"):
                                        skill.name = new_name
                                        skill.description = new_desc
                                        db.commit()
                                        st.session_state[f"edit_mode_{skill.id}"] = False # Close edit mode
                                        st.success("Skill updated successfully!")
                                        st.rerun()
                                        
                                    if st.form_submit_button("Cancel"):
                                        st.session_state[f"edit_mode_{skill.id}"] = False
                                        st.rerun()
                else:
                    st.info("No skills found. Add one in the next tab!")

        # --- TAB 2: CREATE ---
        with tab2:
            st.subheader("Add a New Skill")
            with st.form("add_skill_form"):
                name = st.text_input("Skill Name (e.g. Python)")
                description = st.text_area("Description (optional)")
                submit = st.form_submit_button("Add Skill")

                if submit:
                    if name:
                        with get_db() as db:
                            new_skill = Skill(user_id=st.session_state.user_id, name=name, description=description)
                            db.add(new_skill)
                            db.commit()
                        st.success(f"Added skill: {name}")
                        st.balloons()
                    else:
                        st.error("Skill name is required")

    elif menu == "Log Study":
        st.subheader("Log Study Session")

        with get_db() as db:
            skills = db.query(Skill).filter(Skill.user_id == st.session_state.user_id).all()

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
                    with get_db() as db:
                        new_session = StudySession(
                            skill_id=skill_names[selected_skill],
                            date=date,
                            hours=hours,
                            notes=notes
                        )
                        db.add(new_session)
                        db.commit()
                    st.success(f"Logged {hours} hours for {selected_skill}!")

    elif menu == "History":
        st.subheader("Study History (Advanced Filter & Edit) 🔍")

        with get_db() as db:
            # --- DATE FILTER ---
            col1, col2 = st.columns(2)
            start_date = col1.date_input("Start Date", datetime.date.today() - datetime.timedelta(days=30))
            end_date = col2.date_input("End Date", datetime.date.today())

            # Base Query
            query = db.query(StudySession, Skill.name).join(Skill).filter(
                Skill.user_id == st.session_state.user_id,
                StudySession.date >= start_date,
                StudySession.date <= end_date
            )
            
            # --- SHOW SQL (Teacher Impressor) ---
            with st.expander("Show SQL Code (For DBMS Class)"):
                # Compile parameters for display
                sql_statement = str(query.statement.compile(compile_kwargs={"literal_binds": True}))
                st.code(sql_statement, language="sql")

            sessions = query.order_by(StudySession.date.desc()).all()

        if sessions:
            for session, skill_name in sessions:
                with st.expander(f"{session.date} - {skill_name} ({session.hours} hrs)"):
                    # Display Mode
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.markdown(f"**Notes:** {session.notes}")
                    with col2:
                        # Edit Toggle
                        if st.button("Edit", key=f"sess_edit_{session.id}"):
                            st.session_state[f"sess_edit_mode_{session.id}"] = True
                    
                    # Edit Mode
                    if st.session_state.get(f"sess_edit_mode_{session.id}", False):
                        st.info("Editing Session")
                        with st.form(f"edit_sess_form_{session.id}"):
                            # Pre-fill data
                            new_date = st.date_input("Date", value=session.date)
                            new_hours = st.number_input("Hours", value=float(session.hours), min_value=0.1, step=0.5)
                            new_notes = st.text_area("Notes", value=session.notes)
                            
                            if st.form_submit_button("Update Session"):
                                with get_db() as db:
                                    # Fetch fresh object to update
                                    s_to_update = db.query(StudySession).filter(StudySession.id == session.id).first()
                                    s_to_update.date = new_date
                                    s_to_update.hours = new_hours
                                    s_to_update.notes = new_notes
                                    db.commit()
                                table_updated = True
                                st.session_state[f"sess_edit_mode_{session.id}"] = False
                                st.success("Updated!")
                                st.rerun()

            # Delete Functionality (Simplified at bottom)
            st.divider()
            st.subheader("Delete a Session")
            session_ids = [s[0].id for s in sessions] # s is (StudySession, skill_name)
            if session_ids:
                selected_id = st.selectbox("Select Session ID to Delete", session_ids)
                if st.button("Delete Session", type="primary"):
                    with get_db() as db:
                        session_to_delete = db.query(StudySession).filter(StudySession.id == selected_id).first()
                        if session_to_delete:
                            db.delete(session_to_delete)
                            db.commit()
                            st.success(f"Deleted session {selected_id}")
                            st.rerun()
                        else:
                            st.error("Session not found.")
        else:
            st.info("No study sessions found in this date range.")

    elif menu == "Analytics":
        st.subheader("Analytics Dashboard")
        
        with get_db() as db:
            # 1. Total Hours (SQL Aggregate)
            q1 = db.query(func.sum(StudySession.hours)).join(Skill).filter(Skill.user_id == st.session_state.user_id)
            total_hours = q1.scalar() or 0
            
            # 2. Hours by Skill (SQL Group By)
            q2 = db.query(Skill.name, func.sum(StudySession.hours).label("hours")).join(StudySession).filter(Skill.user_id == st.session_state.user_id).group_by(Skill.name)
            skill_stats = q2.all()
            
            # 3. Daily Trend (SQL Group By)
            q3 = db.query(StudySession.date, func.sum(StudySession.hours).label("hours")).join(Skill).filter(Skill.user_id == st.session_state.user_id).group_by(StudySession.date).order_by(StudySession.date)
            daily_stats = q3.all()
            
            # 4. Raw Data for PDF
            sessions = db.query(StudySession.date, Skill.name, StudySession.hours).join(Skill).filter(Skill.user_id == st.session_state.user_id).order_by(StudySession.date.desc()).all()

            # --- TASK ANALYTICS ---
            q_tasks = db.query(StudyTask.status, func.count(StudyTask.id)).filter(StudyTask.user_id == st.session_state.user_id).group_by(StudyTask.status)
            task_stats = q_tasks.all() # [(Pending, 5), (Completed, 3)]

            # --- SHOW SQL (Teacher Impressor) ---
            with st.expander("Show SQL Code (For DBMS Class)"):
                st.markdown("**1. Total Hours Query:**")
                st.code(str(q1.statement.compile(compile_kwargs={"literal_binds": True})), language="sql")
                st.markdown("**2. Hours by Skill Query (GROUP BY):**")
                st.code(str(q2.statement.compile(compile_kwargs={"literal_binds": True})), language="sql")
                st.markdown("**3. Daily Trend Query:**")
                st.code(str(q3.statement.compile(compile_kwargs={"literal_binds": True})), language="sql")
                st.markdown("**4. Task Status Query (GROUP BY):**")
                st.code(str(q_tasks.statement.compile(compile_kwargs={"literal_binds": True})), language="sql")

        # Display Total
        st.metric("Total Hours Studied", f"{total_hours} hrs")

        # Chart 0: Task Completion (Pie Chart)
        if task_stats:
            st.divider()
            st.subheader("Task Completion Rates 🎯")
            df_tasks = pd.DataFrame(task_stats, columns=["Status", "Count"])
            fig_pie = px.pie(df_tasks, names="Status", values="Count", title="Task Status Overview", hole=0.4)
            st.plotly_chart(fig_pie)

        # Chart 0.5: Goal Progress
        with get_db() as db:
             goals = db.query(Goal.goal_name, Goal.progress).filter(Goal.user_id == st.session_state.user_id).all()
        
        if goals:
            st.divider()
            st.subheader("Goal Progress 🚀")
            df_goals = pd.DataFrame(goals, columns=["Goal", "Progress"])
            fig_goals = px.bar(df_goals, x="Goal", y="Progress", range_y=[0, 100], title="Long-term Goal Progress (%)", color="Progress")
            st.plotly_chart(fig_goals)

        # Chart 1: Hours by Skill
        if skill_stats:
            df_skills = pd.DataFrame(skill_stats, columns=["Skill", "Hours"])
            fig_bar = px.bar(df_skills, x="Skill", y="Hours", color="Skill", title="Total Hours per Subject (SQL Aggregated)")
            st.plotly_chart(fig_bar)
        else:
            st.info("No study data by skill yet.")

        # Chart 2: Study Trend
        st.subheader("Study Trend")
        if daily_stats:
            df_trend = pd.DataFrame(daily_stats, columns=["Date", "Hours"])
            fig_line = px.line(df_trend, x="Date", y="Hours", markers=True, title="Daily Study Hours (SQL Aggregated)")
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
        


    elif menu == "Admin Panel":
        st.subheader("Admin Panel 🛠️")
        if st.session_state.role != "admin":
            st.error("Access Denied")
        else:
            with get_db() as db:
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
