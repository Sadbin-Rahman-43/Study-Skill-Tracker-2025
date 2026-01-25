from database_utils import get_db
from models import User


def promote_to_admin():
    print("--- Admin Promotion Tool ---")
    
    with get_db() as db:
        users = db.query(User).all()
        print(f"Found {len(users)} users:")
        for u in users:
            print(f"- {u.name} ({u.email}) [{u.role}]")
            
    email = input("\nEnter email of user to promote: ")
    
    with get_db() as db:
        user = db.query(User).filter(User.email == email).first()
        if user:
            user.role = "admin"
            db.commit()
            print(f"✅ Success! {user.name} ({user.email}) is now an ADMIN.")
        else:
            print(f"❌ User with email '{email}' not found.")

if __name__ == "__main__":
    promote_to_admin()
