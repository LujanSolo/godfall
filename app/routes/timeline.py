# ============================================
# GODFALL - app/routes/timeline.py
# Timeline Mission Control
# ============================================
# All routes for the interactive timeline.
# Familiar CRUD shape from characters and
# sessions, plus three new things:
#
#   1. Cast management — adding, removing,
#      and updating character connections
#      via the EventCharacter join table.
#
#   2. HTMX preview endpoint — a tiny route
#      that returns just a fragment of HTML
#      for hover tooltips. Our first real
#      use of HTMX in the project.
#
#   3. Sort order management — keeping the
#      timeline visually consistent.
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
    TimelineEvent,
    EventImage,
    EventCharacter,
    Character,
)

# --- USE THE CENTRAL TEMPLATES INSTANCE ---
# Same pattern as sessions.py and characters.py.
# One source of truth for filters and template
# config, like we set up after the great
# templating refactor.
from app.templating import templates

# --- CONFIGURATION ---
BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_DIR = BASE_DIR / "static" / "uploads" / "timeline"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# --- CREATE THE ROUTER ---
router = APIRouter(
    prefix="/timeline",
    tags=["Timeline"],
)


# ============================================
# ROUTE: TIMELINE VIEW (the main attraction)
# GET /timeline
# ============================================
# Renders the full interactive timeline.
# Events are sorted by sort_order ascending
# (left-to-right on desktop, top-to-bottom
# on mobile).
#
# We pre-compute the featured image for
# each event in Python, since templates
# can't easily do it efficiently.
# ============================================
@router.get("/")
async def timeline_view(
    request: Request,
    db: Session = Depends(get_db)
):
    events = (
        db.query(TimelineEvent)
        .order_by(TimelineEvent.sort_order.asc())
        .all()
    )

    return templates.TemplateResponse(
        "timeline/list.html",
        {
            "request": request,
            "title": "Timeline — Godfall",
            "events": events,
        }
    )


# ============================================
# ROUTE: NEW EVENT FORM
# GET /timeline/new
# ============================================
# Same "named route before parameter route"
# rule. /new before /{id}.
#
# We pass in the character lists separated
# by type, so the form can show two picker
# sections (PCs and NPCs).
#
# Suggested sort_order is the highest
# existing + 100 — leaves room to insert.
# ============================================
@router.get("/new")
async def event_new_form(
    request: Request,
    db: Session = Depends(get_db)
):
    last_event = (
        db.query(TimelineEvent)
        .order_by(TimelineEvent.sort_order.desc())
        .first()
    )
    suggested_sort_order = (last_event.sort_order + 100) if last_event else 100

    # Split characters by type for the picker.
    # The character_type field we added back
    # in Phase 2 (looking out for future-us)
    # makes this trivial.
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

    return templates.TemplateResponse(
        "timeline/form.html",
        {
            "request": request,
            "title": "New Event — Godfall",
            "event": None,
            "editing": False,
            "suggested_sort_order": suggested_sort_order,
            "pcs": pcs,
            "npcs": npcs,
            "selected_character_ids": set(),  # empty for new
        }
    )


# ============================================
# ROUTE: CREATE NEW EVENT
# POST /timeline/new
# ============================================
# Two things happen here:
#   1. Create the TimelineEvent itself
#   2. Create EventCharacter rows for each
#      character that was selected
#
# The character_ids parameter receives a
# list because the form has multiple
# checkboxes with the same name. FastAPI
# automatically gathers them into a list
# when the type hint is List[int].
# ============================================
@router.post("/new")
async def event_create(
    request: Request,
    db: Session = Depends(get_db),
    title: str = Form(...),
    event_date: Optional[str] = Form(None),
    event_end_date: Optional[str] = Form(None),
    sort_order: int = Form(...),
    summary: Optional[str] = Form(None),
    body: Optional[str] = Form(None),
    is_milestone: int = Form(0),
    character_ids: List[int] = Form(default=[]),
):
    # Step 1: create the event itself
    new_event = TimelineEvent(
        title=title,
        event_date=event_date,
        event_end_date=event_end_date,
        sort_order=sort_order,
        summary=summary,
        body=body,
        is_milestone=is_milestone,
    )
    db.add(new_event)
    db.commit()
    db.refresh(new_event)

    # Step 2: create the character links
    # We loop through each selected character
    # id and create an EventCharacter row
    # connecting it to the new event.
    #
    # Like creating mission assignments —
    # one record per pilot/squadron pairing.
    for character_id in character_ids:
        link = EventCharacter(
            event_id=new_event.id,
            character_id=character_id,
        )
        db.add(link)

    db.commit()

    return RedirectResponse(
        url=f"/timeline/{new_event.id}",
        status_code=303
    )


