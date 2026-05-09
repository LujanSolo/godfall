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
from app.routes import characters, sessions, timeline, lore, map as map_routes

# Centralized templates instance — single
# source of truth, filters already attached.
from app.templating import templates

# --- CONFIGURATION ---
BASE_DIR = Path(__file__).resolve().parent

# --- CREATE THE APP ---
app = FastAPI(title="Godfall")

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