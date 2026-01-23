import streamlit as st
from auth import register_user, login_user
from database_utils import get_db
from sqlalchemy import func
from models import Skill, StudySession, User, StudyTask, Goal, Semester, Subject, Topic
from admin_panel import render_admin_panel
from advanced_sql import render_advanced_sql_page
from audit_utils import log_audit
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
    
    # Show Admin Panel to everyone (access control handled inside the panel)
    menu = st.sidebar.radio("Navigation", ["Dashboard", "Study Plan", "Goals", "Academic Tracker", "Admin Panel", "Advanced SQL", "Manage Skills", "Log Study", "History", "Analytics"])

    if st.sidebar.button("Logout"):

        st.session_state.logged_in = False
        st.session_state.page = "login"
        st.rerun()

    # ------------------ PAGES ------------------
    
    if menu == "Dashboard":
        st.subheader(f"👋 Hi, {st.session_state.name}!")
        st.write("Here is your daily overview.")
        
        with get_db() as db:
            today = datetime.date.today()
            
            # --- METRICS ---
            # 1. Study Hours Today
            today_hours = db.query(func.sum(StudySession.hours)).filter(StudySession.date == today).scalar() or 0
            # 2. Tasks Due Today
            today_tasks_count = db.query(func.count(StudyTask.id)).filter(StudyTask.user_id == st.session_state.user_id, StudyTask.due_date == today).scalar() or 0
            # 3. Tasks Completed Today
            today_tasks_done = db.query(func.count(StudyTask.id)).filter(StudyTask.user_id == st.session_state.user_id, StudyTask.due_date == today, StudyTask.status == "Completed").scalar() or 0
            
            m1, m2, m3 = st.columns(3)
            m1.metric("Hours Studied Today", f"{today_hours:.1f} hrs")
            m2.metric("Tasks Due", today_tasks_count)
            m3.metric("Tasks Completed", today_tasks_done)
            
            st.divider()
            
            # --- COLUMNS ---
            c_left, c_right = st.columns([1, 1])
            
            with c_left:
                st.subheader("📅 Today's To-Do")
                todays_tasks = db.query(StudyTask).filter(StudyTask.user_id == st.session_state.user_id, StudyTask.due_date == today).all()
                
                if todays_tasks:
                    for task in todays_tasks:
                        col_chk, col_txt = st.columns([0.1, 0.9])
                        is_done = task.status == "Completed"
                        if col_chk.checkbox("Done", value=is_done, key=f"dash_check_{task.id}", label_visibility="hidden"):
                            if not is_done:
                                task.status = "Completed"
                                db.commit()
                                st.rerun()
                        else:
                            if is_done:
                                task.status = "Pending"
                                db.commit()
                                st.rerun()
                        
                        label = f"~~{task.task}~~" if is_done else task.task
                        if task.goal:
                            label += f" *(Goal: {task.goal.goal_name})*"
                        col_txt.markdown(label)
                else:
                    st.info("No tasks for today. Check your Study Plan!")
                    if st.button("Go to Study Plan"):
                         pass # Navigation handled by sidebar usually, but button helps UX

            with c_right:
                st.subheader("⏳ Time Distribution (Today)")
                today_sessions = db.query(Skill.name, func.sum(StudySession.hours).label("hours"))\
                    .select_from(StudySession)\
                    .join(Skill)\
                    .filter(StudySession.date == today, Skill.user_id == st.session_state.user_id)\
                    .group_by(Skill.name).all()
                
                if today_sessions:
                     df_today = pd.DataFrame(today_sessions, columns=["Subject", "Hours"])
                     fig_donut = px.pie(df_today, names="Subject", values="Hours", hole=0.4)
                     st.plotly_chart(fig_donut, key="dash_donut_chart")
                else:
                    st.caption("No study sessions logged today.")


            st.divider()
            
            # Recent Activity Widget
            st.subheader("📌 Recent Activity")
            recent_sessions = db.query(StudySession.date, Skill.name, StudySession.hours)\
                .join(Skill)\
                .filter(Skill.user_id == st.session_state.user_id)\
                .order_by(StudySession.date.desc())\
                .limit(5).all()
            
            if recent_sessions:
                for session_date, skill_name, hours in recent_sessions:
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.write(f"📚 **{skill_name}** - {session_date}")
                    with col2:
                        st.write(f"*{hours:.1f} hrs*")
            else:
                st.info("No recent activity. Start logging your study sessions!")
            
            st.divider()
            st.info("💡 Tip: Use separate tabs to Manage Skills, Track Goals, or Log detailed sessions.")

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
                    
                    # Skills Dropdown
                    skills = db.query(Skill).filter(Skill.user_id == st.session_state.user_id).all()
                    t_skill = st.selectbox("Related Skill (Optional)", ["None"] + [s.name for s in skills])

                    # Goals Dropdown
                    goals = db.query(Goal).filter(Goal.user_id == st.session_state.user_id).filter(Goal.status != "Achieved").all()
                    t_goal = st.selectbox("Link to Goal (Optional)", ["None"] + [g.goal_name for g in goals])

                    t_date = st.date_input("Due Date", today)
                    t_submit = st.form_submit_button("Add Task")

                    if t_submit and t_desc:
                        skill_id = None
                        if t_skill != "None":
                             sk = next((s for s in skills if s.name == t_skill), None)
                             if sk: skill_id = sk.id
                        
                        goal_id = None
                        if t_goal != "None":
                            gl = next((g for g in goals if g.goal_name == t_goal), None)
                            if gl: goal_id = gl.id

                        new_task = StudyTask(
                            user_id=st.session_state.user_id,
                            skill_id=skill_id, 
                            goal_id=goal_id,
                            task=t_desc,
                            due_date=t_date,
                            status="Pending"
                        )
                        db.add(new_task)
                        db.commit()
                        st.success("Task Added & Linked!")
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
                    col1, col2, col3 = st.columns([0.1, 0.7, 0.2])
                    
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
                    
                    # Delete button
                    if col3.button("🗑️", key=f"del_task_{task.id}", help="Delete task"):
                        task_to_del = task
                        db.delete(task)
                        db.commit()
                        log_audit(db, st.session_state.user_id, "DELETE", "study_tasks", task_to_del.id, {"task": task_to_del.task})
                        st.rerun()

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
                        # Auto-Calculate Progress
                        total_linked = len(goal.tasks)
                        completed_linked = sum(1 for t in goal.tasks if t.status == "Completed")
                        
                        calc_progress = int((completed_linked / total_linked * 100)) if total_linked > 0 else 0
                        
                        # Update DB if changed
                        if calc_progress != goal.progress:
                            goal.progress = calc_progress
                            if calc_progress == 100 and goal.status != "Achieved":
                                goal.status = "Achieved"
                            db.commit() # Save calculated progress

                        with st.expander(f"{goal.goal_name} ({calc_progress}%) - {goal.status}"):
                            st.write(f"**Linked Tasks:** {completed_linked}/{total_linked}")
                            st.progress(calc_progress / 100)
                            
                            if total_linked == 0:
                                st.warning("No tasks linked! Go to 'Study Plan' and add a task linked to this goal.")
                            
                            # List tasks for this goal
                            for t in goal.tasks:
                                icon = "✅" if t.status == "Completed" else "⏳"
                                st.write(f"{icon} {t.task} (Due: {t.due_date})")

                            if goal.status == "Achieved":
                                st.success("Goal Achieved! 🎉")
                            
                            # Delete Goal
                            st.divider()
                            st.write("**⚠️ Delete Goal**")
                            confirm_del = st.checkbox(f"I confirm deletion", key=f"conf_goal_{goal.id}")
                            if st.button("Delete Goal", type="primary", disabled=not confirm_del, key=f"del_goal_{goal.id}"):
                                goal_to_del = goal
                                db.delete(goal)
                                db.commit()
                                log_audit(db, st.session_state.user_id, "DELETE", "goals", goal_to_del.id, {"goal_name": goal_to_del.goal_name})
                                st.success("Goal deleted!")
                                st.rerun()
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
                        log_audit(db, st.session_state.user_id, "CREATE", "goals", new_goal.id, {"goal_name": g_name})
                    st.success("New Goal Set!")
                    st.rerun()

    elif menu == "Academic Tracker":
        st.subheader("Academic Tracker 🎓")
        
        tab_manage, tab_track = st.tabs(["Manage Subjects", "Topic Tracker"])
        
        # --- TAB 1: MANAGE HIERARCHY ---
        with tab_manage:
            col1, col2 = st.columns(2)
            
            # 1. Add Semester
            with col1:
                st.write("### 1. New Semester")
                with st.form("add_sem"):
                    sem_name = st.text_input("Semester Name (e.g., Sem 4)")
                    sub_sem = st.form_submit_button("Add Semester")
                    if sub_sem and sem_name:
                        with get_db() as db:
                            new_sem = Semester(user_id=st.session_state.user_id, name=sem_name)
                            db.add(new_sem)
                            db.commit()
                        st.success(f"Added {sem_name}")
                        st.rerun()

            # 2. Add Subject
            with col2:
                st.write("### 2. New Subject")
                with get_db() as db:
                    sems = db.query(Semester).filter(Semester.user_id == st.session_state.user_id).all()
                    
                    if not sems:
                        st.warning("Add a Semester first!")
                    else:
                        with st.form("add_sub"):
                            s_sem = st.selectbox("Select Semester", [s.name for s in sems])
                            sub_name = st.text_input("Subject Name (e.g., DBMS)")
                            sub_sub = st.form_submit_button("Add Subject")
                            
                            if sub_sub and sub_name:
                                sem_id = next(s.id for s in sems if s.name == s_sem)
                                new_sub = Subject(semester_id=sem_id, name=sub_name)
                                db.add(new_sub)
                                db.commit()
                                st.success(f"Added {sub_name} to {s_sem}")
                                st.rerun()

            st.divider()
            with get_db() as db:
                # View Hierarchy
                my_sems = db.query(Semester).filter(Semester.user_id == st.session_state.user_id).all()
                if my_sems:
                    st.write("### Your Semesters")
                    for s in my_sems:
                        with st.expander(s.name):
                            subs = s.subjects
                            if subs:
                                for sub in subs:
                                    st.write(f"- 📘 {sub.name}")
                            else:
                                st.caption("No subjects yet.")

        # --- TAB 2: TOPIC TRACKER ---
        with tab_track:
            with get_db() as db:
                my_sems = db.query(Semester).filter(Semester.user_id == st.session_state.user_id).all()
                if not my_sems:
                    st.warning("Go to 'Manage Subjects' to set up your semesters first!")
                else:
                    # Filter Controls
                    c1, c2 = st.columns(2)
                    sel_sem_name = c1.selectbox("Filter Semester", [s.name for s in my_sems])
                    
                    sel_sem = next(s for s in my_sems if s.name == sel_sem_name)
                    my_subs = sel_sem.subjects
                    
                    if not my_subs:
                        st.info("No subjects in this semester.")
                    else:
                        sel_sub_name = c2.selectbox("Filter Subject", [s.name for s in my_subs])
                        sel_sub = next(s for s in my_subs if s.name == sel_sub_name)
                        
                        # --- SUBJECT PROGRESS ---
                        st.markdown(f"### 📘 {sel_sub.name}")
                        topics = sel_sub.topics
                        total_tops = len(topics)
                        done_tops = sum(1 for t in topics if t.status == "Completed")
                        prog = int((done_tops/total_tops)*100) if total_tops > 0 else 0
                        
                        st.progress(prog/100)
                        st.caption(f"Progress: {prog}% ({done_tops}/{total_tops} Topics)")
                        
                        # --- ADD TOPIC ---
                        with st.form("add_topic"):
                            t_name = st.text_input("New Topic Name (e.g., Normalization)")
                            if st.form_submit_button("Add Topic") and t_name:
                                new_topic = Topic(subject_id=sel_sub.id, name=t_name, status="Pending")
                                db.add(new_topic)
                                db.commit()
                                st.rerun()
                        
                        # --- TOPIC LIST ---
                        if topics:
                            st.write("#### Topics")
                            for topic in topics:
                                c_chk, c_txt = st.columns([0.1, 0.9])
                                is_done = topic.status == "Completed"
                                if c_chk.checkbox("Done", value=is_done, key=f"topic_{topic.id}", label_visibility="hidden"):
                                    if not is_done:
                                        topic.status = "Completed"
                                        db.commit()
                                        st.rerun()
                                else:
                                    if is_done:
                                        topic.status = "Pending"
                                        db.commit()
                                        st.rerun()
                                
                                if is_done:
                                    c_txt.markdown(f"~~{topic.name}~~")
                                else:
                                    c_txt.write(topic.name)

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
                                
                                # Delete Button with info
                                session_count = len(skill.sessions)
                                task_count = db.query(StudyTask).filter(StudyTask.skill_id == skill.id).count()
                                
                                if session_count > 0:
                                    st.caption(f"⚠️ {session_count} sessions")
                                if task_count > 0:
                                    st.caption(f"⚠️ {task_count} tasks will be unlinked")
                                
                                confirm_skill_del = st.checkbox("Confirm", key=f"conf_skill_{skill.id}", label_visibility="collapsed")
                                if st.button("Delete", key=f"del_btn_{skill.id}", type="primary", disabled=not confirm_skill_del):
                                    try:
                                        # First, nullify skill_id in all linked tasks
                                        linked_tasks = db.query(StudyTask).filter(StudyTask.skill_id == skill.id).all()
                                        for task in linked_tasks:
                                            task.skill_id = None
                                        
                                        # Now delete the skill (cascades to sessions)
                                        skill_to_del = skill
                                        db.delete(skill)
                                        db.commit()
                                        log_audit(db, st.session_state.user_id, "DELETE", "skills", skill_to_del.id, {"name": skill_to_del.name, "sessions": session_count})
                                        st.success(f"Deleted {skill_to_del.name} and {session_count} linked sessions")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Error deleting skill: {str(e)}")
                                        st.info("Please try again or contact support.")

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
                            log_audit(db, st.session_state.user_id, "CREATE", "skills", new_skill.id, {"name": name})
                        st.success(f"Added skill: {name}")
                        st.balloons()
                        st.rerun()
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
                date = st.date_input("Date", datetime.date.today(), help="Select the date when you studied")
                hours = st.number_input("Hours Studied", min_value=0.1, step=0.5, help="Enter study duration (e.g., 2.5 hours)")
                notes = st.text_area("Notes (Optional)", help="Add any study notes or topics covered")
                submit = st.form_submit_button("Log Session")
                
                if submit:
                    # Validate date
                    if date > datetime.date.today():
                        st.warning("⚠️ Future dates not recommended. Are you planning ahead?")
                    
                    try:
                        with get_db() as db:
                            new_session = StudySession(
                                skill_id=skill_names[selected_skill],
                                date=date,
                                hours=hours,
                                notes=notes
                            )
                            db.add(new_session)
                            db.commit()
                            log_audit(db, st.session_state.user_id, "CREATE", "study_sessions", new_session.id, {"skill": selected_skill, "hours": hours})
                        st.success(f"Logged {hours:.1f} hours for {selected_skill}!")
                    except Exception as e:
                        st.error(f"Error logging session: {str(e)}")
                        st.info("💡 Make sure you've selected a valid skill and entered positive hours.")

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
            
            # Additional Filters
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                search_text = st.text_input("🔍 Search Notes", placeholder="Type to filter by notes...")
            with col_f2:
                all_skills = db.query(Skill).filter(Skill.user_id == st.session_state.user_id).all()
                skill_names = ["All Skills"] + [s.name for s in all_skills]
                filter_skill = st.selectbox("Filter by Skill", skill_names)
            
            # Apply additional filters
            if search_text:
                query = query.filter(StudySession.notes.contains(search_text))
            
            if filter_skill != "All Skills":
                query = query.filter(Skill.name == filter_skill)
            
            # --- SHOW SQL (Teacher Impressor) ---
            with st.expander("Show SQL Code "):
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
                confirm_delete = st.checkbox("⚠️ I confirm deletion (cannot be undone)")
                if st.button("Delete Session", type="primary", disabled=not confirm_delete):
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
            with st.expander("Show SQL Code "):
                st.markdown("**1. Total Hours Query:**")
                st.code(str(q1.statement.compile(compile_kwargs={"literal_binds": True})), language="sql")
                st.markdown("**2. Hours by Skill Query (GROUP BY):**")
                st.code(str(q2.statement.compile(compile_kwargs={"literal_binds": True})), language="sql")
                st.markdown("**3. Daily Trend Query:**")
                st.code(str(q3.statement.compile(compile_kwargs={"literal_binds": True})), language="sql")
                st.markdown("**4. Task Status Query (GROUP BY):**")
                st.code(str(q_tasks.statement.compile(compile_kwargs={"literal_binds": True})), language="sql")

        # Display Total
        st.metric("Total Hours Studied", f"{total_hours:.1f} hrs")

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

        # PDF Export (Always Visible)
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
        
        # CSV Export
        st.divider()
        st.subheader("Export to CSV")
        if sessions:
            csv_data = pd.DataFrame(sessions, columns=["Date", "Skill", "Hours"])
            csv_string = csv_data.to_csv(index=False)
            st.download_button(
                label="📥 Download CSV",
                data=csv_string,
                file_name="study_sessions.csv",
                mime="text/csv"
            )
        


    
    elif menu == "Advanced SQL":
        with get_db() as db:
            render_advanced_sql_page(db)

    elif menu == "Admin Panel":
        if st.session_state.role != "admin":
            st.error("Access Denied: Admins Only")
        else:
            with get_db() as db:
                render_admin_panel(db)
