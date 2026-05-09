# ============================================
# GODFALL - app/routes/lore.py
# Lore Mission Control
# ============================================
# Routes for the world lore section.
# Familiar CRUD + image patterns, plus:
#
#   - Two join tables (LoreCharacter,
#     LoreEvent) managed in the same
#     delete-and-recreate pattern from
#     the timeline phase.
#
#   - Query parameter filtering — the URL
#     /lore?category=Location lets us scope
#     the list view, and the parameter is
#     accepted automatically by FastAPI.
# ============================================

# --- IMPORTS ---
from fastapi import (
    APIRouter,
    Request,
    Depends,
    Form,
    UploadFile,
    File,
)
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.orm import Session

from pathlib import Path
from typing import List, Optional
import shutil
import uuid

from app.database import get_db
from app.models import (
    LoreEntry,
    LoreImage,
    LoreCharacter,
    LoreEvent,
    Character,
    TimelineEvent,
)
from app.templating import templates

# --- CONFIGURATION ---
BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_DIR = BASE_DIR / "static" / "uploads" / "lore"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# --- CREATE THE ROUTER ---
router = APIRouter(
    prefix="/lore",
    tags=["Lore"],
)

# --- AVAILABLE CATEGORIES ---
# Defined here so we can pass it to forms
# and the filter UI. Adding a new category
# is a one-line change here — no migrations,
# no data updates. Existing entries with
# categories not in this list still work fine.
#
# Like a starport's official ship registry —
# unofficial visitors are still allowed in,
# they just don't show up in the standard menu.
LORE_CATEGORIES = [
    "Location",
    "Faction",
    "Item",
    "Deity",
    "Creature",
    "Event",
    "Other",
]


# ============================================
# ROUTE: LORE LIST
# GET /lore
# ============================================
# The main lore browse page. Optionally
# filtered by category via query parameter:
#   /lore                  → all entries
#   /lore?category=Faction → factions only
#
# FastAPI auto-recognizes "category" as a
# query parameter because we declared it as
# a function argument that doesn't match a
# path parameter.
#
# Optional[str] = None means: "this query
# parameter is optional, and defaults to
# None if not provided."
# ============================================
@router.get("/")
async def lore_list(
    request: Request,
    db: Session = Depends(get_db),
    category: Optional[str] = None,
):
    # Build the base query
    query = db.query(LoreEntry)

    # Apply category filter if provided
    if category and category != "all":
        query = query.filter(LoreEntry.category == category)

    # Always sort alphabetically — predictable,
    # easy to scan visually.
    entries = query.order_by(LoreEntry.title).all()

    return templates.TemplateResponse(
        "lore/list.html",
        {
            "request": request,
            "title": "World Lore — Godfall",
            "entries": entries,
            "categories": LORE_CATEGORIES,
            "active_category": category or "all",
        },
    )


# ============================================
# ROUTE: NEW LORE FORM
# GET /lore/new
# ============================================
# Same pattern as previous "new form" routes.
# We pass in the categories list, character
# lists (PCs and NPCs split), and event list
# so the form can render its pickers.
#
# An optional ?category= query param pre-fills
# the category dropdown. Useful for "add a new
# Location" buttons on filtered views — one
# fewer click for the DM.
# ============================================
@router.get("/new")
async def lore_new_form(
    request: Request,
    db: Session = Depends(get_db),
    category: Optional[str] = None,
):
    pcs = (
        db.query(Character)
        .filter(Character.character_type == "player")
        .order_by(Character.name)
        .all()
    )
    npcs = (
        db.query(Character)
        .filter(Character.character_type == "npc")
        .order_by(Character.name)
        .all()
    )
    events = db.query(TimelineEvent).order_by(TimelineEvent.sort_order).all()

    return templates.TemplateResponse(
        "lore/form.html",
        {
            "request": request,
            "title": "New Lore Entry — Godfall",
            "entry": None,
            "editing": False,
            "categories": LORE_CATEGORIES,
            "pcs": pcs,
            "npcs": npcs,
            "events": events,
            "selected_character_ids": set(),
            "selected_event_ids": set(),
            "preselected_category": category,
        },
    )


