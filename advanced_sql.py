import streamlit as st
import pandas as pd
from sqlalchemy import func, text
from models import User, Skill, StudySession, StudyTask, Goal
import plotly.express as px

def render_advanced_sql_page(db):
    """
    Showcase advanced SQL queries to demonstrate DBMS expertise
    """
    st.title("🎓 Advanced SQL Query Showcase")
    st.write("Demonstrating advanced database concepts using real data")
    
    tab1, tab2, tab3, tab4 = st.tabs(["Subqueries", "Window Functions", "CTEs", "Complex Aggregations"])
    
    # ======================
    # TAB 1: SUBQUERIES
    # ======================
    with tab1:
        st.subheader("📊 Subquery Examples")
        
        # Example 1: Students who studied MORE than average
        st.write("### 1. Students Who Studied More Than Average")
        
        avg_hours_subquery = db.query(func.avg(StudySession.hours)).scalar() or 0
        
        above_avg_query = db.query(
            User.name,
            func.sum(StudySession.hours).label('total_hours')
        ).select_from(User)\
         .join(Skill)\
         .join(StudySession)\
         .group_by(User.id)\
         .having(func.sum(StudySession.hours) > avg_hours_subquery)
        
        # Show SQL
        with st.expander("📝 Show SQL Query"):
            st.code(str(above_avg_query.statement.compile(compile_kwargs={"literal_binds": True})), language="sql")
        
        results = above_avg_query.all()
        if results:
            df = pd.DataFrame(results, columns=["Student", "Total Hours"])
            st.dataframe(df, use_container_width=False)
            st.caption(f"📌 Average hours: {avg_hours_subquery:.2f}")
        else:
            st.info("No students found above average")
        
        st.divider()
        
        # Example 2: Users with NO study sessions (NOT IN)
        st.write("### 2. Inactive Users (Using Subquery)")
        
        active_user_ids = db.query(Skill.user_id).join(StudySession).distinct().subquery()
        inactive_query = db.query(User.name, User.email)\
            .filter(User.id.not_in(db.query(active_user_ids)))
        
        with st.expander("📝 Show SQL Query"):
            st.code(str(inactive_query.statement.compile(compile_kwargs={"literal_binds": True})), language="sql")
        
        inactive_results = inactive_query.all()
        if inactive_results:
            df_inactive = pd.DataFrame(inactive_results, columns=["Name", "Email"])
            st.table(df_inactive)
        else:
            st.success("All users are active!")
    
    # ======================
    # TAB 2: WINDOW FUNCTIONS
    # ======================
    with tab2:
        st.subheader("🪟 Window Function Examples")
        
        st.write("### 1. Ranking Users by Study Hours")
        
        # Using raw SQL for window functions (SQLAlchemy ORM doesn't support them well)
        ranking_sql = text("""
            SELECT 
                u.name,
                COALESCE(SUM(ss.hours), 0) as total_hours,
                RANK() OVER (ORDER BY COALESCE(SUM(ss.hours), 0) DESC) as rank_position
            FROM users u
            LEFT JOIN skills sk ON u.id = sk.user_id
            LEFT JOIN study_sessions ss ON sk.id = ss.skill_id
            GROUP BY u.id, u.name
            ORDER BY total_hours DESC
        """)
        
        with st.expander("📝 Show SQL Query"):
            st.code(str(ranking_sql), language="sql")
        
        ranking_results = db.execute(ranking_sql).fetchall()
        if ranking_results:
            df_rank = pd.DataFrame(ranking_results, columns=["Student", "Total Hours", "Rank"])
            st.dataframe(df_rank, use_container_width=False)
        
        st.divider()
        
        st.write("### 2. Running Total of Hours by Date")
        
        running_total_sql = text("""
            SELECT 
                date,
                hours,
                SUM(hours) OVER (ORDER BY date ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) as running_total
            FROM study_sessions
            ORDER BY date
            LIMIT 20
        """)
        
        with st.expander("📝 Show SQL Query"):
            st.code(str(running_total_sql), language="sql")
        
        rt_results = db.execute(running_total_sql).fetchall()
        if rt_results:
            df_rt = pd.DataFrame(rt_results, columns=["Date", "Hours", "Running Total"])
            st.line_chart(df_rt.set_index("Date")["Running Total"])
            st.dataframe(df_rt, use_container_width=False)
    
    # ======================
    # TAB 3: CTEs
    # ======================
    with tab3:
        st.subheader("🔗 Common Table Expressions (CTEs)")
        
        st.write("### 1. Monthly Study Summary with CTE")
        
        cte_sql = text("""
            WITH monthly_stats AS (
                SELECT 
                    DATE_FORMAT(date, '%Y-%m') as month,
                    COUNT(*) as session_count,
                    SUM(hours) as total_hours,
                    AVG(hours) as avg_hours
                FROM study_sessions
                GROUP BY DATE_FORMAT(date, '%Y-%m')
            )
            SELECT 
                month,
                session_count,
                ROUND(total_hours, 1) as total_hours,
                ROUND(avg_hours, 2) as avg_session_length
            FROM monthly_stats
            ORDER BY month DESC
        """)
        
        with st.expander("📝 Show SQL Query"):
            st.code(str(cte_sql), language="sql")
        
        cte_results = db.execute(cte_sql).fetchall()
        if cte_results:
            df_cte = pd.DataFrame(cte_results, columns=["Month", "Sessions", "Total Hours", "Avg Length"])
            st.dataframe(df_cte, use_container_width=False)
            
            # Visualization
            fig = px.bar(df_cte, x="Month", y="Total Hours", title="Monthly Study Hours")
            st.plotly_chart(fig)
    
    # ======================
    # TAB 4: COMPLEX AGGREGATIONS
    # ======================
    with tab4:
        st.subheader("📈 Complex Aggregations")
        
        st.write("### 1. HAVING Clause: Skills with >5 Total Hours")
        
        having_query = db.query(
            Skill.name,
            func.count(StudySession.id).label('session_count'),
            func.sum(StudySession.hours).label('total_hours')
        ).join(StudySession)\
         .group_by(Skill.id)\
         .having(func.sum(StudySession.hours) > 5)
        
        with st.expander("📝 Show SQL Query"):
            st.code(str(having_query.statement.compile(compile_kwargs={"literal_binds": True})), language="sql")
        
        having_results = having_query.all()
        if having_results:
            df_having = pd.DataFrame(having_results, columns=["Skill", "Sessions", "Total Hours"])
            st.dataframe(df_having, use_container_width=False)
        else:
            st.info("No skills with >5 hours yet")
        
        st.divider()
        
        st.write("### 2. Multi-Level Grouping: User -> Skill Breakdown")
        
        breakdown_query = db.query(
            User.name,
            Skill.name.label('skill_name'),
            func.count(StudySession.id).label('sessions'),
            func.sum(StudySession.hours).label('hours')
        ).select_from(User)\
         .join(Skill)\
         .join(StudySession)\
         .group_by(User.id, Skill.id)\
         .order_by(User.name, func.sum(StudySession.hours).desc())
        
        with st.expander("📝 Show SQL Query"):
            st.code(str(breakdown_query.statement.compile(compile_kwargs={"literal_binds": True})), language="sql")
        
        breakdown_results = breakdown_query.all()
        if breakdown_results:
            df_breakdown = pd.DataFrame(breakdown_results, columns=["Student", "Skill", "Sessions", "Hours"])
            st.dataframe(df_breakdown, use_container_width=False)
