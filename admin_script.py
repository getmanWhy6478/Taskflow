import argparse
from app.database import SessionLocal
from app.models import User
from sqlalchemy import or_, select

def main():
    parser = argparse.ArgumentParser(description="Назначить пользователя администратором")
    parser.add_argument("email_or_username", help="Email или логин пользователя")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        user = db.scalar(select(User).where(or_(User.email == args.email_or_username, User.username == args.email_or_username)))
        if not user:
            print(f"Пользователь {args.email_or_username} не найден")
            return
        user.is_admin = True
        db.commit()
        db.refresh(user)
        print(f"Пользователь {args.email_or_username} теперь администратор")
    finally:
        db.close()

if __name__ == "__main__":
    main()