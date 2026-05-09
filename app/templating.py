# ============================================
# GODFALL - app/templating.py
# ============================================
# The single, central Jinja2 templates
# instance for the whole application.
#
# Why this file exists:
# Every route file used to create its own
# Jinja2Templates() instance, which meant
# filters registered in main.py weren't
# available in routers. Now there's ONE
# templates object that every route imports.
#
# This file also defines our custom filters
# and a context-processor mechanism for
# making variables available to ALL templates
# without explicitly passing them per-route.
# ============================================

from fastapi.templating import Jinja2Templates
from pathlib import Path
import markdown as md_lib

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