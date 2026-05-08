# ============================================
# GODFALL - app/routes/characters.py
# Mission Control for Characters
# ============================================
# Every route related to characters lives
# here — viewing, creating, editing, deleting,
# and uploading images.
#
# This file uses FastAPI's APIRouter, which
# lets us organize routes into separate files
# instead of cramming everything into main.py.
# Like assigning different officers to
# different bridge stations — everyone has
# their own scope of responsibility.
# ============================================

# --- IMPORTS ---

# APIRouter: a mini-app that holds routes.
# We define routes here, then "include" this
# router in main.py. Modular, clean, scalable.
#
# Request: the incoming request object
# (browser info, URL, etc).
#
# Depends: FastAPI's dependency injection.
# When a route says Depends(get_db), FastAPI
# automatically calls get_db() and hands the
# result to the route function. Like a supply
# droid that brings you exactly what you
# requested, no questions asked.
#
# Form: tells FastAPI "this parameter comes
# from an HTML form submission, not the URL."
#
# UploadFile: represents a file the user is
# uploading through a form.
#
# File: marker that tells FastAPI "this
# parameter is an uploaded file."
from fastapi import (
    APIRouter,
    Request,
    Depends,
    Form,
    UploadFile,
    File,
)

# RedirectResponse: sends the browser to a
# different URL. After creating a character,
# we redirect to their dossier page instead
# of showing a blank "success" screen.
#
# HTMLResponse: for sending raw HTML back.
# We won't use it much, but it's good to have.
from fastapi.responses import RedirectResponse, HTMLResponse

from app.templating import templates

# Session: type hint for the database session.
# This tells Python (and your code editor)
# what type of object get_db() returns.
from sqlalchemy.orm import Session

# Path and shutil: file system tools.
# Path for building paths, shutil for file
# operations (we'll use it for saving uploads).
from pathlib import Path
import shutil
import uuid

# Our own modules:
# get_db: the database session generator.
# Character, CharacterImage: our data models.
from app.database import get_db
from app.models import Character, CharacterImage

# --- CONFIGURATION ---

# Same BASE_DIR / templates pattern as main.py.
BASE_DIR = Path(__file__).resolve().parent.parent
from app.templating import templates

# Where uploaded character images will be
# stored on disk. We put them in static/ so
# they're servable as URLs.
UPLOAD_DIR = BASE_DIR / "static" / "uploads" / "characters"

# Create the upload directory if it doesn't
# exist yet. parents=True creates any missing
# parent folders too. exist_ok=True means
# "don't crash if it already exists."
#
# Like telling the crew: "Make sure cargo
# bay 7 is set up. If it's already set up,
# carry on."
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# --- CREATE THE ROUTER ---
# prefix="/characters" means every route in
# this file automatically starts with
# /characters. So @router.get("/") actually
# maps to /characters/.
#
# tags=["Characters"] groups these routes
# together in FastAPI's auto-generated docs.
router = APIRouter(
    prefix="/characters",
    tags=["Characters"],
)


# ============================================
# ROUTE: LIST ALL CHARACTERS
# GET /characters
# ============================================
# The roster view — shows a card grid of all
# party members. This is the first thing
# players see when they click "Characters"
# in the nav.
#
# New concept: db.query(Character).all()
# This is SQLAlchemy's way of saying
# "SELECT * FROM characters" in SQL.
# The ORM translates Python into SQL for you.
# Protocol droid doing its job.
# ============================================
@router.get("/")
async def character_list(
    request: Request,
    db: Session = Depends(get_db)
):
    # Query all characters from the database,
    # ordered by name alphabetically.
    # .order_by() is like adding
    # "ORDER BY name" in SQL.
    characters = (
        db.query(Character)
        .order_by(Character.name)
        .all()
    )

    return templates.TemplateResponse(
        "characters/list.html",
        {
            "request": request,
            "title": "The Roster — Godfall",
            "characters": characters,
        }
    )


# ============================================
# ROUTE: NEW CHARACTER FORM
# GET /characters/new
# ============================================
# Displays the empty form for adding a new
# character to the roster.
#
# IMPORTANT: This route MUST be defined
# BEFORE the /characters/{id} route below.
# Why? Because FastAPI matches routes in
# order. If {id} came first, FastAPI would
# see /characters/new and think "new" is an
# id, then crash trying to convert "new" to
# an integer.
#
# It's like checkpoint security — the specific
# "VIP entrance" (named routes) must come
# before the general "all visitors" gate
# (parameter routes), or VIPs get stuck in
# the wrong line.
# ============================================
@router.get("/new")
async def character_new_form(request: Request):
    return templates.TemplateResponse(
        "characters/form.html",
        {
            "request": request,
            "title": "New Character — Godfall",
            "character": None,
            "editing": False,
        }
    )


