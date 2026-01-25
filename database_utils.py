from contextlib import contextmanager
from database import SessionLocal


@contextmanager
def get_db():
    """
    Context manager to ensure database sessions are properly closed.
    
    Usage:
        with get_db() as db:
            users = db.query(User).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
