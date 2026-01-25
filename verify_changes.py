import datetime
from database import SessionLocal
from models import User, Skill, StudySession
from sqlalchemy.exc import IntegrityError

def verify_db():
    print("[TEST] Starting verification...")
    db = SessionLocal()
    
    # 1. Test User Creation
    user = db.query(User).filter(User.email == "test@test.com").first()
    if not user:
        user = User(name="Test User", email="test@test.com", password_hash="dummy", role="student")
        db.add(user)
        db.commit()
    print("[SUCCESS] Found or Created User")

    # 2. Test Skill Creation
    skill = Skill(user_id=user.id, name="DB Testing", description="Testing constraints")
    db.add(skill)
    db.commit()
    print("[SUCCESS] Created Skill")

    # 3. Test Positive Session (Should Succeed)
    session_ok = StudySession(skill_id=skill.id, date=datetime.date.today(), hours=2.0)
    db.add(session_ok)
    db.commit()
    print("[SUCCESS] Added Valid Session")

    # 4. Test Negative Session (Should Fail)
    print("[ACTION] Testing Negative Hours Constraint...")
    try:
        session_bad = StudySession(skill_id=skill.id, date=datetime.date.today(), hours=-1.0)
        db.add(session_bad)
        db.commit()
        print("[FAILED] FAILED: Negative hours were allowed!")
    except IntegrityError:
        db.rollback()
        print("[SUCCESS] SUCCESS: Negative hours were rejected (IntegrityError caught).")
    except Exception as e:
        db.rollback()
        print(f"[ERROR] Caught unexpected error: {e}")

    # 5. Test Cascading Delete (Clean up this test only)
    print("[ACTION] Cleaning up verification data...")
    db.delete(skill) # Cascades to session
    db.commit()
    
    print("[SUCCESS] Verification complete.")
    db.close()

if __name__ == "__main__":
    verify_db()
