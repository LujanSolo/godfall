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
#   - The Codex / Folio system with chapters,
#     gem grids, reveal states, and search.
# ============================================

# --- IMPORTS ---
from app.auth import require_dm, get_current_user
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
    User,
)
from app.templating import templates

# ============================================
# CHAPTER SLUG HELPERS
# ============================================

CODEX_CHAPTERS = [
    "Places of the North",
    "Allies, Enemies & Other Dalefolk",
    "Relics & Curiosities",
    "Gods & Mysteries",
    "Whispers & Rumors",
]


def chapter_to_slug(chapter_name: str) -> str:
    return (
        chapter_name.lower()
        .replace(" & ", "-and-")
        .replace(",", "")
        .replace(" ", "-")
        .replace("'", "")
    )


def slug_to_chapter(slug: str) -> Optional[str]:
    for chapter in CODEX_CHAPTERS:
        if chapter_to_slug(chapter) == slug:
            return chapter
    return None


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
LORE_CATEGORIES = [
    "Location",
    "NPC",
    "Faction",
    "Item",
    "Deity",
    "Creature",
    "Event",
    "Other",
]


# ============================================
# ROUTE: SEARCH DATA (JSON)
# GET /lore/search-data
# ============================================
@router.get("/search-data")
async def search_data(
    request: Request,
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_current_user),
):
    query = db.query(LoreEntry)

    if user is None or user.role != "dm":
        query = query.filter(LoreEntry.is_secret == 0)
        query = query.filter(LoreEntry.is_revealed == 1)

    entries = query.order_by(LoreEntry.title).all()

    results = [
        {
            "id": entry.id,
            "title": entry.title,
            "subtitle": entry.subtitle or "",
            "category": entry.category or "",
            "chapter": entry.folio_chapter or "",
            "url": f"/lore/{entry.id}",
        }
        for entry in entries
    ]

    return {"entries": results}


# ============================================
# ROUTE: LORE LIST (TABLE OF CONTENTS)
# GET /lore
# ============================================
@router.get("/")
async def lore_list(
    request: Request,
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_current_user),
):
    query = db.query(LoreEntry)

    if user is None or user.role != "dm":
        query = query.filter(LoreEntry.is_secret == 0)

    entries = query.order_by(
        LoreEntry.folio_chapter, LoreEntry.folio_position, LoreEntry.title
    ).all()

    # Group entries by chapter
    chapters = {}
    for entry in entries:
        chapter = entry.folio_chapter or "Whispers & Rumors"
        if chapter not in chapters:
            chapters[chapter] = []
        chapters[chapter].append(entry)

    # Sort chapters into canonical order
    ordered_chapters = {}
    for chapter_name in CODEX_CHAPTERS:
        if chapter_name in chapters:
            ordered_chapters[chapter_name] = chapters[chapter_name]
    for chapter_name, entries_list in chapters.items():
        if chapter_name not in ordered_chapters:
            ordered_chapters[chapter_name] = entries_list
    chapters = ordered_chapters

    # Count revealed vs total for each chapter
    chapter_stats = {}
    for chapter_name, chapter_entries in chapters.items():
        total = len(chapter_entries)
        revealed = sum(1 for e in chapter_entries if e.is_revealed == 1)
        chapter_stats[chapter_name] = {
            "total": total,
            "revealed": revealed,
        }

    return templates.TemplateResponse(
        "lore/list.html",
        {
            "request": request,
            "title": "The Codex — Godfall",
            "chapters": chapters,
            "chapter_stats": chapter_stats,
            "codex_chapters": CODEX_CHAPTERS,
        },
    )


# ============================================
# ROUTE: NEW LORE FORM
# GET /lore/new
# ============================================
@router.get("/new")
async def lore_new_form(
    request: Request,
    db: Session = Depends(get_db),
    _dm: User = Depends(require_dm),
    category: Optional[str] = None,
):
    pcs = (
        db.query(Character)
        .filter(Character.character_type == "player")
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
            "npcs": [],
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
@router.post("/new")
async def lore_create(
    request: Request,
    db: Session = Depends(get_db),
    _dm: User = Depends(require_dm),
    title: str = Form(...),
    category: str = Form(...),
    subtitle: Optional[str] = Form(None),
    body: Optional[str] = Form(None),
    is_secret: int = Form(0),
    folio_chapter: str = Form("Places of the North"),
    folio_layout: str = Form("bestiary"),
    folio_position: int = Form(0),
    is_revealed: int = Form(0),
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
        folio_chapter=folio_chapter,
        folio_layout=folio_layout,
        folio_position=folio_position,
        is_revealed=is_revealed,
        lat=lat,
        lng=lng,
    )
    db.add(new_entry)
    db.commit()
    db.refresh(new_entry)

    for character_id in character_ids:
        link = LoreCharacter(
            lore_id=new_entry.id,
            character_id=character_id,
        )
        db.add(link)

    for event_id in event_ids:
        link = LoreEvent(
            lore_id=new_entry.id,
            event_id=event_id,
        )
        db.add(link)

    db.commit()

    return RedirectResponse(url=f"/lore/{new_entry.id}", status_code=303)


# ============================================
# ROUTE: CHAPTER SPREAD
# GET /lore/chapter/{slug}
# ============================================
@router.get("/chapter/{slug}")
async def chapter_spread(
    request: Request,
    slug: str,
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_current_user),
):
    chapter_name = slug_to_chapter(slug)
    if chapter_name is None:
        return HTMLResponse(
            content="<h1>Chapter not found</h1>"
            "<p>This volume contains no such chapter.</p>",
            status_code=404,
        )

    # Query entries for this chapter
    query = db.query(LoreEntry).filter(LoreEntry.folio_chapter == chapter_name)

    # Non-DMs never see secret entries
    if user is None or user.role != "dm":
        query = query.filter(LoreEntry.is_secret == 0)

    entries = query.all()

    # Split into revealed and unrevealed,
    # each sorted alphabetically.
    revealed_entries = sorted(
        [e for e in entries if e.is_revealed == 1], key=lambda e: e.title.lower()
    )
    unrevealed_entries = sorted(
        [e for e in entries if e.is_revealed != 1], key=lambda e: e.title.lower()
    )

    # Chapter navigation
    try:
        current_idx = CODEX_CHAPTERS.index(chapter_name)
        prev_chapter = CODEX_CHAPTERS[current_idx - 1] if current_idx > 0 else None
        next_chapter = (
            CODEX_CHAPTERS[current_idx + 1]
            if current_idx < len(CODEX_CHAPTERS) - 1
            else None
        )
    except ValueError:
        prev_chapter = None
        next_chapter = None

    return templates.TemplateResponse(
        "lore/chapter.html",
        {
            "request": request,
            "title": f"{chapter_name} — The Codex",
            "chapter_name": chapter_name,
            "chapter_number": current_idx + 1,
            "revealed_entries": revealed_entries,
            "unrevealed_entries": unrevealed_entries,
            "prev_chapter": prev_chapter,
            "next_chapter": next_chapter,
            "chapter_to_slug": chapter_to_slug,
        },
    )


