# ============================================
# GODFALL - app/routes/tavern.py
# The Tavern — where adventurers gather
# ============================================
# Player auth routes and (later) the tavern
# thread/message routes.
#
# Like the cantina in Mos Eisley — everyone
# is welcome, but the bartender keeps order.
# ============================================

import bcrypt
from datetime import datetime, timezone
from fastapi import (
    APIRouter,
    Request,
    Depends,
    Form,
)
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.models import Player, Character, User
from app.auth import (
    require_dm,
    get_current_user,
    get_current_player,
    create_player_session,
    PLAYER_COOKIE_NAME,
)
from app.templating import templates

router = APIRouter(
    prefix="/tavern",
    tags=["Tavern"],
)


# ============================================
# PLAYER LOGIN
# ============================================

@router.get("/login")
async def player_login_form(request: Request):
    return templates.TemplateResponse(
        "tavern/login.html",
        {
            "request": request,
            "title": "Player Login — Godfall",
            "error": None,
        }
    )


@router.post("/login")
async def player_login(
    request: Request,
    db: Session = Depends(get_db),
    username: str = Form(...),
    password: str = Form(...),
):
    # Find the player
    player = db.query(Player).filter(
        Player.username == username
    ).first()

    if not player or not player.is_active:
        return templates.TemplateResponse(
            "tavern/login.html",
            {
                "request": request,
                "title": "Player Login — Godfall",
                "error": "Invalid username or password.",
            },
            status_code=401,
        )

    # Verify password
    if not bcrypt.checkpw(
        password.encode("utf-8"),
        player.password_hash.encode("utf-8")
    ):
        return templates.TemplateResponse(
            "tavern/login.html",
            {
                "request": request,
                "title": "Player Login — Godfall",
                "error": "Invalid username or password.",
            },
            status_code=401,
        )

    # Update last login
    player.last_login_at = datetime.now(timezone.utc)
    db.commit()

    # Create session cookie
    response = RedirectResponse(url="/tavern", status_code=303)
    response.set_cookie(
        key=PLAYER_COOKIE_NAME,
        value=create_player_session(player.id),
        httponly=True,
        samesite="lax",
        max_age=60 * 60 * 24 * 30,  # 30 days
    )
    return response


@router.post("/logout")
async def player_logout():
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie(PLAYER_COOKIE_NAME)
    return response


# ============================================
# DM PLAYER MANAGEMENT
# ============================================

@router.get("/players")
async def player_list(
    request: Request,
    db: Session = Depends(get_db),
    _dm: User = Depends(require_dm),
):
    players = db.query(Player).order_by(Player.username).all()

    return templates.TemplateResponse(
        "tavern/players.html",
        {
            "request": request,
            "title": "Player Accounts — Godfall",
            "players": players,
        }
    )


@router.get("/players/new")
async def player_new_form(
    request: Request,
    db: Session = Depends(get_db),
    _dm: User = Depends(require_dm),
):
    characters = (
        db.query(Character)
        .filter(Character.character_type == "player")
        .order_by(Character.name)
        .all()
    )

    return templates.TemplateResponse(
        "tavern/player_form.html",
        {
            "request": request,
            "title": "New Player Account — Godfall",
            "characters": characters,
            "player": None,
            "editing": False,
        }
    )


@router.post("/players/new")
async def player_create(
    request: Request,
    db: Session = Depends(get_db),
    _dm: User = Depends(require_dm),
    username: str = Form(...),
    password: str = Form(...),
    character_id: Optional[int] = Form(None),
):
    # Check for duplicate username
    existing = db.query(Player).filter(
        Player.username == username
    ).first()
    if existing:
        characters = (
            db.query(Character)
            .filter(Character.character_type == "player")
            .order_by(Character.name)
            .all()
        )
        return templates.TemplateResponse(
            "tavern/player_form.html",
            {
                "request": request,
                "title": "New Player Account — Godfall",
                "characters": characters,
                "player": None,
                "editing": False,
                "error": f"Username '{username}' already exists.",
            }
        )

    # Hash password
    password_hash = bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt()
    ).decode("utf-8")

    player = Player(
        username=username,
        password_hash=password_hash,
        character_id=character_id if character_id else None,
    )
    db.add(player)
    db.commit()

    return RedirectResponse(url="/tavern/players", status_code=303)


@router.post("/players/{id}/reset-password")
async def player_reset_password(
    id: int,
    db: Session = Depends(get_db),
    _dm: User = Depends(require_dm),
    new_password: str = Form(...),
):
    player = db.query(Player).filter(Player.id == id).first()
    if not player:
        return HTMLResponse(content="<h1>Player not found</h1>", status_code=404)

    player.password_hash = bcrypt.hashpw(
        new_password.encode("utf-8"),
        bcrypt.gensalt()
    ).decode("utf-8")
    db.commit()

    return RedirectResponse(url="/tavern/players", status_code=303)


@router.post("/players/{id}/toggle-active")
async def player_toggle_active(
    id: int,
    db: Session = Depends(get_db),
    _dm: User = Depends(require_dm),
):
    player = db.query(Player).filter(Player.id == id).first()
    if not player:
        return HTMLResponse(content="<h1>Player not found</h1>", status_code=404)

    player.is_active = 0 if player.is_active == 1 else 1
    db.commit()

    return RedirectResponse(url="/tavern/players", status_code=303)


# ============================================
# TAVERN MAIN (placeholder for Session 2)
# ============================================

@router.get("/")
async def tavern_home(
    request: Request,
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_current_user),
    player: Optional[Player] = Depends(get_current_player),
):
    return templates.TemplateResponse(
        "tavern/list.html",
        {
            "request": request,
            "title": "The Tavern — Godfall",
        }
    )