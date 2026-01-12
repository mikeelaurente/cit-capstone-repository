
# ------------------------------
# Seed default users (Admin & Staff)
# ------------------------------
from db import SessionLocal
from models import User

def seed_default_users():
    db = SessionLocal()
    try:
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        def get_password_hash(password: str):
            return pwd_context.hash(password)

        if not db.query(User).filter(User.email == "admin@cit.edu").first():
            admin_user = User(
                email="admin@cit.edu",
                password=get_password_hash("admin123"),
                role="Admin",
            )
            db.add(admin_user)

        if not db.query(User).filter(User.email == "staff@cit.edu").first():
            staff_user = User(
                email="staff@cit.edu",
                password=get_password_hash("staff123"),
                role="Staff",
            )
            db.add(staff_user)

        db.commit()
    finally:
        if db:
            db.close()

if __name__ == '__main__':
    seed_default_users()