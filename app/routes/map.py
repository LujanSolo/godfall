# ============================================
# GODFALL - app/routes/map.py
# Map Mission Control — Leaflet Edition
# ============================================
# Two routes:
#   1. The world map page (/map)
#   2. Town-level maps (/map/{slug})
#
# Like the tactical display on the bridge
# of a Star Destroyer — zooming from the
# full sector view down to individual
# planetary surfaces.
# ============================================

import json
import re
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.models import LoreEntry, User
from app.auth import get_current_user
from app.templating import templates

router = APIRouter(
    prefix="/map",
    tags=["Map"],
)

# World map image dimensions (pixels)
WORLD_MAP_WIDTH = 1500
WORLD_MAP_HEIGHT = 1054


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

    if user is None or user.role != "dm":
        query = query.filter(LoreEntry.is_secret == 0)

    pins = query.all()

    # Build a JSON-serializable list of pin data
    # for Leaflet to consume on the client side.
    pin_data = []
    for pin in pins:
        # Find featured image
        featured = None
        for img in pin.images:
            if img.is_featured == 1:
                featured = img
                break
        if featured is None and pin.images:
            featured = pin.images[0]

        pin_data.append({
            "id": pin.id,
            "title": pin.title,
            "subtitle": pin.subtitle or "",
            "category": pin.category,
            "lat": pin.lat,
            "lng": pin.lng,
            "body_preview": re.sub(r'[#*>\-_`\[\]]', '', (pin.body or "")[:200]).replace("\n", " ").strip(),
            "image": featured.file_path if featured else None,
            "url": f"/lore/{pin.id}",
            "has_town_map": bool(pin.town_map_image) if hasattr(pin, 'town_map_image') and pin.town_map_image else False,
        })

    return templates.TemplateResponse(
        "map/view.html",
        {
            "request": request,
            "title": "World Map — Godfall",
            "pins_json": json.dumps(pin_data),
            "map_width": WORLD_MAP_WIDTH,
            "map_height": WORLD_MAP_HEIGHT,
        }
    )