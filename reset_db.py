from database import engine
from models import Base

from sqlalchemy import text

print("⚠️  Resetting database... This will delete all existing data.")

with engine.connect() as connection:
    connection.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
    connection.commit()

Base.metadata.drop_all(engine)
Base.metadata.create_all(engine)

with engine.connect() as connection:
    connection.execute(text("SET FOREIGN_KEY_CHECKS = 1"))
    connection.commit()

print("✅ Database has been reset and all tables recreated successfully!")
