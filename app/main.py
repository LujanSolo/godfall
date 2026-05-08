# ============================================
# GODFALL - app/main.py - The Command Center
# ============================================
# This is the heart of the application.
# Everything flows through here — like the
# bridge of a Star Destroyer (except we're
# the good guys).
# ============================================

# --- IMPORTS ---
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path

# --- NEW: Database & Routes Imports ---
# Bringing in our database engine, the Base
# class that all models inherit from, and the
# character router we just built.
#
# Importing models is what registers them
# with Base. Without this import, Base.metadata
# wouldn't know about Character or
# CharacterImage, and the tables wouldn't get
# created. It's like making sure the crew
# actually shows up to the briefing — present
# and accounted for.
from app.database import engine, Base
from app import models  # noqa: F401  (registers models with Base)
from app.routes import characters

# --- CONFIGURATION ---
BASE_DIR = Path(__file__).resolve().parent

# --- CREATE THE APP ---
app = FastAPI(title="Godfall")

# --- NEW: CREATE DATABASE TABLES ---
# Base.metadata.create_all() looks at every
# model that inherits from Base, then creates
# any tables that don't already exist in the
# database.
#
# Crucially: it does NOT alter existing tables.
# If you change a model, this won't update the
# table — that's where Alembic migrations come
# in (Phase 2.5 territory).
#
# But for first-time setup, this is perfect.
# Like the first power-up of a new starship —
# all systems initialize, ready for service.
Base.metadata.create_all(bind=engine)

# --- STATIC FILES ---
app.mount(
    "/static",
    StaticFiles(directory=str(BASE_DIR / "static")),
    name="static"
)

# --- TEMPLATES ---
templates = Jinja2Templates(
    directory=str(BASE_DIR / "templates")
)

# --- NEW: REGISTER THE CHARACTER ROUTER ---
# This single line plugs in every route from
# routes/characters.py. Now /characters,
# /characters/new, /characters/{id}, etc. all
# work — without us having to define them
# here.
#
# Like docking the character module onto the
# main ship. Once locked in, all its systems
# come online instantly.
app.include_router(characters.router)

# --- HOMEPAGE ROUTE ---
# (unchanged)
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