# ============================================
# ROUTE: CREATE NEW CHARACTER
# POST /characters/new
# ============================================
# Processes the submitted form and saves the
# new character to the database.
#
# New concepts:
#
# Form(...) parameters: Each form field maps
# to a parameter in this function. FastAPI
# extracts them from the submitted form data.
# The "..." means "required" — if the field
# is missing, FastAPI returns an error.
# Form(None) means "optional."
#
# db.add(): stages a new record for saving.
# db.commit(): actually writes it to the
# database. Like drafting a message (add)
# and then hitting send (commit).
#
# db.refresh(): after committing, this pulls
# the record back from the database with its
# newly assigned id. Without this, character.id
# would be None because the database hadn't
# assigned it yet when we created the object.
# ============================================
@router.post("/new")
async def character_create(
    request: Request,
    db: Session = Depends(get_db),
    name: str = Form(...),
    player_name: str = Form(...),
    race: str = Form(...),
    character_class: str = Form(...),
    level: int = Form(1),
    age: str = Form(None),
    one_liner: str = Form(None),
    backstory: str = Form(None),
    top_magic_items: str = Form(None),
    notable_traits: str = Form(None),
    pets_companions: str = Form(None),
    status: str = Form("Active"),
):
    # Create a new Character object from the
    # form data. This doesn't touch the
    # database yet — it's just a Python object.
    character = Character(
        name=name,
        player_name=player_name,
        race=race,
        character_class=character_class,
        level=level,
        age=age,
        one_liner=one_liner,
        backstory=backstory,
        top_magic_items=top_magic_items,
        notable_traits=notable_traits,
        pets_companions=pets_companions,
        status=status,
    )

    # Stage it for saving.
    db.add(character)

    # Write it to the database.
    db.commit()

    # Pull back the saved version (now with
    # its auto-assigned id).
    db.refresh(character)

    # Redirect to the new character's dossier
    # page. status_code=303 is the HTTP way of
    # saying "I'm redirecting you after a form
    # submission." It tells the browser to use
    # GET for the redirect, preventing the
    # "resubmit form?" popup if the user
    # refreshes the page.
    return RedirectResponse(
        url=f"/characters/{character.id}",
        status_code=303
    )


# ============================================
# ROUTE: VIEW ONE CHARACTER
# GET /characters/{id}
# ============================================
# The full dossier view. Click a character
# card on the roster and you land here.
#
# {id} is a path parameter — FastAPI extracts
# it from the URL and passes it as the "id"
# argument. /characters/3 means id=3.
#
# db.query(Character).filter(...).first()
# is SQLAlchemy for:
# "SELECT * FROM characters WHERE id = 3
#  LIMIT 1"
#
# .first() returns the single result or None
# if no match is found.
# ============================================
@router.get("/{id}")
async def character_detail(
    request: Request,
    id: int,
    db: Session = Depends(get_db)
):
    character = (
        db.query(Character)
        .filter(Character.id == id)
        .first()
    )

    # If no character was found with that id,
    # show a 404 page. In a real production
    # app we'd raise an HTTPException, but
    # for now a simple message works.
    if not character:
        return HTMLResponse(
            content="<h1>Character not found</h1>"
                    "<p>This dossier doesn't exist. "
                    "Perhaps they vanished into the "
                    "frozen wastes...</p>",
            status_code=404
        )

    return templates.TemplateResponse(
        "characters/detail.html",
        {
            "request": request,
            "title": f"{character.name} — Godfall",
            "character": character,
        }
    )


# ============================================
# ROUTE: EDIT CHARACTER FORM
# GET /characters/{id}/edit
# ============================================
# Shows the same form as "new" but pre-filled
# with the character's existing data. We pass
# the character object to the template and
# set editing=True so the template knows to
# fill in the fields.
#
# This is the power of reusing one template
# for both create and edit — like using the
# same cockpit for training and live missions,
# just with different configurations loaded.
# ============================================
@router.get("/{id}/edit")
async def character_edit_form(
    request: Request,
    id: int,
    db: Session = Depends(get_db)
):
    character = (
        db.query(Character)
        .filter(Character.id == id)
        .first()
    )

    if not character:
        return HTMLResponse(
            content="<h1>Character not found</h1>",
            status_code=404
        )

    return templates.TemplateResponse(
        "characters/form.html",
        {
            "request": request,
            "title": f"Edit {character.name} — Godfall",
            "character": character,
            "editing": True,
        }
    )


# ============================================
# ROUTE: UPDATE CHARACTER
# POST /characters/{id}/edit
# ============================================
# Processes the edit form and updates the
# existing character record.
#
# Instead of creating a new object, we fetch
# the existing one and update its attributes.
# SQLAlchemy tracks changes automatically —
# when we commit, it generates an UPDATE
# statement, not an INSERT.
#
# Like modifying a dossier instead of writing
# a new one from scratch.
# ============================================
@router.post("/{id}/edit")
async def character_update(
    request: Request,
    id: int,
    db: Session = Depends(get_db),
    name: str = Form(...),
    player_name: str = Form(...),
    race: str = Form(...),
    character_class: str = Form(...),
    level: int = Form(1),
    age: str = Form(None),
    one_liner: str = Form(None),
    backstory: str = Form(None),
    top_magic_items: str = Form(None),
    notable_traits: str = Form(None),
    pets_companions: str = Form(None),
    status: str = Form("Active"),
):
    character = (
        db.query(Character)
        .filter(Character.id == id)
        .first()
    )

    if not character:
        return HTMLResponse(
            content="<h1>Character not found</h1>",
            status_code=404
        )

    # Update each field. SQLAlchemy detects
    # the changes automatically.
    character.name = name
    character.player_name = player_name
    character.race = race
    character.character_class = character_class
    character.level = level
    character.age = age
    character.one_liner = one_liner
    character.backstory = backstory
    character.top_magic_items = top_magic_items
    character.notable_traits = notable_traits
    character.pets_companions = pets_companions
    character.status = status

    # Commit the changes.
    db.commit()

    return RedirectResponse(
        url=f"/characters/{character.id}",
        status_code=303
    )


