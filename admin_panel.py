import streamlit as st
import pandas as pd
from sqlalchemy import func
import datetime
from models import User, Skill, StudySession, Goal, StudyTask
from auth import hash_password


def render_admin_panel(db):
    st.subheader("Admin Panel 🛠️")
    
    tab_users, tab_global, tab_analytics, tab_audit = st.tabs(["User Management", "Global Data (Skills/Goals)", "Admin Analytics", "Audit Logs"])
    
    # ==========================
    # TAB 1: USER MANAGEMENT
    # ==========================
    with tab_users:
        st.write("### 👥 Manage Users")
        
        # 1. User List
        users = db.query(User).all()
        if users:
            user_data = []
            for u in users:
                user_data.append({
                    "ID": u.id,
                    "Name": u.name,
                    "Email": u.email,
                    "Role": u.role,
                    "Joined": u.created_at.date()
                })
            df_users = pd.DataFrame(user_data)
            st.dataframe(df_users, width='content')
            
            # 2. Actions
            c1, c2, c3 = st.columns(3)
            
            # Change Role
            with c1:
                with st.expander("Change User Role"):
                     u_id_role = st.selectbox("Select User ID", [u.id for u in users], key="role_sel")
                     new_role = st.selectbox("New Role", ["student", "admin"], key="role_val")
                     if st.button("Update Role"):
                         u = db.query(User).filter(User.id == u_id_role).first()
                         if u:
                             u.role = new_role
                             db.commit()
                             st.success(f"Updated User {u_id_role} to {new_role}")
                             st.rerun()

            # Delete User
            with c2:
                with st.expander("Delete User (Danger!)"):
                    u_id_del = st.selectbox("Select User ID", [u.id for u in users], key="del_sel")
                    if st.button("Delete User", type="primary"):
                        u = db.query(User).filter(User.id == u_id_del).first()
                        if u:
                            db.delete(u)
                            db.commit()
                            st.warning(f"Deleted User {u_id_del} and all their data.")
                            st.rerun()

            # Add User
            with c3:
                with st.expander("Add New User"):
                    with st.form("admin_add_user"):
                        n_name = st.text_input("Name")
                        n_email = st.text_input("Email")
                        n_pass = st.text_input("Password", type="password")
                        n_role = st.selectbox("Role", ["student", "admin"])
                        if st.form_submit_button("Create User"):
                            if n_name and n_email and n_pass:
                                # Validate inputs
                                if not n_name.strip():
                                    st.error("Name cannot be empty or whitespace")
                                elif not n_email.strip() or '@' not in n_email:
                                    st.error("Please enter a valid email address")
                                elif len(n_pass) < 3:
                                    st.error("Password must be at least 3 characters")
                                else:
                                    hashed = hash_password(n_pass)
                                    new_u = User(name=n_name.strip(), email=n_email.strip(), password_hash=hashed, role=n_role)
                                    db.add(new_u)
                                    db.commit()
                                    st.success("User Created!")
                                    st.rerun()
                            else:
                                st.error("All fields required")

    # ==========================
    # TAB 2: GLOBAL DATA
    # ==========================
    with tab_global:
        st.write("### 🌍 Global Data Manager")
        
        # Select User to Manage
        sel_user_id = st.selectbox("Select User to Manage Data", [u.id for u in users], format_func=lambda x: next((u.name for u in users if u.id == x), "Unknown"))
        
        if sel_user_id:
            st.divider()
            target_user = db.query(User).filter(User.id == sel_user_id).first()
            st.markdown(f"**Managing Data for:** `{target_user.name}` ({target_user.email})")
            
            sub_t1, sub_t2, sub_t3 = st.tabs(["Skills", "Study Sessions", "Goals"])
            
            # -- Global Skills --
            with sub_t1:
                u_skills = target_user.skills
                if u_skills:
                    for s in u_skills:
                         with st.expander(f"{s.name}"):
                             session_count = len(s.sessions)
                             task_count = db.query(StudyTask).filter(StudyTask.skill_id == s.id).count()
                             
                             if session_count > 0 or task_count > 0:
                                 st.caption(f"⚠️ Will remove: {session_count} sessions, {task_count} tasks")
                             
                             if st.button(f"Delete {s.name}", key=f"adm_del_sk_{s.id}"):
                                 # First, nullify skill_id in all linked tasks
                                 linked_tasks = db.query(StudyTask).filter(StudyTask.skill_id == s.id).all()
                                 for task in linked_tasks:
                                     task.skill_id = None
                                 
                                 # Now delete the skill (cascades to sessions)
                                 db.delete(s)
                                 db.commit()
                                 st.success(f"Deleted {s.name}, {session_count} sessions, unlinked {task_count} tasks")
                                 st.rerun()
                else:
                    st.info("User has no skills.")
                
                # Add Skill for User
                if st.button("Add Skill for User", key="adm_add_sk_btn"):
                     # Simple and easy form
                     pass # Implementing full form inside button is tricky, simpler to skip for V1 or use session state
                with st.form("adm_add_sk"):
                    sk_name = st.text_input("New Skill Name")
                    if st.form_submit_button(f"Add Skill for {target_user.name}"):
                        new_s = Skill(user_id=sel_user_id, name=sk_name, description="Added by Admin")
                        db.add(new_s)
                        db.commit()
                        st.success("Added!")
                        st.rerun()

            # -- Global Sessions --
            with sub_t2:
                # List sessions
                sessions = db.query(StudySession).join(Skill).filter(Skill.user_id == sel_user_id).order_by(StudySession.date.desc()).all()
                if sessions:
                    for sess in sessions:
                        st.write(f"- **{sess.date}**: {sess.skill.name} ({sess.hours} hrs)")
                        if st.button("Delete Log", key=f"adm_del_sess_{sess.id}"):
                            db.delete(sess)
                            db.commit()
                            st.rerun()
                else:
                    st.info("No sessions found.")

            # -- Global Goals --
            with sub_t3:
                u_goals = target_user.goals
                if u_goals:
                    for g in u_goals:
                        st.write(f"Goal: **{g.goal_name}** - {g.progress}% ({g.status})")
                        if st.button("Delete Goal", key=f"adm_del_goal_{g.id}"):
                            db.delete(g)
                            db.commit()
                            st.rerun()
                else:
                    st.info("No goals found.")

    # ==========================
    # TAB 3: ANALYTICS
    # ==========================
    with tab_analytics:
        st.write("### 📊 Platform Insights")
        
        # Key Metrics
        tot_u = db.query(User).count()
        tot_hrs = db.query(func.sum(StudySession.hours)).scalar() or 0
        avg_sess = db.query(func.avg(StudySession.hours)).scalar() or 0
        
        k1, k2, k3 = st.columns(3)
        k1.metric("Total Users", tot_u)
        k2.metric("Total Study Hours", f"{tot_hrs:.1f}")
        k3.metric("Avg Session Length", f"{avg_sess:.2f} hrs")
        
        st.divider()
        
        st.write("#### 🏆 Top Students (Most Hours)")
        top_students = db.query(User.name, func.sum(StudySession.hours).label("total_hours"))\
            .select_from(User)\
            .join(Skill)\
            .join(StudySession)\
            .group_by(User.id)\
            .order_by(func.sum(StudySession.hours).desc()).limit(5).all()
            
        if top_students:
            df_top = pd.DataFrame(top_students, columns=["Student", "Total Hours"])
            st.table(df_top)
            
        st.write("#### 💤 Inactive Users (No Sessions)")
        # Find users not in the list of users with sessions
        active_ids = db.query(Skill.user_id).join(StudySession).distinct()
        inactive_users = db.query(User).filter(User.id.not_in(active_ids)).all()
        
        if inactive_users:
            for bad_u in inactive_users:
                st.write(f"- 🔴 {bad_u.name} ({bad_u.email})")
        else:
            st.success("All users are active!")
    
    # ==========================
    # TAB 4: AUDIT LOGS
    # ==========================
    with tab_audit:
        st.write("### 📜 System Audit Logs")
        st.caption("Track all database changes and user actions")
        
        from models import AuditLog
        import json
        
        # Filter options
        col1, col2, col3 = st.columns(3)
        with col1:
            filter_action = st.selectbox("Filter by Action", ["All", "CREATE", "UPDATE", "DELETE"])
        with col2:
            users = db.query(User).all()
            user_options = ["All Users"] + [f"{u.name} (ID: {u.id})" for u in users]
            filter_user = st.selectbox("Filter by User", user_options)
        with col3:
            limit = st.number_input("Show last N records", min_value=10, max_value=500, value=50, step=10)
        
        # Build query
        query = db.query(AuditLog).order_by(AuditLog.timestamp.desc())
        
        if filter_action != "All":
            query = query.filter(AuditLog.action == filter_action)
        
        if filter_user != "All Users":
            user_id = int(filter_user.split("ID: ")[1].rstrip(")"))
            query = query.filter(AuditLog.user_id == user_id)
        
        logs = query.limit(limit).all()
        
        if logs:
            log_data = []
            for log in logs:
                user_name = log.user.name if log.user else "System"
                details_preview = log.details[:50] + "..." if log.details and len(log.details) > 50 else (log.details or "")
                
                log_data.append({
                    "ID": log.id,
                    "User": user_name,
                    "Action": log.action,
                    "Table": log.table_name,
                    "Record ID": log.record_id or "N/A",
                    "Timestamp": log.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                    "Details": details_preview
                })
            
            df_logs = pd.DataFrame(log_data)
            st.dataframe(df_logs, width='content')
            
            # Export Audit Logs
            st.divider()
            csv_audit = df_logs.to_csv(index=False)
            st.download_button(
                label="📥 Export Audit Logs to CSV",
                data=csv_audit,
                file_name=f"audit_logs_{datetime.date.today()}.csv",
                mime="text/csv"
            )
        else:
            st.info("No audit logs found. Logs are created when users perform database operations.")
            st.caption("💡 Note: Audit logging is a premium DBMS feature that tracks accountability!")
