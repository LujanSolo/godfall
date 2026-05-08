# ============================================
# GODFALL - app/database.py - The Vault
# ============================================
# This file establishes the connection between
# our Python application and the SQLite
# database where all our data lives.
#
# Think of it as the door to the vault —
# it doesn't store anything itself, but
# nothing gets in or out without it.
# ============================================

# --- IMPORTS ---

# create_engine: builds the connection to the
# database. It's the key to the vault door.
#
# "Engine" is SQLAlchemy's term for the object
# that manages the actual database connection.
# You create it once, and every database
# operation flows through it.
from sqlalchemy import create_engine

# declarative_base: creates a base class that
# all our database models will inherit from.
# Every table in our database (Characters,
# CharacterImages, etc.) will be a Python
# class that extends this base.
#
# It's like the midi-chlorians of our data
# layer — it's what gives our Python classes
# the ability to talk to the database.
from sqlalchemy.orm import declarative_base

# sessionmaker: creates a factory for database
# sessions. A "session" is a conversation with
# the database — you open one, do your work
# (read, write, update, delete), and close it.
#
# Like opening a comm channel: you establish
# the connection, transmit your orders, and
# close the channel when you're done.
from sqlalchemy.orm import sessionmaker

# Path: for building file paths cleanly.
from pathlib import Path

# --- DATABASE CONFIGURATION ---

# Figure out where the project root is.
# We go up one level from app/ to godfall/
# so the database file lives at the project
# root, not buried inside app/.
BASE_DIR = Path(__file__).resolve().parent.parent

# The database URL tells SQLAlchemy:
# - What type of database (sqlite)
# - Where to find it (a file called godfall.db
#   in the project root)
#
# The three slashes in "sqlite:///" are not a
# typo — two are part of the protocol, the
# third starts the file path. It's a quirk
# of the SQLite connection string format.
# Just accept it, like the Kessel Run being
# measured in parsecs.
DATABASE_URL = f"sqlite:///{BASE_DIR / 'godfall.db'}"

# --- CREATE THE ENGINE ---
# This builds the connection to our database.
#
# connect_args={"check_same_thread": False}
# is SQLite-specific. By default, SQLite only
# allows the thread that created it to use it.
# Since FastAPI is async and may handle
# requests on different threads, we need to
# disable that restriction.
#
# echo=False means SQLAlchemy won't print
# every SQL query to the terminal. Set it to
# True if you ever want to see exactly what
# SQL is being generated — useful for
# debugging, like switching on thermal vision.
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False
)

# --- CREATE THE SESSION FACTORY ---
# sessionmaker creates a reusable factory.
# Every time we need to talk to the database,
# we'll call SessionLocal() to open a new
# session (comm channel).
#
# autocommit=False: changes don't save until
# we explicitly say so. Like drafting a
# message before hitting send — you can
# review and cancel if something's wrong.
#
# autoflush=False: SQLAlchemy won't
# automatically push pending changes to the
# database. We control when that happens.
# Manual controls, not autopilot.
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# --- CREATE THE BASE CLASS ---
# This is the ancestor class for all our
# database models. When we define Character
# or CharacterImage in models.py, they'll
# inherit from this Base class, which gives
# them all the SQLAlchemy superpowers needed
# to map to database tables.
Base = declarative_base()


# --- DEPENDENCY: GET A DATABASE SESSION ---
# This is a Python generator function (note
# the "yield" keyword instead of "return").
#
# Generators are special functions that can
# pause and resume. Here's how this one works:
#
# 1. Someone requests a database session
# 2. We create one with SessionLocal()
# 3. We "yield" it — hand it over for use
#    while the function pauses
# 4. When the work is done (or if an error
#    occurs), the "finally" block runs and
#    closes the session
#
# This pattern guarantees the session ALWAYS
# gets closed, even if something crashes.
# Like an airlock that auto-seals — you never
# leave it hanging open, no matter what
# emergency is happening inside the ship.
#
# FastAPI uses this as a "dependency" — we'll
# inject it into our route functions so they
# automatically get a fresh session for each
# request.
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()