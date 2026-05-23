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
from app.models import (
    Player,
    Character,
    User,
    TavernThread,
    TavernMessage,
    SessionRecap,
    LoreEntry,
)
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
        },
    )


@router.post("/login")
async def player_login(
    request: Request,
    db: Session = Depends(get_db),
    username: str = Form(...),
    password: str = Form(...),
):
    # Find the player
    player = db.query(Player).filter(Player.username == username).first()

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
        password.encode("utf-8"), player.password_hash.encode("utf-8")
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
        },
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
        },
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
    existing = db.query(Player).filter(Player.username == username).first()
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
            },
        )

    # Hash password
    password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode(
        "utf-8"
    )

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
        new_password.encode("utf-8"), bcrypt.gensalt()
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
# TAVERN — THREAD LIST
# ============================================


@router.get("/")
async def tavern_home(
    request: Request,
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_current_user),
    player: Optional[Player] = Depends(get_current_player),
):
    # Pinned threads first, then by most recent activity
    threads = (
        db.query(TavernThread)
        .order_by(TavernThread.is_pinned.desc(), TavernThread.updated_at.desc())
        .all()
    )

    # Get the last message and message count for each thread
    thread_data = []
    for thread in threads:
        message_count = (
            db.query(TavernMessage).filter(TavernMessage.thread_id == thread.id).count()
        )
        last_message = (
            db.query(TavernMessage)
            .filter(TavernMessage.thread_id == thread.id)
            .order_by(TavernMessage.created_at.desc())
            .first()
        )
        thread_data.append(
            {
                "thread": thread,
                "message_count": message_count,
                "last_message": last_message,
            }
        )

    return templates.TemplateResponse(
        "tavern/list.html",
        {
            "request": request,
            "title": "The Tavern — Godfall",
            "thread_data": thread_data,
        },
    )


# ============================================
# TAVERN — NEW THREAD FORM
# ============================================


@router.get("/new")
async def tavern_new_thread_form(
    request: Request,
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_current_user),
    player: Optional[Player] = Depends(get_current_player),
):
    if not user and not player:
        return RedirectResponse(url="/tavern/login", status_code=303)

    sessions = db.query(SessionRecap).order_by(SessionRecap.session_number.desc()).all()
    lore_entries = db.query(LoreEntry).order_by(LoreEntry.title).all()
    characters = (
        db.query(Character)
        .filter(Character.character_type == "player")
        .order_by(Character.name)
        .all()
    )

    return templates.TemplateResponse(
        "tavern/new_thread.html",
        {
            "request": request,
            "title": "New Thread — The Tavern",
            "sessions": sessions,
            "lore_entries": lore_entries,
            "characters": characters,
        },
    )


# ============================================
# TAVERN — CREATE THREAD
# ============================================


@router.post("/new")
async def tavern_create_thread(
    request: Request,
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_current_user),
    player: Optional[Player] = Depends(get_current_player),
    title: str = Form(...),
    body: str = Form(...),
    is_ic: int = Form(0),
    npc_name: Optional[str] = Form(None),
    linked_session_id: Optional[int] = Form(None),
    linked_lore_id: Optional[int] = Form(None),
    linked_character_id: Optional[int] = Form(None),
):
    if not user and not player:
        return RedirectResponse(url="/tavern/login", status_code=303)

    from datetime import datetime, timezone

    now = datetime.now(timezone.utc)

    thread = TavernThread(
        title=title,
        created_by_id=player.id if player else None,
        created_by_dm=1 if user else 0,
        linked_session_id=linked_session_id if linked_session_id else None,
        linked_lore_id=linked_lore_id if linked_lore_id else None,
        linked_character_id=linked_character_id if linked_character_id else None,
        created_at=now,
        updated_at=now,
    )
    db.add(thread)
    db.commit()
    db.refresh(thread)

    # Create the first message
    message = TavernMessage(
        thread_id=thread.id,
        posted_by_id=player.id if player else None,
        posted_by_dm=1 if user else 0,
        is_ic=is_ic,
        npc_name=npc_name if (user and is_ic) else None,
        body=body,
        created_at=now,
    )
    db.add(message)
    db.commit()

    return RedirectResponse(url=f"/tavern/{thread.id}", status_code=303)


# ============================================
# TAVERN — VIEW THREAD
# ============================================


@router.get("/{id}")
async def tavern_thread(
    request: Request,
    id: int,
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_current_user),
    player: Optional[Player] = Depends(get_current_player),
):
    thread = db.query(TavernThread).filter(TavernThread.id == id).first()
    if not thread:
        return HTMLResponse(
            content="<h1>Thread not found</h1>",
            status_code=404,
        )

    messages = (
        db.query(TavernMessage)
        .filter(TavernMessage.thread_id == id)
        .order_by(TavernMessage.created_at)
        .all()
    )

    return templates.TemplateResponse(
        "tavern/thread.html",
        {
            "request": request,
            "title": f"{thread.title} — The Tavern",
            "thread": thread,
            "messages": messages,
        },
    )


