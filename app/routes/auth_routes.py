# ============================================
# GODFALL - app/routes/auth_routes.py
# Login and Logout Routes
# ============================================
# Three routes:
#
#   GET  /login   → show the login form
#   POST /login   → process login submission
#   POST /logout  → clear the session and redirect
#
# Login flow:
#   1. User submits email + password
#   2. Server looks up user by email
#   3. Server verifies password against the hash
#   4. If valid, server creates a signed session
#      token and sets it as a cookie
#   5. Browser is redirected to the home page
#      with the cookie now in place
#
# From then on, every request includes the
# cookie, and our get_current_user dependency
# can identify the DM.
# ============================================

from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import Optional

from app.database import get_db
from app.models import User
from app.auth import (
    verify_password,
    create_session_token,
    SESSION_COOKIE_NAME,
)
from app.templating import templates

# --- CREATE THE ROUTER ---
router = APIRouter(tags=["Auth"])


# ============================================
# ROUTE: LOGIN FORM
# GET /login
# ============================================
@router.get("/login")
async def login_form(request: Request, error: Optional[str] = None):
    return templates.TemplateResponse(
        "auth/login.html",
        {
            "request": request,
            "title": "Login — Godfall",
            "error": error,
        }
    )


# ============================================
# ROUTE: PROCESS LOGIN
# POST /login
# ============================================
# Looks up the user, verifies the password,
# and (if successful) sets the session cookie.
#
# Note: we use the same generic error message
# for "user not found" AND "wrong password."
# That's intentional — revealing which one
# failed would let an attacker enumerate
# valid emails by trying random ones and
# noticing which message appears.
#
# Like a stormtrooper checkpoint that just
# says "access denied" instead of "wrong ID
# number" or "ID not in our database" —
# attackers don't get free intel about your
# system from error messages.
# ============================================
@router.post("/login")
async def login_submit(
    request: Request,
    db: Session = Depends(get_db),
    email: str = Form(...),
    password: str = Form(...),
):
    # Normalize the email (strip whitespace, lowercase)
    # so login works regardless of how it was typed.
    email = email.strip().lower()

    # Look up the user
    user = (
        db.query(User)
        .filter(User.email == email)
        .first()
    )

    # Verify password. Note we ALWAYS do the bcrypt
    # check even if the user doesn't exist — this
    # prevents "timing attacks" where an attacker
    # could measure response time to figure out
    # whether an email exists in the database.
    #
    # If user is None, we verify against a dummy
    # hash so the bcrypt operation still happens,
    # taking the same amount of time as a real check.
    if user is None:
        # Dummy bcrypt operation for timing consistency
        verify_password(
            password,
            "$2b$12$" + "x" * 53  # malformed but bcrypt-shaped
        )
        return RedirectResponse(
            url="/login?error=invalid",
            status_code=303
        )

    if not verify_password(password, user.password_hash):
        return RedirectResponse(
            url="/login?error=invalid",
            status_code=303
        )

    # Update last_login_at timestamp
    user.last_login_at = datetime.now(timezone.utc)
    db.commit()

    # Create a session token for this user
    token = create_session_token(user.id)

    # Set the cookie and redirect home
    response = RedirectResponse(url="/", status_code=303)
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        # httponly=True means JavaScript on the page
        # can't read this cookie, only the server can.
        # Defense against XSS attacks that try to
        # steal session cookies.
        httponly=True,
        # samesite="lax" prevents the cookie from
        # being sent with most cross-site requests.
        # Defense against CSRF attacks.
        samesite="lax",
        # max_age in seconds. 30 days here.
        # User stays logged in for a month.
        max_age=60 * 60 * 24 * 30,
        # secure=True would mean "only send over HTTPS"
        # which is correct for production but breaks
        # local development on http://127.0.0.1.
        # Set this to True when deploying.
        secure=False,
    )
    return response


# ============================================
# ROUTE: LOGOUT
# POST /logout
# ============================================
# Just clears the cookie and redirects home.
# We use POST rather than GET because logout
# is an "action" that changes server state
# (kind of). Also prevents accidental logout
# from someone clicking a stale link.
# ============================================
@router.post("/logout")
async def logout():
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie(SESSION_COOKIE_NAME)
    return response