# ============================================
# ROUTE: DELETE CHARACTER
# POST /characters/{id}/delete
# ============================================
# Removes a character and all their images
# from the database. The cascade rule we set
# up in models.py handles deleting the image
# RECORDS, but we also need to delete the
# actual image FILES from disk.
#
# A two-step cleanup: erase the records
# (database) and erase the evidence (files).
# Thorough, like the Empire. But for good.
# ============================================
@router.post("/{id}/delete")
async def character_delete(
    id: int,
    db: Session = Depends(get_db)
):
    character = (
        db.query(Character)
        .filter(Character.id == id)
        .first()
    )

    if not character:
        return HTMLResponse(
            content="<h1>Character not found</h1>",
            status_code=404
        )

    # Delete actual image files from disk
    for image in character.images:
        file_path = BASE_DIR / image.file_path.lstrip("/")
        if file_path.exists():
            file_path.unlink()

    # Delete the character (cascade handles
    # the image records in the database).
    db.delete(character)
    db.commit()

    # Redirect back to the roster.
    return RedirectResponse(
        url="/characters",
        status_code=303
    )


# ============================================
# ROUTE: UPLOAD IMAGES
# POST /characters/{id}/upload
# ============================================
# Handles image file uploads for a character.
# The user can upload multiple files at once.
#
# New concepts:
#
# List[UploadFile]: tells FastAPI to expect
# multiple files. The HTML form needs
# multiple="true" on the file input.
#
# uuid.uuid4(): generates a unique random
# string. We prepend this to the filename so
# that two files with the same name (like
# "portrait.jpg") don't overwrite each other.
# Like assigning unique call signs to pilots
# who happen to share a name.
#
# shutil.copyfileobj(): efficiently copies
# the uploaded file data to a file on disk.
# It handles the streaming so we don't have
# to load the entire image into memory.
# ============================================
from typing import List, Optional

@router.post("/{id}/upload")
async def character_upload_images(
    id: int,
    db: Session = Depends(get_db),
    files: List[UploadFile] = File(...),
    caption: Optional[str] = Form(None),
    is_primary: int = Form(0),
):
    character = (
        db.query(Character)
        .filter(Character.id == id)
        .first()
    )

    if not character:
        return HTMLResponse(
            content="<h1>Character not found</h1>",
            status_code=404
        )

    for uploaded_file in files:
        # Generate a unique filename to prevent
        # collisions. uuid4() creates something
        # like "a3f7b2c1-..." that we prepend
        # to the original filename.
        unique_name = f"{uuid.uuid4().hex}_{uploaded_file.filename}"
        file_path = UPLOAD_DIR / unique_name

        # Save the file to disk.
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(uploaded_file.file, buffer)

        # If this is marked as the primary image,
        # first unset any existing primary image
        # for this character.
        if is_primary:
            db.query(CharacterImage).filter(
                CharacterImage.character_id == character.id,
                CharacterImage.is_primary == 1
            ).update({"is_primary": 0})

        # Create a database record for the image.
        # The file_path stored is relative to
        # the static folder so it works as a URL.
        image_record = CharacterImage(
            character_id=character.id,
            file_path=f"/static/uploads/characters/{unique_name}",
            caption=caption,
            is_primary=is_primary,
        )

        db.add(image_record)

    db.commit()

    return RedirectResponse(
        url=f"/characters/{character.id}",
        status_code=303
    )


# ============================================
# ROUTE: DELETE A SINGLE IMAGE
# POST /characters/{id}/images/{image_id}/delete
# ============================================
# Removes one image from a character — both
# the database record and the file on disk.
# ============================================
@router.post("/{id}/images/{image_id}/delete")
async def character_image_delete(
    id: int,
    image_id: int,
    db: Session = Depends(get_db)
):
    image = (
        db.query(CharacterImage)
        .filter(
            CharacterImage.id == image_id,
            CharacterImage.character_id == id,
        )
        .first()
    )

    if not image:
        return HTMLResponse(
            content="<h1>Image not found</h1>",
            status_code=404
        )

    # Delete the file from disk.
    file_path = BASE_DIR / image.file_path.lstrip("/")
    if file_path.exists():
        file_path.unlink()

    # Delete the database record.
    db.delete(image)
    db.commit()

    return RedirectResponse(
        url=f"/characters/{id}",
        status_code=303
    )