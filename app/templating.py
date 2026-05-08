# ============================================
# GODFALL - app/templating.py
# ============================================
# The single, central Jinja2 templates
# instance for the whole application.
#
# Why this file exists:
# Every route file used to create its own
# Jinja2Templates() instance. That meant
# filters registered in main.py weren't
# available in routers. Each instance was
# its own isolated bridge — same blueprint,
# but no shared crew.
#
# Now there's ONE templates object that
# every route imports. Register a filter
# here once, and it works everywhere.
# ============================================

from fastapi.templating import Jinja2Templates
from pathlib import Path
import markdown as md_lib

# Path to the templates folder (one level
# up from this file, then into templates/).
BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


# --- MARKDOWN FILTER ---
def markdown_filter(text):
    if not text:
        return ""
    return md_lib.markdown(
        text,
        extensions=["extra", "nl2br", "sane_lists"]
    )


# --- STRFTIME FILTER ---
def strftime_filter(value, fmt="%B %-d, %Y"):
    if value is None:
        return ""
    return value.strftime(fmt)


# --- REGISTER FILTERS ---
templates.env.filters["markdown"] = markdown_filter
templates.env.filters["strftime"] = strftime_filter