# ============================================
# TAVERN — POST REPLY
# ============================================


@router.post("/{id}/reply")
async def tavern_reply(
    request: Request,
    id: int,
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_current_user),
    player: Optional[Player] = Depends(get_current_player),
    body: str = Form(...),
    is_ic: int = Form(0),
    npc_name: Optional[str] = Form(None),
):
    if not user and not player:
        return RedirectResponse(url="/tavern/login", status_code=303)

    thread = db.query(TavernThread).filter(TavernThread.id == id).first()
    if not thread:
        return HTMLResponse(content="<h1>Thread not found</h1>", status_code=404)

    if thread.is_locked == 1 and not user:
        return RedirectResponse(url=f"/tavern/{id}", status_code=303)

    from datetime import datetime, timezone

    now = datetime.now(timezone.utc)

    message = TavernMessage(
        thread_id=id,
        posted_by_id=player.id if player else None,
        posted_by_dm=1 if user else 0,
        is_ic=is_ic,
        npc_name=npc_name if (user and is_ic) else None,
        body=body,
        created_at=now,
    )
    db.add(message)

    # Bump thread activity
    thread.updated_at = now
    db.commit()

    return RedirectResponse(url=f"/tavern/{id}", status_code=303)


# ============================================
# TAVERN — EDIT MESSAGE
# ============================================


@router.post("/message/{id}/edit")
async def tavern_edit_message(
    request: Request,
    id: int,
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_current_user),
    player: Optional[Player] = Depends(get_current_player),
    body: str = Form(...),
):
    message = db.query(TavernMessage).filter(TavernMessage.id == id).first()
    if not message:
        return HTMLResponse(content="<h1>Message not found</h1>", status_code=404)

    # Only the author or the DM can edit
    can_edit = False
    if user:
        can_edit = True
    elif player and message.posted_by_id == player.id:
        can_edit = True

    if not can_edit:
        return RedirectResponse(url=f"/tavern/{message.thread_id}", status_code=303)

    from datetime import datetime, timezone

    message.body = body
    message.edited_at = datetime.now(timezone.utc)
    db.commit()

    return RedirectResponse(url=f"/tavern/{message.thread_id}", status_code=303)


# ============================================
# TAVERN — DELETE MESSAGE (DM only)
# ============================================


@router.post("/message/{id}/delete")
async def tavern_delete_message(
    id: int,
    db: Session = Depends(get_db),
    _dm: User = Depends(require_dm),
):
    message = db.query(TavernMessage).filter(TavernMessage.id == id).first()
    if not message:
        return HTMLResponse(content="<h1>Message not found</h1>", status_code=404)

    thread_id = message.thread_id
    db.delete(message)
    db.commit()

    return RedirectResponse(url=f"/tavern/{thread_id}", status_code=303)


# ============================================
# TAVERN — LOCK/UNLOCK THREAD (DM only)
# ============================================


@router.post("/{id}/lock")
async def tavern_toggle_lock(
    id: int,
    db: Session = Depends(get_db),
    _dm: User = Depends(require_dm),
):
    thread = db.query(TavernThread).filter(TavernThread.id == id).first()
    if not thread:
        return HTMLResponse(content="<h1>Thread not found</h1>", status_code=404)

    thread.is_locked = 0 if thread.is_locked == 1 else 1
    db.commit()

    return RedirectResponse(url=f"/tavern/{id}", status_code=303)


# ============================================
# TAVERN — PIN/UNPIN THREAD (DM only)
# ============================================


@router.post("/{id}/pin")
async def tavern_toggle_pin(
    id: int,
    db: Session = Depends(get_db),
    _dm: User = Depends(require_dm),
):
    thread = db.query(TavernThread).filter(TavernThread.id == id).first()
    if not thread:
        return HTMLResponse(content="<h1>Thread not found</h1>", status_code=404)

    thread.is_pinned = 0 if thread.is_pinned == 1 else 1
    db.commit()

    return RedirectResponse(url=f"/tavern/{id}", status_code=303)


# ============================================
# TAVERN — DELETE THREAD (DM only)
# ============================================


@router.post("/{id}/delete")
async def tavern_delete_thread(
    id: int,
    db: Session = Depends(get_db),
    _dm: User = Depends(require_dm),
):
    thread = db.query(TavernThread).filter(TavernThread.id == id).first()
    if not thread:
        return HTMLResponse(content="<h1>Thread not found</h1>", status_code=404)

    db.delete(thread)
    db.commit()

    return RedirectResponse(url="/tavern", status_code=303)