# ============================================
# ROUTE: VIEW ONE EVENT
# GET /timeline/{id}
# ============================================
# The full detail page. Through the
# character_links relationship, we can
# access all linked characters from the
# event object directly in the template.
# ============================================
@router.get("/{id}")
async def event_detail(
    request: Request,
    id: int,
    db: Session = Depends(get_db)
):
    event = (
        db.query(TimelineEvent)
        .filter(TimelineEvent.id == id)
        .first()
    )

    if not event:
        return HTMLResponse(
            content="<h1>Event not found</h1>"
                    "<p>This moment in history doesn't exist. "
                    "Or perhaps it never happened — yet.</p>",
            status_code=404
        )

    return templates.TemplateResponse(
        "timeline/detail.html",
        {
            "request": request,
            "title": f"{event.title} — Godfall",
            "event": event,
        }
    )


# ============================================
# ROUTE: HTMX HOVER PREVIEW
# GET /timeline/{id}/preview
# ============================================
# THE NEW HOTNESS. This route returns just
# a small HTML fragment — not a full page.
# HTMX will swap this fragment into a
# tooltip element when the user hovers a
# timeline node.
#
# Notice we use TemplateResponse just like
# normal — the difference is the template
# itself only contains the tooltip markup,
# no <html> or <body> wrapper. It's a
# fragment, not a page.
#
# The philosophy: the server stays the
# source of truth, even for tiny UI bits.
# No client-side state to manage. No
# duplicate data on the front-end. Just
# "give me the tooltip HTML for event 7,"
# and the server hands it over.
#
# Like asking the ship's computer for a
# brief on a planet — you get exactly the
# info you need, freshly fetched, no need
# to keep a copy in your head.
# ============================================
@router.get("/{id}/preview")
async def event_preview(
    request: Request,
    id: int,
    db: Session = Depends(get_db)
):
    event = (
        db.query(TimelineEvent)
        .filter(TimelineEvent.id == id)
        .first()
    )

    if not event:
        return HTMLResponse(content="", status_code=404)

    return templates.TemplateResponse(
        "timeline/_preview.html",
        {
            "request": request,
            "event": event,
        }
    )


# ============================================
# ROUTE: EDIT EVENT FORM
# GET /timeline/{id}/edit
# ============================================
# Like the new form but pre-fills with
# existing data. We also build a set of
# already-selected character ids so the
# form template can mark those checkboxes
# as checked.
#
# Why a set instead of a list? Because we'll
# do "is this character_id in our selected
# set?" lookups inside the template loop —
# and that operation is O(1) on a set vs
# O(n) on a list. For 10 characters it
# doesn't matter, but the right pattern is
# the right pattern.
# ============================================
@router.get("/{id}/edit")
async def event_edit_form(
    request: Request,
    id: int,
    db: Session = Depends(get_db)
):
    event = (
        db.query(TimelineEvent)
        .filter(TimelineEvent.id == id)
        .first()
    )

    if not event:
        return HTMLResponse(
            content="<h1>Event not found</h1>",
            status_code=404
        )

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

    # Build a set of character IDs already
    # connected to this event.
    selected_character_ids = {
        link.character_id for link in event.character_links
    }

    return templates.TemplateResponse(
        "timeline/form.html",
        {
            "request": request,
            "title": f"Edit {event.title} — Godfall",
            "event": event,
            "editing": True,
            "suggested_sort_order": event.sort_order,
            "pcs": pcs,
            "npcs": npcs,
            "selected_character_ids": selected_character_ids,
        }
    )


