# ============================================
# GODFALL - app/routes/map.py
# Map Mission Control
# ============================================
# Two routes:
#
#   1. The full map page itself (/map)
#   2. The HTMX hover preview endpoint
#      (/map/pin/{id}/preview)
#
# The map page queries all Location-type
# lore entries with coordinates set, then
# the template renders each one as a pin
# at its lat/lng position.
# ============================================

from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from app.auth import require_dm, get_current_user
from app.database import get_db
from app.models import LoreEntry, User
from app.templating import templates
from typing import Optional

# --- CREATE THE ROUTER ---
router = APIRouter(
    prefix="/map",
    tags=["Map"],
)


# ============================================
# ROUTE: MAP PAGE
# GET /map
# ============================================
# Renders the full-bleed map with pins for
# every Location-type lore entry that has
# coordinates set.
#
# Note the filter: we want entries that ARE
# locations AND have BOTH lat and lng set.
# Entries without coordinates don't appear
# on the map (they may exist but haven't
# been pinned yet).
# ============================================
@router.get("/")
async def map_view(
    request: Request,
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_current_user),
):
    query = (
        db.query(LoreEntry)
        .filter(LoreEntry.category == "Location")
        .filter(LoreEntry.lat.is_not(None))
        .filter(LoreEntry.lng.is_not(None))
    )

    # Hide secret-pinned locations from non-DM visitors
    if user is None or user.role != "dm":
        query = query.filter(LoreEntry.is_secret == 0)

    pins = query.all()

    return templates.TemplateResponse(
        "map/view.html",
        {
            "request": request,
            "title": "World Map — Godfall",
            "pins": pins,
        },
    )


# ============================================
# ROUTE: PIN HOVER PREVIEW (HTMX)
# GET /map/pin/{id}/preview
# ============================================
# Same pattern as the timeline preview.
# Returns just the tooltip HTML fragment
# when HTMX requests it during pin hover.
# ============================================
@router.get("/pin/{id}/preview")
async def pin_preview(
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
        return HTMLResponse(content="", status_code=404)

    return templates.TemplateResponse(
        "map/_pin_preview.html",
        {
            "request": request,
            "entry": entry,
        },
    )
