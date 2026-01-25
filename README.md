# 📚 Study & Skill Management System

A comprehensive web-based application for tracking study sessions, managing academic goals, and monitoring skill development. Built with **Streamlit** and **MySQL**, featuring advanced SQL queries, real-time analytics, and automated task completion prompts.

---

## ✨ Features

### 🎯 Core Functionality
- **User Authentication** - Secure registration and login with role-based access (Admin/Student)
- **Skill Management** - Create, edit, and track study skills with session history
- **Study Session Logging** - Record study hours with notes and automatic validation
- **Task Management** - Create tasks with due dates, link to skills and goals
- **Goal Tracking** - Set long-term goals with auto-calculated progress from linked tasks
- **Academic Tracker** - Organize studies by Semesters → Subjects → Topics

### 🚀 Advanced Features
- **Automated Completion Prompts** - Automatically asks for study hours when marking tasks/topics complete
- **Dynamic Goal Status** - Goals automatically revert from "Achieved" to "In Progress" when new tasks are added
- **Visual Feedback System** - Toast notifications for all user actions
- **Study & Activity Trends** - Dual-metric analytics showing both hours studied and tasks completed
- **Advanced SQL Showcase** - Demonstrates subqueries, window functions, CTEs, and complex aggregations
- **Audit Logging** - Complete system accountability with detailed operation logs
- **Admin Panel** - User management, system statistics, and audit log viewing

### 📊 Analytics & Reporting
- Real-time dashboard with today's metrics
- Interactive Plotly charts (Pie, Bar, Line)
- Task completion rates
- Goal progress visualization
- PDF report generation
- SQL query display for educational purposes

---

## 🛠️ Tech Stack

- **Frontend**: Streamlit
- **Backend**: Python 3.11+
- **Database**: MySQL 8.0+
- **ORM**: SQLAlchemy
- **Visualization**: Plotly Express
- **PDF Generation**: ReportLab

---

## 📋 Prerequisites

- Python 3.11 or higher
- MySQL Server 8.0 or higher
- pip (Python package manager)

---

## 🚀 Installation

### 1. Clone the Repository
```bash
git clone https://github.com/Sadbin-Rahman-43/Study-Skill-Tracker-2025.git
cd Study-Skill-Tracker-2025
```

### 2. Create Virtual Environment
```bash
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac
```

### 3. Install Dependencies
```bash
pip install streamlit sqlalchemy mysql-connector-python pandas plotly reportlab
```

### 4. Configure Database

Create a `.streamlit/secrets.toml` file:
```toml
[mysql]
host = "localhost"
port = 3306
user = "your_mysql_username"
password = "your_mysql_password"
database = "study_tracker"
```

### 5. Initialize Database
```bash
# The database and tables will be created automatically on first run
python app.py
```

---

## 🎮 Usage

### Start the Application
```bash
streamlit run app.py
```

The application will open in your browser at `http://localhost:8501`

### First-Time Setup
1. **Register** a new account
2. **Create Skills** (e.g., Python, Mathematics, Database Systems)
3. **Set Goals** (e.g., "Complete DBMS Course")
4. **Add Tasks** and link them to skills and goals
5. **Log Study Sessions** or mark tasks complete to auto-log

### Making an Admin User
```bash
python make_admin.py
```
Enter the email of the user you want to promote to admin.

---

## 📁 Project Structure

```
Study-Skill-Tracker-2025/
├── app.py                          # Main Streamlit application
├── models.py                       # SQLAlchemy database models
├── auth.py                         # Authentication logic
├── database.py                     # Database connection
├── database_utils.py               # Database utilities
├── admin_panel.py                  # Admin panel functionality
├── advanced_sql.py                 # Advanced SQL demonstrations
├── audit_utils.py                  # Audit logging utilities
├── verify_changes.py               # Database verification script
├── make_admin.py                   # Admin promotion utility
├── reset_db.py                     # Database reset utility
├── sql_technical_documentation.txt # SQL implementation details
├── system_flowchart.md             # Application flow diagram
├── database_schema.md              # Database schema documentation
└── .streamlit/
    └── secrets.toml                # Database credentials (not in repo)
```

---

## 🎯 Key Features Explained

### Automated Task Completion
When you mark a task or topic as "Done", the system:
1. Prompts you to log study hours and notes
2. Creates a study session linked to the appropriate skill
3. Marks the task/topic as completed
4. Updates goal progress automatically
5. Shows a success notification

### Dynamic Goal Management
- Goals calculate progress from linked tasks
- Progress = (Completed Tasks / Total Tasks) × 100
- Status automatically changes:
  - 100% → "Achieved"
  - <100% → "In Progress"
- You can add tasks to "Achieved" goals (status reverts automatically)

### Study Trend Analytics
The Analytics dashboard shows:
- **Hours Studied** - Line chart of daily study time
- **Tasks Completed** - Count of completed tasks per day
- **Combined View** - Dual-metric trend for comprehensive productivity tracking

---

## 🔒 Security Features

- Password hashing with bcrypt
- Role-based access control (Admin/Student)
- SQL injection prevention via SQLAlchemy ORM
- Session state management
- Audit logging for accountability

---

## 📊 Database Schema

The system uses 9 tables:
- `users` - User accounts and authentication
- `skills` - Study subjects/skills
- `study_sessions` - Time tracking records
- `study_tasks` - To-do items
- `goals` - Long-term objectives
- `semesters` - Academic periods
- `subjects` - Courses within semesters
- `topics` - Study topics within subjects
- `audit_logs` - System operation logs

See `database_schema.md` for the complete ER diagram.

---

## 🧪 Testing

Run the verification script to test database constraints:
```bash
python verify_changes.py
```

---

## 📝 SQL Features Demonstrated

This project showcases advanced SQL concepts:
- **Subqueries** - Finding users above average study time
- **Window Functions** - Ranking users, running totals
- **CTEs** - Monthly study summaries
- **Complex Aggregations** - GROUP BY with HAVING clauses
- **Joins** - Multi-table queries
- **Indexes** - Performance optimization
- **Constraints** - Data integrity (CHECK, FOREIGN KEY, UNIQUE)
- **Cascading Deletes** - Referential integrity

---

## 🤝 Contributing

This is an academic project for database management coursework. Contributions are welcome for educational purposes.

---

## 👥 Authors

- **Sadbin Rahman** - [GitHub](https://github.com/Sadbin-Rahman-43)
- **Hasan Imam Bappi** - [GitHub](https://github.com/HasanImamB)
- **Mirza Hamid Al Wasi** - [GitHub](https://github.com/Hamid-Al-Wasi)
- **Alvir Shahriar** - [GitHub](https://github.com/Alvirwebd)

---

## 📄 License

This project is created for academic purposes as part of a Database Management Systems course.

---

## 🙏 Acknowledgments

- Streamlit for the amazing web framework
- SQLAlchemy for robust ORM capabilities
- Plotly for interactive visualizations
- Course instructors for project guidance

---

## 📞 Support

For issues or questions, please open an issue on the GitHub repository.

---

**Built with ❤️ for learning Database Management Systems**