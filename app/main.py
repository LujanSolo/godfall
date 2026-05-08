# ============================================
# GODFALL - app/main.py - The Command Center
# ============================================
# This is the heart of the application.
# Everything flows through here — like the
# bridge of a Star Destroyer (except we're
# the good guys).
# ============================================

# --- IMPORTS ---
# Calling our crew to the bridge.

# FastAPI: the framework itself.
# Request: contains info about incoming
#          requests (who's asking, what
#          browser, etc).
# StaticFiles: serves CSS, images, etc.
# Jinja2Templates: connects our HTML templates.
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# pathlib.Path: Python's modern way of working
# with file paths. Instead of messy string
# concatenation like "/app/../templates", Path
# lets you navigate the filesystem like a Jedi
# sensing their surroundings — cleanly and
# reliably across any operating system.
from pathlib import Path

# --- CONFIGURATION ---
# Setting up the ship's systems before launch.

# This figures out where THIS file lives on
# disk, so we can find templates, static files,
# etc. relative to it. No matter where you run
# the project FROM, this always knows where
# the app/ folder IS.
#
# It's like having a nav beacon — wherever you
# are in the galaxy, you can always find home.
BASE_DIR = Path(__file__).resolve().parent

# --- CREATE THE APP ---
# This single line creates the FastAPI
# application — the command center itself.
# Every route, every template, every request
# flows through this object.
#
# title: shows up in the auto-generated API
#        docs (yes, FastAPI gives you free
#        documentation — we'll explore that).
app = FastAPI(title="Godfall")

# --- STATIC FILES ---
# This tells FastAPI: "When someone requests
# a URL starting with /static, serve files
# from the app/static/ folder."
#
# So /static/css/custom.css maps to the actual
# file at app/static/css/custom.css.
#
# Think of it as the supply route — it tells
# the browser where to find CSS, images, and
# other assets.
app.mount(
    "/static",
    StaticFiles(directory=str(BASE_DIR / "static")),
    name="static"
)

# --- TEMPLATES ---
# This creates a Jinja2 template engine
# pointed at our templates/ folder. When a
# route wants to render an HTML page, it asks
# this object: "Hey, find me home.html and
# fill in the blanks with this data."
#
# Like the holotable on the Rebel base —
# you feed it data, it projects something
# everyone can see and understand.
templates = Jinja2Templates(
    directory=str(BASE_DIR / "templates")
)

# --- ROUTES ---
# For now, one simple route to prove the
# command center is online. We'll move this
# to a separate file soon — but seeing it
# work HERE first makes the concept click.
#
# @app.get("/") is a "decorator" — a Python
# feature that says "attach this function to
# this URL path." When someone visits the
# root URL (http://127.0.0.1:8000/), FastAPI
# calls this function.
#
# "request: Request" — FastAPI automatically
# provides the request object, which contains
# everything about the incoming request.
# Jinja2 needs it to render templates.
#
# "async def" — FastAPI is asynchronous by
# default. This means the server can handle
# multiple requests without them blocking
# each other. Like a Jedi multitasking with
# the Force — deflecting blaster bolts while
# also pulling a lightsaber.
@app.get("/")
async def home(request: Request):
    # TemplateResponse says: "Find home.html,
    # plug in these variables, and send the
    # result back to the browser."
    #
    # The dictionary is where we pass data
    # from Python into the HTML template.
    # "request" is REQUIRED by Jinja2 — it
    # always needs the request object.
    #
    # We're also passing in the campaign name
    # and tagline so the template can display
    # them. This is the power of Jinja2 —
    # Python decides WHAT to show, the
    # template decides HOW to show it.
    return templates.TemplateResponse(
        "home.html",
        {
            "request": request,
            "title": "Godfall",
            "tagline": "Five Flames. One fire. Not kindled, but remembered.",
        }
    )