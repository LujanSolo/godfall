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
# The codex uses URL-safe slugs in its routes
# but stores chapters as human-readable names
# in the database. These helpers convert
# between the two representations.
#
# The slug rules mirror the Jinja2 filter
# chain used in the table of contents template:
#   lowercase, " & " → "-and-", spaces → "-",
#   apostrophes stripped.
#
# Centralizing this here means the slug logic
# lives in one place. If we ever change the
# rules, only one file needs updating.
# ============================================

# The canonical chapter names. Must match the
# dropdown values in the lore form template.
CODEX_CHAPTERS = [
    "Places of the North",
    "Allies, Enemies & Other Dalefolk",
    "Relics & Curiosities",
    "Gods & Mysteries",
    "Whispers & Rumors",
]


def chapter_to_slug(chapter_name: str) -> str:
    """Convert a chapter name to its URL slug."""
    return (
        chapter_name.lower().replace(" & ", "-and-").replace(" ", "-").replace("'", "")
    )


def slug_to_chapter(slug: str) -> Optional[str]:
    """
    Find the canonical chapter name matching
    a given slug. Returns None if the slug
    doesn't match any known chapter.
    """
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
# ROUTE: SEARCH DATA (JSON)
# GET /lore/search-data
# ============================================
# Returns a JSON array of all searchable lore
# entries the current viewer can see. The
# overlay JS uses this to power live filtering.
#
# We return JSON rather than HTML because the
# data is consumed by JavaScript, not rendered
# directly. FastAPI auto-serializes the
# returned dict to JSON with the correct
# content-type header.
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

    # Add NPCs to search results
    npcs = (
        db.query(Character)
        .filter(Character.character_type == "npc")
        .order_by(Character.name)
        .all()
    )

    for npc in npcs:
        results.append(
            {
                "id": npc.id,
                "title": npc.name,
                "subtitle": npc.one_liner or "",
                "category": "NPC",
                "chapter": "Allies, Enemies & Other Dalefolk",
                "url": f"/characters/{npc.id}",
            }
        )

    # Sort combined results alphabetically
    results.sort(key=lambda r: r["title"].lower())

    return {"entries": results}


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
    user: Optional[User] = Depends(get_current_user),
):
    # Build the base query
    query = db.query(LoreEntry)

    # Non-DMs never see is_secret entries — those
    # are DM-only forever. They DO see unrevealed
    # entries (as placeholder slots), so we don't
    # filter is_revealed at the query level.
    if user is None or user.role != "dm":
        query = query.filter(LoreEntry.is_secret == 0)

    entries = query.order_by(
        LoreEntry.folio_chapter, LoreEntry.folio_position, LoreEntry.title
    ).all()

    # Group entries by chapter into a dictionary.
    # Using a regular dict preserves insertion order
    # in Python 3.7+, which is what we want since we
    # already sorted by chapter.
    chapters = {}
    for entry in entries:
        chapter = entry.folio_chapter or "Whispers & Rumors"
        if chapter not in chapters:
            chapters[chapter] = []
        chapters[chapter].append(entry)

        # Sort chapters into canonical order.
        # Python dicts preserve insertion order,
        # so rebuilding the dict in the right
        # order gives us ordered iteration in
        # the template.
        ordered_chapters = {}
        for chapter_name in CODEX_CHAPTERS:
            if chapter_name in chapters:
                ordered_chapters[chapter_name] = chapters[chapter_name]
        # Catch any chapters not in the canonical list
        for chapter_name, entries_list in chapters.items():
            if chapter_name not in ordered_chapters:
                ordered_chapters[chapter_name] = entries_list
        chapters = ordered_chapters

    # Also count revealed vs total for each chapter,
    # which the template uses to show "X of Y known"
    # progress. For DMs this just shows the totals.
    chapter_stats = {}
    for chapter_name, chapter_entries in chapters.items():
        total = len(chapter_entries)
        revealed = sum(1 for e in chapter_entries if e.is_revealed == 1)
        chapter_stats[chapter_name] = {
            "total": total,
            "revealed": revealed,
        }

    # Add NPC count to the Dalefolk chapter stats
    dalefolk_chapter = "Allies, Enemies & Other Dalefolk"
    if dalefolk_chapter in chapter_stats:
        npc_count = (
            db.query(Character).filter(Character.character_type == "npc").count()
        )
        chapter_stats[dalefolk_chapter]["total"] += npc_count
        chapter_stats[dalefolk_chapter]["revealed"] += npc_count
    elif dalefolk_chapter not in chapters:
        # Chapter might not exist yet in lore entries
        # but should appear if there are NPCs
        npc_count = (
            db.query(Character).filter(Character.character_type == "npc").count()
        )
        if npc_count > 0:
            chapters[dalefolk_chapter] = []
            chapter_stats[dalefolk_chapter] = {
                "total": npc_count,
                "revealed": npc_count,
            }

    # template content dictionary
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
    _dm: User = Depends(require_dm),
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
# ROUTE: CHAPTER SPREAD
# GET /lore/chapter/{slug}
# ============================================
# Renders a single chapter as a spread.
# Entries are grouped by their folio_layout
# value: cathedral entries get their own
# spotlight panel, bestiary entries fill a
# grid, glossary entries appear as a textual
# listing.
#
# Unrevealed entries appear as faded slots
# for non-DM viewers — visible structure
# but obscured content.
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

    # --- LORE ENTRIES ---
    query = db.query(LoreEntry).filter(LoreEntry.folio_chapter == chapter_name)

    if user is None or user.role != "dm":
        query = query.filter(LoreEntry.is_secret == 0)

    lore_entries = query.all()

    # --- NPCs (only in the Dalefolk chapter) ---
    # NPCs live in the Character table but appear
    # as gems in the codex. We query them separately
    # and wrap them in a lightweight object that the
    # gem template can render uniformly alongside
    # lore entries.
    npc_gems = []
    if chapter_name == "Allies, Enemies & Other Dalefolk":
        npcs = (
            db.query(Character)
            .filter(Character.character_type == "npc")
            .order_by(Character.name)
            .all()
        )

        for npc in npcs:
            # Build a gem-compatible wrapper.
            # The template expects: id, title,
            # category, images, is_revealed,
            # is_secret, and a URL to link to.
            npc_gems.append(
                {
                    "id": npc.id,
                    "title": npc.name,
                    "category": "NPC",
                    "images": npc.images,
                    "is_revealed": 1,  # NPCs are visible once created
                    "is_secret": 0,
                    "is_npc": True,  # Flag so the template can build the right URL
                    "importance": npc.importance or "minor",
                }
            )

    # --- COMBINE AND SORT ---
    # Build unified lists of revealed and
    # unrevealed items. Each item is either
    # a LoreEntry object or an NPC dict.

    def get_title(item):
        if isinstance(item, dict):
            return item["title"].lower()
        return item.title.lower()

    def is_item_revealed(item):
        if isinstance(item, dict):
            return item["is_revealed"] == 1
        return item.is_revealed == 1

    all_items = list(lore_entries) + npc_gems

    revealed_entries = sorted(
        [e for e in all_items if is_item_revealed(e)], key=get_title
    )
    unrevealed_entries = sorted(
        [e for e in all_items if not is_item_revealed(e)], key=get_title
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

    # Treat secret entries as if they don't exist
    # for non-DM visitors. We return the same
    # "not found" response — never a different
    # error — so players can't tell whether the
    # entry exists at all.
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

    # Update fields
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
async def lore_delete(
    id: int, db: Session = Depends(get_db), _dm: User = Depends(require_dm)
):
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
