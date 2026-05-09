# ============================================
# GODFALL - app/routes/sessions.py
# Adventure Log Mission Control
# ============================================
# Routes for the session recaps. Same CRUD
# pattern as characters.py — view list, view
# detail, create, edit, delete, image upload.
#
# If characters.py was the first run down the
# trench, this is the second pass with a
# better feel for the controls.
# ============================================

# --- IMPORTS ---
from app.auth import require_dm
from fastapi import (
    APIRouter,
    Request,
    Depends,
    Form,
    UploadFile,
    File,
)
from fastapi.responses import RedirectResponse, HTMLResponse
from app.templating import templates
from sqlalchemy.orm import Session

from pathlib import Path
from datetime import date, datetime
from typing import List, Optional
import shutil
import uuid

from app.database import get_db
from app.models import SessionRecap, SessionImage, User
from app.templating import templates

# --- CONFIGURATION ---
BASE_DIR = Path(__file__).resolve().parent.parent

# Different upload folder than characters —
# keeps things organized. session images go
# in their own bin so we never get them mixed
# up with character portraits.
UPLOAD_DIR = BASE_DIR / "static" / "uploads" / "sessions"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# --- CREATE THE ROUTER ---
router = APIRouter(
    prefix="/sessions",
    tags=["Sessions"],
)


# ============================================
# HELPER: PARSE DATE
# ============================================
# HTML date inputs send their value as a
# string in YYYY-MM-DD format. Python wants
# a real date object. This converts between
# the two, returning None if the string is
# empty or malformed.
#
# Like a translator droid for dates — takes
# what the form gives us and converts it to
# the format Python understands.
# ============================================
def parse_date(date_str: Optional[str]) -> Optional[date]:
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None


# ============================================
# ROUTE: LIST ALL SESSIONS
# GET /sessions
# ============================================
# The adventure log feed. Sorted by session
# number descending (newest first).
#
# .desc() reverses the sort. Without it,
# Session 1 would be at the top — but in a
# campaign feed, you typically want the most
# recent at the top.
# ============================================
@router.get("/")
async def session_list(
    request: Request,
    db: Session = Depends(get_db)
):
    sessions = (
        db.query(SessionRecap)
        .order_by(SessionRecap.session_number.desc())
        .all()
    )

    return templates.TemplateResponse(
        "sessions/list.html",
        {
            "request": request,
            "title": "Adventure Log — Godfall",
            "sessions": sessions,
        }
    )


# ============================================
# ROUTE: NEW SESSION FORM
# GET /sessions/new
# ============================================
# Same "named route before parameter route"
# rule as characters — /new MUST come before
# /{id} or FastAPI gets confused.
# ============================================
@router.get("/new")
async def session_new_form(
    request: Request,
    db: Session = Depends(get_db),
    _dm: User = Depends(require_dm)
):
    # Suggest the next session number based on
    # what's already in the database. Convenience
    # for the DM — no need to count manually.
    last_session = (
        db.query(SessionRecap)
        .order_by(SessionRecap.session_number.desc())
        .first()
    )
    next_number = (last_session.session_number + 1) if last_session else 1

    return templates.TemplateResponse(
        "sessions/form.html",
        {
            "request": request,
            "title": "New Session — Godfall",
            "session": None,
            "editing": False,
            "suggested_number": next_number,
        }
    )


# ============================================
# ROUTE: CREATE NEW SESSION
# POST /sessions/new
# ============================================
@router.post("/new")
async def session_create(
    request: Request,
    db: Session = Depends(get_db),
    _dm: User = Depends(require_dm),
    session_number: int = Form(...),
    title: str = Form(...),
    real_date: Optional[str] = Form(None),
    in_game_date: Optional[str] = Form(None),
    summary: Optional[str] = Form(None),
    body: Optional[str] = Form(None),
):
    new_session = SessionRecap(
        session_number=session_number,
        title=title,
        real_date=parse_date(real_date),
        in_game_date=in_game_date,
        summary=summary,
        body=body,
    )

    db.add(new_session)
    db.commit()
    db.refresh(new_session)

    return RedirectResponse(
        url=f"/sessions/{new_session.id}",
        status_code=303
    )


# ============================================
# ROUTE: VIEW ONE SESSION
# GET /sessions/{id}
# ============================================
@router.get("/{id}")
async def session_detail(
    request: Request,
    id: int,
    db: Session = Depends(get_db)
):
    session_recap = (
        db.query(SessionRecap)
        .filter(SessionRecap.id == id)
        .first()
    )

    if not session_recap:
        return HTMLResponse(
            content="<h1>Session not found</h1>"
                    "<p>This entry doesn't exist in "
                    "the adventure log.</p>",
            status_code=404
        )

    return templates.TemplateResponse(
        "sessions/detail.html",
        {
            "request": request,
            "title": f"Session {session_recap.session_number}: {session_recap.title} — Godfall",
            "session": session_recap,
        }
    )


