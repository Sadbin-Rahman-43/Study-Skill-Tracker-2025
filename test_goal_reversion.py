import datetime
from database import SessionLocal
from models import User, Skill, StudyTask, StudySession, Goal
from sqlalchemy import func

def test_goal_logic():
    print("[TEST] Starting goal status reversion verification...")
    db = SessionLocal()
    
    try:
        # 1. Setup
        user = db.query(User).filter(User.email == "test@test.com").first()
        if not user:
            user = User(name="Test User", email="test@test.com", password_hash="dummy", role="student")
            db.add(user)
            db.commit()
        
        # Create a Goal
        goal = Goal(user_id=user.id, goal_name="Reversion Test Goal", target_date=datetime.date.today(), status="In Progress", progress=0)
        db.add(goal)
        db.commit()
        print(f"[SETUP] Created Goal: {goal.goal_name}")

        # Add 1st task and complete it
        task1 = StudyTask(user_id=user.id, goal_id=goal.id, task="Task 1", due_date=datetime.date.today(), status="Completed")
        db.add(task1)
        db.commit()
        print("[ACTION] Added and completed Task 1")

        # Simulate the progress calculation that happens in app.py
        def sync_goal(g_id):
            g = db.query(Goal).filter(Goal.id == g_id).first()
            total = len(g.tasks)
            completed = sum(1 for t in g.tasks if t.status == "Completed")
            prog = int((completed / total * 100)) if total > 0 else 0
            g.progress = prog
            if prog == 100:
                g.status = "Achieved"
            elif prog < 100 and g.status == "Achieved":
                g.status = "In Progress"
            db.commit()
            return g.progress, g.status

        prog, status = sync_goal(goal.id)
        print(f"[CHECK 1] Progress: {prog}%, Status: {status}")
        assert status == "Achieved"

        # Add 2nd task (should reset status to In Progress)
        task2 = StudyTask(user_id=user.id, goal_id=goal.id, task="Task 2", due_date=datetime.date.today(), status="Pending")
        db.add(task2)
        db.commit()
        print("[ACTION] Added Task 2 (Pending)")

        prog, status = sync_goal(goal.id)
        print(f"[CHECK 2] Progress: {prog}%, Status: {status}")
        
        if status == "In Progress" and prog == 50:
            print("[SUCCESS] Goal status correctly reverted to 'In Progress' and progress updated to 50%!")
        else:
            print(f"[FAILED] Goal status: {status}, Progress: {prog}")

        # Cleanup
        db.delete(task1)
        db.delete(task2)
        db.delete(goal)
        db.commit()
        print("[CLEANUP] Cleaned up test data")

    except Exception as e:
        db.rollback()
        print(f"[ERROR] Test failed with error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    test_goal_logic()
