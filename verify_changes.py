import datetime
from database import SessionLocal
from models import User, Skill, StudySession
from sqlalchemy.exc import IntegrityError

def verify_db():
    print("🧪 Starting verification...")
    db = SessionLocal()
    
    # 1. Test User Creation
    user = User(name="Test User", email="test@test.com", password_hash="dummy", role="student")
    db.add(user)
    db.commit()
    print("✅ Created User")

    # 2. Test Skill Creation
    skill = Skill(user_id=user.id, name="DB Testing", description="Testing constraints")
    db.add(skill)
    db.commit()
    print("✅ Created Skill")

    # 3. Test Positive Session (Should Succeed)
    session_ok = StudySession(skill_id=skill.id, date=datetime.date.today(), hours=2.0)
    db.add(session_ok)
    db.commit()
    print("✅ Added Valid Session")

    # 4. Test Negative Session (Should Fail)
    print("👉 Testing Negative Hours Constraint...")
    try:
        session_bad = StudySession(skill_id=skill.id, date=datetime.date.today(), hours=-1.0)
        db.add(session_bad)
        db.commit()
        print("❌ FAILED: Negative hours were allowed!")
    except IntegrityError:
        db.rollback()
        print("✅ SUCCESS: Negative hours were rejected (IntegrityError caught).")
    except Exception as e:
        db.rollback()
        print(f"⚠️ Caught unexpected error: {e}")

    # 5. Test Cascading Delete
    print("👉 Testing Cascading Delete...")
    # Verify we have 1 skill and 1 session
    assert db.query(Skill).count() == 1
    assert db.query(StudySession).count() == 1
    
    # Delete User
    db.delete(user)
    db.commit()
    
    # Check if Skill and Session are gone
    skills_count = db.query(Skill).count()
    sessions_count = db.query(StudySession).count()
    
    if skills_count == 0 and sessions_count == 0:
        print("✅ SUCCESS: Cascading delete worked. Skills and Sessions are gone.")
    else:
        print(f"❌ FAILED: Orphans remaining. Skills: {skills_count}, Sessions: {sessions_count}")

    db.close()

if __name__ == "__main__":
    verify_db()
