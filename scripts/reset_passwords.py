"""Helper utility to reset passwords for default database users with Python 3.13 bcrypt compatibility."""
import bcrypt
import types
import sys

if not hasattr(bcrypt, "__about__"):
    bcrypt.__about__ = types.ModuleType("__about__")
    bcrypt.__about__.__version__ = getattr(bcrypt, "__version__", "unknown")
_orig_hashpw = bcrypt.hashpw
bcrypt.hashpw = lambda pw, salt: _orig_hashpw(pw[:72] if len(pw) > 72 else pw, salt)

from shared.database.session import SessionLocal
from shared.database.rbac_models import User
from passlib.context import CryptContext

def reset_passwords():
    db = SessionLocal()
    pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
    try:
        users = db.query(User).all()
        for u in users:
            u.hashed_password = pwd_ctx.hash("OrzenVision2026!")
            print(f"Password reset for: {u.email}")
        db.commit()
        print("All database passwords updated successfully to 'OrzenVision2026!'")
    except Exception as exc:
        db.rollback()
        print(f"Error: {exc}")
    finally:
        db.close()

if __name__ == "__main__":
    reset_passwords()