# ============================================
# ROUTE: UPDATE EVENT
# POST /timeline/{id}/edit
# ============================================
# This one's interesting because of the
# cast management. The simplest approach
# (and what we'll do): wipe all existing
# character links for this event and
# re-create them from the submitted form.
#
# This is called the "delete-and-recreate"
# pattern. Pros: dead simple, hard to get
# wrong. Cons: loses any per-link data we
# might add later (like role notes — we'll
# rebuild those on edit, which is fine).
#
# A more sophisticated approach would
# diff the lists and only add/remove the
# changes. We can refactor to that later
# if performance becomes a concern. With
# 5-15 characters it's a non-issue.
# ============================================
@router.post("/{id}/edit")
async def event_update(
    request: Request,
    id: int,
    db: Session = Depends(get_db),
    title: str = Form(...),
    event_date: Optional[str] = Form(None),
    sort_order: int = Form(...),
    summary: Optional[str] = Form(None),
    body: Optional[str] = Form(None),
    is_milestone: int = Form(0),
    character_ids: List[int] = Form(default=[]),
):
    event = (
        db.query(TimelineEvent)
        .filter(TimelineEvent.id == id)
        .first()
    )

    if not event:
        return HTMLResponse(
            content="<h1>Event not found</h1>",
            status_code=404
        )

    # Update event fields
    event.title = title
    event.event_date = event_date
    event.event_end_date = event_end_date
    event.sort_order = sort_order
    event.summary = summary
    event.body = body
    event.is_milestone = is_milestone

    # Wipe existing character links.
    # The cascade we set up in the model
    # would handle this if we deleted the
    # event entirely, but here we're just
    # rebuilding the links — so we do it
    # manually.
    db.query(EventCharacter).filter(
        EventCharacter.event_id == event.id
    ).delete()

    # Recreate from form data
    for character_id in character_ids:
        link = EventCharacter(
            event_id=event.id,
            character_id=character_id,
        )
        db.add(link)

    db.commit()

    return RedirectResponse(
        url=f"/timeline/{event.id}",
        status_code=303
    )


# ============================================
# ROUTE: DELETE EVENT
# POST /timeline/{id}/delete
# ============================================
# Cascade rules in the model handle the
# database cleanup (images and character
# links go with the event). We still need
# to manually delete the image FILES from
# disk, same pattern as before.
# ============================================
@router.post("/{id}/delete")
async def event_delete(
    id: int,
    db: Session = Depends(get_db)
):
    event = (
        db.query(TimelineEvent)
        .filter(TimelineEvent.id == id)
        .first()
    )

    if not event:
        return HTMLResponse(
            content="<h1>Event not found</h1>",
            status_code=404
        )

    # Delete image files from disk
    for image in event.images:
        file_path = BASE_DIR / image.file_path.lstrip("/")
        if file_path.exists():
            file_path.unlink()

    db.delete(event)
    db.commit()

    return RedirectResponse(
        url="/timeline",
        status_code=303
    )

# ============================================
# ROUTE: UPLOAD IMAGES
# POST /timeline/{id}/upload
# ============================================
@router.post("/{id}/upload")
async def event_upload_images(
    id: int,
    db: Session = Depends(get_db),
    files: List[UploadFile] = File(...),
    caption: Optional[str] = Form(None),
    is_featured: int = Form(0),
):
    event = (
        db.query(TimelineEvent)
        .filter(TimelineEvent.id == id)
        .first()
    )

    if not event:
        return HTMLResponse(
            content="<h1>Event not found</h1>",
            status_code=404
        )

    for uploaded_file in files:
        unique_name = f"{uuid.uuid4().hex}_{uploaded_file.filename}"
        file_path = UPLOAD_DIR / unique_name

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(uploaded_file.file, buffer)

        if is_featured:
            db.query(EventImage).filter(
                EventImage.event_id == event.id,
                EventImage.is_featured == 1
            ).update({"is_featured": 0})

        image_record = EventImage(
            event_id=event.id,
            file_path=f"/static/uploads/timeline/{unique_name}",
            caption=caption,
            is_featured=is_featured,
        )

        db.add(image_record)

    db.commit()

    return RedirectResponse(
        url=f"/timeline/{event.id}",
        status_code=303
    )


# ============================================
# ROUTE: DELETE A SINGLE IMAGE
# POST /timeline/{id}/images/{image_id}/delete
# ============================================
@router.post("/{id}/images/{image_id}/delete")
async def event_image_delete(
    id: int,
    image_id: int,
    db: Session = Depends(get_db)
):
    image = (
        db.query(EventImage)
        .filter(
            EventImage.id == image_id,
            EventImage.event_id == id,
        )
        .first()
    )

    if not image:
        return HTMLResponse(
            content="<h1>Image not found</h1>",
            status_code=404
        )

    file_path = BASE_DIR / image.file_path.lstrip("/")
    if file_path.exists():
        file_path.unlink()

    db.delete(image)
    db.commit()

    return RedirectResponse(
        url=f"/timeline/{id}",
        status_code=303
    )