# ============================================
# ROUTE: CREATE NEW LORE ENTRY
# POST /lore/new
# ============================================
# Three steps:
#   1. Create the LoreEntry
#   2. Create LoreCharacter rows for each
#      selected character
#   3. Create LoreEvent rows for each selected
#      event
#
# Same delete-and-recreate pattern we used
# for events, just adapted for two join tables
# instead of one.
# ============================================
@router.post("/new")
async def lore_create(
    request: Request,
    db: Session = Depends(get_db),
    title: str = Form(...),
    category: str = Form(...),
    subtitle: Optional[str] = Form(None),
    body: Optional[str] = Form(None),
    is_secret: int = Form(0),
    lat: Optional[float] = Form(None),
    lng: Optional[float] = Form(None),
    character_ids: List[int] = Form(default=[]),
    event_ids: List[int] = Form(default=[]),
):
    new_entry = LoreEntry(
        title=title,
        category=category,
        subtitle=subtitle,
        body=body,
        is_secret=is_secret,
        lat=lat,
        lng=lng,
    )
    db.add(new_entry)
    db.commit()
    db.refresh(new_entry)

    # Create character connections
    for character_id in character_ids:
        link = LoreCharacter(
            lore_id=new_entry.id,
            character_id=character_id,
        )
        db.add(link)

    # Create event connections
    for event_id in event_ids:
        link = LoreEvent(
            lore_id=new_entry.id,
            event_id=event_id,
        )
        db.add(link)

    db.commit()

    return RedirectResponse(url=f"/lore/{new_entry.id}", status_code=303)


# ============================================
# ROUTE: VIEW ONE LORE ENTRY
# GET /lore/{id}
# ============================================
@router.get("/{id}")
async def lore_detail(request: Request, id: int, db: Session = Depends(get_db)):
    entry = db.query(LoreEntry).filter(LoreEntry.id == id).first()

    if not entry:
        return HTMLResponse(
            content="<h1>Lore not found</h1>"
            "<p>This entry has been lost to the "
            "frozen ages.</p>",
            status_code=404,
        )

    return templates.TemplateResponse(
        "lore/detail.html",
        {
            "request": request,
            "title": f"{entry.title} — Godfall",
            "entry": entry,
        },
    )


# ============================================
# ROUTE: EDIT LORE FORM
# GET /lore/{id}/edit
# ============================================
@router.get("/{id}/edit")
async def lore_edit_form(request: Request, id: int, db: Session = Depends(get_db)):
    entry = db.query(LoreEntry).filter(LoreEntry.id == id).first()

    if not entry:
        return HTMLResponse(content="<h1>Lore not found</h1>", status_code=404)

    pcs = (
        db.query(Character)
        .filter(Character.character_type == "player")
        .order_by(Character.name)
        .all()
    )
    npcs = (
        db.query(Character)
        .filter(Character.character_type == "npc")
        .order_by(Character.name)
        .all()
    )
    events = db.query(TimelineEvent).order_by(TimelineEvent.sort_order).all()

    selected_character_ids = {link.character_id for link in entry.character_links}
    selected_event_ids = {link.event_id for link in entry.event_links}

    return templates.TemplateResponse(
        "lore/form.html",
        {
            "request": request,
            "title": f"Edit {entry.title} — Godfall",
            "entry": entry,
            "editing": True,
            "categories": LORE_CATEGORIES,
            "pcs": pcs,
            "npcs": npcs,
            "events": events,
            "selected_character_ids": selected_character_ids,
            "selected_event_ids": selected_event_ids,
            "preselected_category": None,
        },
    )


