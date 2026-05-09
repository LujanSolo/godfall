# ============================================
# GODFALL - app/main.py - The Command Center
# ============================================

# Load environment variables from .env file
# BEFORE any other imports that might use them.
# This needs to happen first because some
# imported modules (like auth.py) read env
# vars at import time.
from dotenv import load_dotenv
load_dotenv()
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from app.database import engine, Base
from app import models  # noqa: F401  (registers models with Base)
from app.routes import characters, sessions, timeline, lore, map as map_routes, auth_routes

# Centralized templates instance — single
# source of truth, filters already attached.
from app.templating import templates

# --- CONFIGURATION ---
BASE_DIR = Path(__file__).resolve().parent

# --- CREATE THE APP ---
app = FastAPI(title="Godfall")

# ============================================
# AUTH-AWARE TEMPLATE CONTEXT
# ============================================
# We want every template to know whether the
# DM is logged in, without every route having
# to manually pass that variable.
#
# FastAPI's middleware pattern lets us run
# code before AND after each request. Here we
# add the current user to request.state, where
# templates can pick it up via request.state.user.
#
# Like a stormtrooper at the door of every
# room — checks credentials once, attaches a
# clearance badge, and the rest of the room
# can just glance at the badge to know what
# the visitor's allowed to do.
# ============================================
from app.auth import get_current_user
from app.database import SessionLocal
from starlette.middleware.base import BaseHTTPMiddleware


class AuthContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        # Open a database session for this request
        db = SessionLocal()
        try:
            # Use our auth dependency to find the user
            # (returns None if not logged in)
            user = get_current_user(request, db)
            # Stash on request.state where templates
            # can access it via request.state.user
            request.state.user = user
        except Exception:
            request.state.user = None
        finally:
            db.close()

        # Continue to the actual route handler
        response = await call_next(request)
        return response


app.add_middleware(AuthContextMiddleware)

# --- CREATE DATABASE TABLES ---
Base.metadata.create_all(bind=engine)

# --- STATIC FILES ---
app.mount(
    "/static",
    StaticFiles(directory=str(BASE_DIR / "static")),
    name="static"
)

# --- INCLUDE ROUTERS ---
app.include_router(characters.router)
app.include_router(sessions.router)
app.include_router(timeline.router)
app.include_router(lore.router)
app.include_router(map_routes.router)
app.include_router(auth_routes.router)


# --- HOMEPAGE ROUTE ---
@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse(
        "home.html",
        {
            "request": request,
            "title": "Godfall",
            "tagline": "Five Flames. One fire. Not kindled, but remembered.",
        }
    )