"""
Give (or remove) admin access for an existing account.

Usage:  python -m backend.make_admin you@example.com
        python -m backend.make_admin you@example.com --remove
"""
import sys

from backend.init_db import initialize_database
from backend.database import SessionLocal
from backend.models import User


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    initialize_database()
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == sys.argv[1].strip().lower()).first()
        if not user:
            print(f"No account found for {sys.argv[1]}")
            sys.exit(1)
        user.is_admin = 0 if "--remove" in sys.argv else 1
        db.commit()
        print(f"{user.email} is {'now' if user.is_admin else 'no longer'} an admin.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