# ============================================
# ROUTE: VIEW ONE LORE ENTRY
# GET /lore/{id}
# ============================================
@router.get("/{id}")
async def lore_detail(
    request: Request,
    id: int,
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_current_user),
):
    entry = db.query(LoreEntry).filter(LoreEntry.id == id).first()

    if entry and entry.is_secret == 1:
        if user is None or user.role != "dm":
            entry = None

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
async def lore_edit_form(
    request: Request,
    id: int,
    db: Session = Depends(get_db),
    _dm: User = Depends(require_dm),
):
    entry = db.query(LoreEntry).filter(LoreEntry.id == id).first()

    if not entry:
        return HTMLResponse(content="<h1>Lore not found</h1>", status_code=404)

    pcs = (
        db.query(Character)
        .filter(Character.character_type == "player")
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
            "npcs": [],
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
@router.post("/{id}/edit")
async def lore_update(
    request: Request,
    id: int,
    db: Session = Depends(get_db),
    _dm: User = Depends(require_dm),
    title: str = Form(...),
    category: str = Form(...),
    subtitle: Optional[str] = Form(None),
    body: Optional[str] = Form(None),
    is_secret: int = Form(0),
    folio_chapter: str = Form("Places of the North"),
    folio_layout: str = Form("bestiary"),
    folio_position: int = Form(0),
    is_revealed: int = Form(0),
    lat: Optional[float] = Form(None),
    lng: Optional[float] = Form(None),
    character_ids: List[int] = Form(default=[]),
    event_ids: List[int] = Form(default=[]),
):
    entry = db.query(LoreEntry).filter(LoreEntry.id == id).first()

    if not entry:
        return HTMLResponse(content="<h1>Lore not found</h1>", status_code=404)

    entry.title = title
    entry.category = category
    entry.subtitle = subtitle
    entry.body = body
    entry.is_secret = is_secret
    entry.folio_chapter = folio_chapter
    entry.folio_layout = folio_layout
    entry.folio_position = folio_position
    entry.is_revealed = is_revealed
    entry.lat = lat
    entry.lng = lng

    db.query(LoreCharacter).filter(LoreCharacter.lore_id == entry.id).delete()
    for character_id in character_ids:
        link = LoreCharacter(
            lore_id=entry.id,
            character_id=character_id,
        )
        db.add(link)

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
async def lore_delete(
    id: int, db: Session = Depends(get_db), _dm: User = Depends(require_dm)
):
    entry = db.query(LoreEntry).filter(LoreEntry.id == id).first()

    if not entry:
        return HTMLResponse(content="<h1>Lore not found</h1>", status_code=404)

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
    _dm: User = Depends(require_dm),
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
# ROUTE: SET FEATURED IMAGE
# POST /lore/{id}/images/{image_id}/feature
# ============================================
# Like promoting a new wing commander —
# the previous one steps down, the new
# one steps up. Only one featured image
# at a time.
# ============================================
@router.post("/{id}/images/{image_id}/feature")
async def lore_image_set_featured(
    id: int,
    image_id: int,
    db: Session = Depends(get_db),
    _dm: User = Depends(require_dm),
):
    # Unfeature all images for this entry
    db.query(LoreImage).filter(
        LoreImage.lore_id == id, LoreImage.is_featured == 1
    ).update({"is_featured": 0})

    # Feature the selected one
    image = (
        db.query(LoreImage)
        .filter(LoreImage.id == image_id, LoreImage.lore_id == id)
        .first()
    )

    if image:
        image.is_featured = 1
        db.commit()

    return RedirectResponse(url=f"/lore/{id}", status_code=303)


# ============================================
# ROUTE: DELETE A SINGLE IMAGE
# POST /lore/{id}/images/{image_id}/delete
# ============================================
@router.post("/{id}/images/{image_id}/delete")
async def lore_image_delete(
    id: int,
    image_id: int,
    db: Session = Depends(get_db),
    _dm: User = Depends(require_dm),
):
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
