import datetime
from database import SessionLocal
from models import User, Skill, StudyTask, StudySession, Topic, Subject, Semester
from sqlalchemy import func

def test_logic():
    print("[TEST] Starting logic verification...")
    db = SessionLocal()
    
    try:
        # 1. Setup - Use existing or create test user
        user = db.query(User).filter(User.email == "test@test.com").first()
        if not user:
            user = User(name="Test User", email="test@test.com", password_hash="dummy", role="student")
            db.add(user)
            db.commit()
            print("[SETUP] Created Test User")
        
        skill = db.query(Skill).filter(Skill.user_id == user.id, Skill.name == "DB Testing").first()
        if not skill:
            skill = Skill(user_id=user.id, name="DB Testing", description="Testing constraints")
            db.add(skill)
            db.commit()
            print("[SETUP] Created Test Skill")

        # 2. Mock Task Completion Logic
        task = StudyTask(user_id=user.id, skill_id=skill.id, task="Test Task Logic", due_date=datetime.date.today(), status="Pending")
        db.add(task)
        db.commit()
        print(f"[ACTION] Created Task: {task.task}")

        # Simulate completion with logging
        new_session = StudySession(
            skill_id=task.skill_id,
            date=datetime.date.today(),
            hours=1.5,
            notes=f"Completed task: {task.task}"
        )
        db.add(new_session)
        task.status = "Completed"
        db.commit()
        print("[ACTION] Simulated Task Completion & Logging")

        # 3. Verify DB State
        t_check = db.query(StudyTask).filter(StudyTask.id == task.id).first()
        s_check = db.query(StudySession).filter(StudySession.skill_id == skill.id, StudySession.notes.contains("Test Task Logic")).first()

        if t_check.status == "Completed" and s_check and s_check.hours == 1.5:
            print("[SUCCESS] Task marked completed and session created correctly!")
        else:
            print(f"[FAILED] State mismatch. Task Status: {t_check.status}, Session found: {s_check is not None}")

        # 4. Cleanup
        db.delete(t_check)
        if s_check: db.delete(s_check)
        db.commit()
        print("[CLEANUP] Cleaned up test data")

    except Exception as e:
        db.rollback()
        print(f"[ERROR] Test failed with error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    test_logic()
