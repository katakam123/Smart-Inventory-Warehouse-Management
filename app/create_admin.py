from app.database import SessionLocal
from app.auth.jwt import hash_password
from app.models.user import User


def create_admin():

    db = SessionLocal()

    try:

        existing_admin = db.query(User).filter(
            User.username == "admin"
        ).first()

        if existing_admin:

            print("Admin already exists")
            return

        admin = User(
            username="admin",
            email="admin@example.com",
            hashed_password=hash_password(
                "Admin@123"
            ),
            role="Admin",
            is_active=True
        )

        db.add(admin)
        db.commit()

        print("Admin created successfully")
        print("Username: admin")
        print("Password: Admin@123")

    finally:

        db.close()


if __name__ == "__main__":
    create_admin()