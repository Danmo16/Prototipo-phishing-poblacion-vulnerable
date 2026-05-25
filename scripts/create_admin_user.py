# scripts/create_admin_user.py
from __future__ import annotations

import sys
import argparse
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy.orm import Session

from core.db.session import SessionLocal
from core.domain.models import User
from core.security.jwt import get_password_hash


def parse_args():
    parser = argparse.ArgumentParser(description="Crear usuario administrador")
    parser.add_argument("--username", required=True)
    parser.add_argument("--email", required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument("--full-name", default="Admin")
    return parser.parse_args()


def main():
    args = parse_args()
    db: Session = SessionLocal()

    try:
        existing_user = db.query(User).filter(User.username == args.username).first()
        if existing_user:
            print("Ya existe un usuario con ese username.")
            return

        existing_email = db.query(User).filter(User.email == args.email).first()
        if existing_email:
            print("Ya existe un usuario con ese email.")
            return

        user = User(
            username=args.username,
            email=args.email,
            full_name=args.full_name,
            password_hash=get_password_hash(args.password),
            role="admin",
            is_active=True,
        )
        db.add(user)
        db.commit()
        print(f"Usuario admin creado correctamente: {args.username}")
    finally:
        db.close()


if __name__ == "__main__":
    main()