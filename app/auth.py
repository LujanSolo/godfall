# ============================================
# GODFALL - app/auth.py
# The Authentication Core
# ============================================
# All the cryptographic and session handling
# logic for the auth system lives here.
#
# Three core responsibilities:
#
#   1. Hash and verify passwords (bcrypt)
#   2. Sign and verify session tokens
#      (itsdangerous)
#   3. Provide FastAPI dependencies so
#      routes can ask "is the DM logged in?"
#      and "require the DM or 401"
#
# Like the credentials office on a Star
# Destroyer — issues IDs, verifies them at
# checkpoints, and tells stormtroopers
# whether to let someone through.
# ============================================

import os
from datetime import datetime, timezone
from typing import Optional

import bcrypt
from itsdangerous import URLSafeSerializer, BadSignature
from fastapi import Request, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User


# ============================================
# CONFIGURATION
# ============================================
# The SECRET_KEY signs session cookies. It
# MUST be kept secret and MUST be the same
# value across server restarts (otherwise
# everyone gets logged out every time the
# server restarts).
#
# In development, we read from an environment
# variable with a fallback default. In real
# production, you'd ALWAYS set this via env
# var with a long random value.
#
# We'll create a .env file in step 4 to
# manage this properly.
# ============================================
SECRET_KEY = os.environ.get(
    "GODFALL_SECRET_KEY",
    "dev-only-change-me-in-production-please-and-thank-you"
)

# Cookie configuration
SESSION_COOKIE_NAME = "godfall_session"

# Serializer that signs the cookie value.
# "salt" is just a namespace for this
# particular use of the secret — keeps signed
# cookies for different purposes from being
# interchangeable.
serializer = URLSafeSerializer(SECRET_KEY, salt="godfall-session")


# ============================================
# PASSWORD HASHING
# ============================================
# bcrypt is the gold standard for password
# hashing. It's deliberately slow (which is
# good — makes brute-force attacks expensive)
# and includes built-in salting (which makes
# rainbow-table attacks impossible).
# ============================================

def hash_password(password: str) -> str:
    """
    Convert a plain-text password into a
    secure bcrypt hash. Used when creating or
    updating the DM's password.
    """
    # bcrypt expects bytes, not strings.
    # The .encode() turns "hunter2" into b"hunter2".
    password_bytes = password.encode("utf-8")

    # gensalt() generates a random salt automatically
    # and includes it in the resulting hash, so we
    # don't need to store it separately.
    hashed = bcrypt.hashpw(password_bytes, bcrypt.gensalt())

    # Convert back to string for storage in the database
    return hashed.decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """
    Check whether a plain-text password matches
    a stored bcrypt hash. Used during login.

    Returns True if the password is correct,
    False otherwise. Never raises — even if
    the hash is malformed, just returns False.
    """
    try:
        return bcrypt.checkpw(
            password.encode("utf-8"),
            password_hash.encode("utf-8")
        )
    except (ValueError, TypeError):
        return False


# ============================================
# SESSION HANDLING
# ============================================
# When the DM logs in, we create a signed
# token containing their user ID and stash it
# in a cookie. On each subsequent request, we
# read the cookie, verify the signature, and
# look up the user.
#
# Signed cookies are tamper-evident: if the
# user tries to change the cookie value, the
# signature won't match and we reject it.
# ============================================

def create_session_token(user_id: int) -> str:
    """
    Create a signed session token for a user.
    The token contains just the user ID, which
    we use to look up the user on each request.
    """
    return serializer.dumps({"user_id": user_id})


def decode_session_token(token: str) -> Optional[int]:
    """
    Verify and decode a session token, returning
    the user ID. Returns None if the token is
    invalid, tampered with, or malformed.
    """
    try:
        data = serializer.loads(token)
        return data.get("user_id")
    except BadSignature:
        return None
    except Exception:
        return None


# ============================================
# FASTAPI DEPENDENCIES
# ============================================
# These functions plug into FastAPI routes via
# Depends() to provide auth-aware behavior.
#
# Two flavors:
#
#   get_current_user — returns the User if
#     logged in, or None. Routes use this
#     when they want to KNOW about auth status
#     but allow both logged-in and logged-out
#     visitors (like list views that show
#     extra buttons to the DM).
#
#   require_dm — returns the User if the
#     DM is logged in, or raises 401 otherwise.
#     Routes use this to BLOCK access from
#     anyone who isn't the DM (like delete
#     routes).
# ============================================

def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
) -> Optional[User]:
    """
    Look at the request's session cookie and,
    if it's valid, return the corresponding
    User. Returns None if no cookie, invalid
    cookie, or user not found.

    This dependency NEVER raises — it just
    returns None when there's no logged-in
    user. Routes that want to gracefully
    handle both states use this.
    """
    # Get the cookie from the request
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if not token:
        return None

    # Decode and verify
    user_id = decode_session_token(token)
    if user_id is None:
        return None

    # Look up the user in the database
    user = db.query(User).filter(User.id == user_id).first()
    return user


def require_dm(
    user: Optional[User] = Depends(get_current_user),
) -> User:
    """
    Stricter version of get_current_user that
    raises 401 if no DM is logged in. Use this
    on any route that should be DM-only.

    The check is "any logged-in user with role
    'dm'", which today means "the only user."
    Future-proofed for if we ever add other
    roles.
    """
    if user is None or user.role != "dm":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="DM access required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user