# ============================================
# ROUTE: UPDATE LORE ENTRY
# POST /lore/{id}/edit
# ============================================
# Wipe-and-rebuild for both join tables.
# ============================================
@router.post("/{id}/edit")
async def lore_update(
    request: Request,
    id: int,
    db: Session = Depends(get_db),
    title: str = Form(...),
    category: str = Form(...),
    subtitle: Optional[str] = Form(None),
    body: Optional[str] = Form(None),
    is_secret: int = Form(0),
    lat: Optional[float] = Form(None),
    lng: Optional[float] = Form(None),
    character_ids: List[int] = Form(default=[]),
    event_ids: List[int] = Form(default=[]),
):
    entry = db.query(LoreEntry).filter(LoreEntry.id == id).first()

    if not entry:
        return HTMLResponse(content="<h1>Lore not found</h1>", status_code=404)

    # Update fields
    entry.title = title
    entry.category = category
    entry.subtitle = subtitle
    entry.body = body
    entry.is_secret = is_secret
    entry.lat = lat
    entry.lng = lng

    # Wipe and rebuild character links
    db.query(LoreCharacter).filter(LoreCharacter.lore_id == entry.id).delete()
    for character_id in character_ids:
        link = LoreCharacter(
            lore_id=entry.id,
            character_id=character_id,
        )
        db.add(link)

    # Wipe and rebuild event links
    db.query(LoreEvent).filter(LoreEvent.lore_id == entry.id).delete()
    for event_id in event_ids:
        link = LoreEvent(
            lore_id=entry.id,
            event_id=event_id,
        )
        db.add(link)

    db.commit()

    return RedirectResponse(url=f"/lore/{entry.id}", status_code=303)


# ============================================
# ROUTE: DELETE LORE ENTRY
# POST /lore/{id}/delete
# ============================================
@router.post("/{id}/delete")
async def lore_delete(id: int, db: Session = Depends(get_db)):
    entry = db.query(LoreEntry).filter(LoreEntry.id == id).first()

    if not entry:
        return HTMLResponse(content="<h1>Lore not found</h1>", status_code=404)

    # Delete image files from disk
    for image in entry.images:
        file_path = BASE_DIR / image.file_path.lstrip("/")
        if file_path.exists():
            file_path.unlink()

    db.delete(entry)
    db.commit()

    return RedirectResponse(url="/lore", status_code=303)


# ============================================
# ROUTE: UPLOAD IMAGES
# POST /lore/{id}/upload
# ============================================
@router.post("/{id}/upload")
async def lore_upload_images(
    id: int,
    db: Session = Depends(get_db),
    files: List[UploadFile] = File(...),
    caption: Optional[str] = Form(None),
    is_featured: int = Form(0),
):
    entry = db.query(LoreEntry).filter(LoreEntry.id == id).first()

    if not entry:
        return HTMLResponse(content="<h1>Lore not found</h1>", status_code=404)

    for uploaded_file in files:
        unique_name = f"{uuid.uuid4().hex}_{uploaded_file.filename}"
        file_path = UPLOAD_DIR / unique_name

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(uploaded_file.file, buffer)

        if is_featured:
            db.query(LoreImage).filter(
                LoreImage.lore_id == entry.id, LoreImage.is_featured == 1
            ).update({"is_featured": 0})

        image_record = LoreImage(
            lore_id=entry.id,
            file_path=f"/static/uploads/lore/{unique_name}",
            caption=caption,
            is_featured=is_featured,
        )

        db.add(image_record)

    db.commit()

    return RedirectResponse(url=f"/lore/{entry.id}", status_code=303)


# ============================================
# ROUTE: DELETE A SINGLE IMAGE
# POST /lore/{id}/images/{image_id}/delete
# ============================================
@router.post("/{id}/images/{image_id}/delete")
async def lore_image_delete(id: int, image_id: int, db: Session = Depends(get_db)):
    image = (
        db.query(LoreImage)
        .filter(
            LoreImage.id == image_id,
            LoreImage.lore_id == id,
        )
        .first()
    )

    if not image:
        return HTMLResponse(content="<h1>Image not found</h1>", status_code=404)

    file_path = BASE_DIR / image.file_path.lstrip("/")
    if file_path.exists():
        file_path.unlink()

    db.delete(image)
    db.commit()

    return RedirectResponse(url=f"/lore/{id}", status_code=303)