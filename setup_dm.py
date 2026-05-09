# ============================================
# GODFALL - setup_dm.py
# ============================================
# Run this ONCE to create the initial DM user.
# After it runs successfully, you can log in
# at /login with the email and password you
# set here.
#
# Usage:
#   python setup_dm.py
#
# It'll prompt you interactively for the
# email and password. Won't echo the password
# to the terminal as you type it.
#
# Run it again later if you ever need to
# update the DM's password — it'll detect the
# existing user and offer to reset it rather
# than create a duplicate.
# ============================================

# Load environment variables first
from dotenv import load_dotenv
load_dotenv()

import getpass
from app.database import SessionLocal, engine, Base
from app import models  # registers models with Base
from app.models import User
from app.auth import hash_password


def main():
    # Make sure the database and tables exist
    Base.metadata.create_all(bind=engine)

    # Open a database session
    db = SessionLocal()

    try:
        # Check if a DM already exists
        existing_dm = db.query(User).filter(User.role == "dm").first()

        if existing_dm:
            print(f"\nA DM account already exists: {existing_dm.email}")
            response = input("Reset the password? [y/N]: ").strip().lower()
            if response != "y":
                print("Cancelled. No changes made.")
                return

            # Update existing user's password
            print("\nEnter the new password for the DM.")
            password = getpass.getpass("New password: ")
            confirm = getpass.getpass("Confirm password: ")

            if password != confirm:
                print("\nPasswords don't match. Try again.")
                return

            if len(password) < 8:
                print("\nPassword must be at least 8 characters.")
                return

            existing_dm.password_hash = hash_password(password)
            db.commit()
            print(f"\n✓ Password updated for {existing_dm.email}")
            print("  You can now log in at http://127.0.0.1:8000/login")
            return

        # No DM yet — create one
        print("\n=== GODFALL DM Setup ===")
        print("Creating the initial DM user.\n")

        email = input("Email: ").strip()
        if not email or "@" not in email:
            print("That doesn't look like a valid email address.")
            return

        password = getpass.getpass("Password (min 8 chars): ")
        confirm = getpass.getpass("Confirm password: ")

        if password != confirm:
            print("\nPasswords don't match. Try again.")
            return

        if len(password) < 8:
            print("\nPassword must be at least 8 characters.")
            return

        # Create the user
        new_dm = User(
            email=email,
            password_hash=hash_password(password),
            role="dm",
        )
        db.add(new_dm)
        db.commit()

        print(f"\n✓ DM account created: {email}")
        print("  You can now log in at http://127.0.0.1:8000/login")

    finally:
        db.close()


if __name__ == "__main__":
    main()