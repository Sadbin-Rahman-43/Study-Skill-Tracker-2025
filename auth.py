import bcrypt
from database import SessionLocal
from models import User

# --------------------
# PASSWORD HELPERS
# --------------------
def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def check_password(password, hashed):
    return bcrypt.checkpw(password.encode(), hashed.encode())


# --------------------
# REGISTER
# --------------------
def register_user(name, email, password):
    db = SessionLocal()

    if db.query(User).filter(User.email == email).first():
        db.close()
        return False, "Email already registered"

    role = "admin" if email == "admin@gmail.com" else "student"

    user = User(
        name=name,
        email=email,
        password_hash=hash_password(password),
        role=role
    )

    db.add(user)
    db.commit()
    db.close()

    return True, "Registration successful"


# --------------------
# LOGIN
# --------------------
def login_user(email, password):
    db = SessionLocal()
    user = db.query(User).filter(User.email == email).first()
    db.close()

    if user and check_password(password, user.password_hash):
        return True, user.name, user.role, user.id

    return False, None, "Invalid email or password", None