# ============================================
# ROUTE: EDIT SESSION FORM
# GET /sessions/{id}/edit
# ============================================
@router.get("/{id}/edit")
async def session_edit_form(
    request: Request,
    id: int,
    db: Session = Depends(get_db),
    _dm: User = Depends(require_dm)
):
    session_recap = (
        db.query(SessionRecap)
        .filter(SessionRecap.id == id)
        .first()
    )

    if not session_recap:
        return HTMLResponse(
            content="<h1>Session not found</h1>",
            status_code=404
        )

    return templates.TemplateResponse(
        "sessions/form.html",
        {
            "request": request,
            "title": f"Edit Session {session_recap.session_number} — Godfall",
            "session": session_recap,
            "editing": True,
            "suggested_number": session_recap.session_number,
        }
    )


# ============================================
# ROUTE: UPDATE SESSION
# POST /sessions/{id}/edit
# ============================================
@router.post("/{id}/edit")
async def session_update(
    request: Request,
    id: int,
    db: Session = Depends(get_db),
    _dm: User = Depends(require_dm),
    session_number: int = Form(...),
    title: str = Form(...),
    real_date: Optional[str] = Form(None),
    in_game_date: Optional[str] = Form(None),
    summary: Optional[str] = Form(None),
    body: Optional[str] = Form(None),
):
    session_recap = (
        db.query(SessionRecap)
        .filter(SessionRecap.id == id)
        .first()
    )

    if not session_recap:
        return HTMLResponse(
            content="<h1>Session not found</h1>",
            status_code=404
        )

    session_recap.session_number = session_number
    session_recap.title = title
    session_recap.real_date = parse_date(real_date)
    session_recap.in_game_date = in_game_date
    session_recap.summary = summary
    session_recap.body = body

    db.commit()

    return RedirectResponse(
        url=f"/sessions/{session_recap.id}",
        status_code=303
    )


# ============================================
# ROUTE: DELETE SESSION
# POST /sessions/{id}/delete
# ============================================
@router.post("/{id}/delete")
async def session_delete(
    id: int,
    db: Session = Depends(get_db),
    _dm: User = Depends(require_dm)
):
    session_recap = (
        db.query(SessionRecap)
        .filter(SessionRecap.id == id)
        .first()
    )

    if not session_recap:
        return HTMLResponse(
            content="<h1>Session not found</h1>",
            status_code=404
        )

    # Delete image files from disk first.
    for image in session_recap.images:
        file_path = BASE_DIR / image.file_path.lstrip("/")
        if file_path.exists():
            file_path.unlink()

    db.delete(session_recap)
    db.commit()

    return RedirectResponse(
        url="/sessions",
        status_code=303
    )


# ============================================
# ROUTE: UPLOAD IMAGES
# POST /sessions/{id}/upload
# ============================================
@router.post("/{id}/upload")
async def session_upload_images(
    id: int,
    db: Session = Depends(get_db),
    _dm: User = Depends(require_dm),
    files: List[UploadFile] = File(...),
    caption: Optional[str] = Form(None),
    is_featured: int = Form(0),
):
    session_recap = (
        db.query(SessionRecap)
        .filter(SessionRecap.id == id)
        .first()
    )

    if not session_recap:
        return HTMLResponse(
            content="<h1>Session not found</h1>",
            status_code=404
        )

    for uploaded_file in files:
        unique_name = f"{uuid.uuid4().hex}_{uploaded_file.filename}"
        file_path = UPLOAD_DIR / unique_name

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(uploaded_file.file, buffer)

        # If this is marked as featured, unset
        # any existing featured image for this
        # session first.
        if is_featured:
            db.query(SessionImage).filter(
                SessionImage.session_id == session_recap.id,
                SessionImage.is_featured == 1
            ).update({"is_featured": 0})

        image_record = SessionImage(
            session_id=session_recap.id,
            file_path=f"/static/uploads/sessions/{unique_name}",
            caption=caption,
            is_featured=is_featured,
        )

        db.add(image_record)

    db.commit()

    return RedirectResponse(
        url=f"/sessions/{session_recap.id}",
        status_code=303
    )


# ============================================
# ROUTE: DELETE A SINGLE IMAGE
# POST /sessions/{id}/images/{image_id}/delete
# ============================================
@router.post("/{id}/images/{image_id}/delete")
async def session_image_delete(
    id: int,
    image_id: int,
    db: Session = Depends(get_db),
    _dm: User = Depends(require_dm)
):
    image = (
        db.query(SessionImage)
        .filter(
            SessionImage.id == image_id,
            SessionImage.session_id == id,
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
        url=f"/sessions/{id}",
        status_code=303
    )