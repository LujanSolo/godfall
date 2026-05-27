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
from app.routes import characters, sessions, timeline, lore, map as map_routes, auth_routes, tavern

# Centralized templates instance — single
# source of truth, filters already attached.
from app.templating import templates
import os
from pathlib import Path
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
from app.auth import get_current_user, get_current_player
from app.database import SessionLocal
from starlette.middleware.base import BaseHTTPMiddleware
import os

class AuthContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        db = SessionLocal()
        try:
            # --- DM AUTH ---
            user = get_current_user(request, db)
            request.state.user = user

            # --- PLAYER AUTH ---
            player = get_current_player(request, db)
            request.state.player = player
        except Exception:
            request.state.user = None
            request.state.player = None
        finally:
            db.close()

        response = await call_next(request)
        return response


app.add_middleware(AuthContextMiddleware)

# --- CREATE DATABASE TABLES ---
Base.metadata.create_all(bind=engine)

# On Railway, symlink the uploads directory
# from the persistent volume into the static
# folder so existing database paths work
DATA_DIR = os.environ.get("DATA_DIR", "")
if DATA_DIR:
    volume_uploads = Path(DATA_DIR) / "uploads"
    static_uploads = Path(__file__).resolve().parent / "static" / "uploads"
    volume_uploads.mkdir(parents=True, exist_ok=True)
    if static_uploads.exists() and not static_uploads.is_symlink():
        import shutil
        shutil.rmtree(static_uploads)
    if not static_uploads.exists():
        static_uploads.symlink_to(volume_uploads)

# --- STATIC FILES ---
app.mount(
    "/static",
    StaticFiles(directory=str(BASE_DIR / "static")),
    name="static"
)
DATA_DIR = os.environ.get("DATA_DIR", "")
if DATA_DIR:
    uploads_path = os.path.join(DATA_DIR, "uploads")
    os.makedirs(uploads_path, exist_ok=True)
    app.mount("/uploads", StaticFiles(directory=uploads_path), name="uploads")

# --- INCLUDE ROUTERS ---
app.include_router(characters.router)
app.include_router(sessions.router)
app.include_router(timeline.router)
app.include_router(lore.router)
app.include_router(map_routes.router)
app.include_router(auth_routes.router)
app.include_router(tavern.router)


# --- HOMEPAGE ROUTE ---
@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse(
        "home.html",
        {
            "request": request,
            "title": "Godfall",
            "tagline": "Five Flames. One fire. Not rekindled, but remembered.",
        }
    )