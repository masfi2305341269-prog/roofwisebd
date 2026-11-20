import os
import sys
import getpass
import argparse
from pathlib import Path

# Ensure backend root directory is in sys.path
backend_dir = Path(__file__).resolve().parent.parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.database.database import SessionLocal
from app.database.models import User
from app.core.security import get_password_hash, validate_password_strength

def create_admin_interactive(email: str = None, password: str = None, full_name: str = None):
    """Securely creates or upgrades an administrator account using Argon2id."""
    email = email or os.getenv("ADMIN_EMAIL")
    if not email:
        email = input("Enter admin email address: ").strip()
    
    if not email or "@" not in email:
        print("[ERROR] A valid email address is required.")
        sys.exit(1)

    password = password or os.getenv("ADMIN_PASSWORD")
    if not password:
        password = getpass.getpass("Enter admin password (min 8 chars, 1 letter, 1 number): ")
        confirm_password = getpass.getpass("Confirm admin password: ")
        if password != confirm_password:
            print("[ERROR] Passwords do not match.")
            sys.exit(1)
            
    is_valid, err_msg = validate_password_strength(password)
    if not is_valid:
        print(f"[ERROR] Invalid password: {err_msg}")
        sys.exit(1)

    full_name = full_name or os.getenv("ADMIN_NAME") or "System Administrator"

    hashed_pw = get_password_hash(password)

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email.lower()).first()
        if user:
            user.role = "admin"
            user.hashed_password = hashed_pw
            user.is_active = True
            if full_name:
                user.full_name = full_name
            db.commit()
            print(f"[SUCCESS] Existing user '{email}' successfully upgraded to Administrator role.")
        else:
            admin_user = User(
                email=email.lower(),
                hashed_password=hashed_pw,
                full_name=full_name,
                role="admin",
                is_active=True
            )
            db.add(admin_user)
            db.commit()
            print(f"[SUCCESS] Administrator user '{email}' created successfully.")
    finally:
        db.close()

def list_admins():
    """Lists existing administrators (emails and statuses only, never passwords)."""
    db = SessionLocal()
    try:
        admins = db.query(User).filter(User.role == "admin").all()
        if not admins:
            print("No administrator accounts found.")
            return
        print(f"{'ID':<6} {'Email':<30} {'Name':<25} {'Active':<8} {'Created At'}")
        print("-" * 85)
        for a in admins:
            print(f"{a.id:<6} {a.email:<30} {a.full_name:<25} {str(a.is_active):<8} {a.created_at}")
    finally:
        db.close()

def main():
    parser = argparse.ArgumentParser(description="RoofwiseBD Secure Administrator Management CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    create_parser = subparsers.add_parser("create-admin", help="Create or upgrade an administrator")
    create_parser.add_argument("--email", help="Administrator email address")
    create_parser.add_argument("--password", help="Administrator password (optional, prompted if omitted)")
    create_parser.add_argument("--name", help="Administrator display name")

    subparsers.add_parser("list-admins", help="List all administrator accounts")

    args = parser.parse_args()

    if args.command == "create-admin":
        create_admin_interactive(email=args.email, password=args.password, full_name=args.name)
    elif args.command == "list-admins":
        list_admins()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
