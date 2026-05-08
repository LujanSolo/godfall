# ============================================
# GODFALL - app/models.py - The Blueprints
# ============================================
# These are the database models — Python
# classes that map directly to database tables.
#
# Think of each class as a blueprint for a
# starship. The blueprint defines what the
# ship HAS (name, hull strength, weapon
# slots). The database stores the actual
# ships built from those blueprints.
#
# Class = blueprint (the structure)
# Row in the database = an actual ship (the data)
# ============================================

# --- IMPORTS ---

# Column: defines a single column in a table.
# Integer, String, Text: the data types for
# those columns (number, short text, long text).
# DateTime: for timestamps.
# ForeignKey: creates a link between tables
# (how CharacterImage knows which Character
# it belongs to).
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    Date,
    ForeignKey,
)

# relationship: tells SQLAlchemy about the
# connection between two models so you can
# navigate between them in Python.
# e.g. character.images gives you all images
# for that character — no raw SQL needed.
from sqlalchemy.orm import relationship

# datetime: Python's built-in date/time tools.
# We use it to auto-stamp when records are
# created or updated.
from datetime import datetime

# Base: the ancestor class we created in
# database.py. Every model inherits from it.
from app.database import Base


# ============================================
# CHARACTER MODEL
# ============================================
# This is the dossier blueprint. Each row in
# the "characters" table represents one member
# of the Godfall party.
#
# In ORM terms:
#   Class name (Character) = the Python object
#   __tablename__ ("characters") = the actual
#       table name in SQLite
#   Each Column = a field in the dossier
# ============================================
class Character(Base):
    __tablename__ = "characters"

    # --- PRIMARY KEY ---
    # Every table needs a unique identifier
    # for each row. "id" auto-increments:
    # first character is 1, second is 2, etc.
    #
    # Like a serial number stamped on each
    # dossier folder. No two are the same.
    id = Column(Integer, primary_key=True, index=True)

    # --- IDENTITY ---
    # nullable=False means this field is
    # REQUIRED — you can't create a character
    # without a name. Like how you can't
    # register a ship without a designation.
    name = Column(String(100), nullable=False)
    player_name = Column(String(100), nullable=True)
    character_type = Column(String(20), default="player", nullable=False)
    # --- IMPORTANCE TIER ---
    # "major"   = recurring, story-significant
    # "minor"   = supporting role
    # "cameo"   = one-off encounter
    #
    # Players default to "major" 
    importance = Column(String(20), default="major", nullable=True)
    race = Column(String(50), nullable=False)
    character_class = Column(String(50), nullable=False)

    # We call it "character_class" instead of
    # "class" because "class" is a reserved
    # keyword in Python — it's how you define
    # classes (like this very model). Using it
    # as a column name would confuse Python.

    level = Column(Integer, default=1)
    age = Column(String(30))

    # --- THE ONE-LINER ---
    # A punchy sentence that captures who
    # this character is. String(255) caps it
    # at 255 characters — enough for a
    # compelling hook, not a novel.
    one_liner = Column(String(255))

    # --- LONGER TEXT FIELDS ---
    # Text type has no length limit (well,
    # SQLite's limit is enormous). Perfect for
    # backstories, item lists, and anything
    # that might run long.
    #
    # Think of String as a label on a crate,
    # and Text as the full cargo manifest
    # inside.
    backstory = Column(Text)
    top_magic_items = Column(Text)
    notable_traits = Column(Text)
    pets_companions = Column(Text)

    # --- STATUS ---
    # Active, Dead, Missing, Unknown...
    # because it's Frostmaiden and no one
    # is safe. Defaults to "Active" because
    # we're optimists. For now.
    status = Column(String(20), default="Active")

    # --- TIMESTAMPS ---
    # Automatically records when the character
    # was first added and last updated.
    #
    # default=datetime.utcnow runs when a
    # record is CREATED.
    # onupdate=datetime.utcnow runs when a
    # record is MODIFIED.
    #
    # Like a ship's log — you always know
    # when something was first recorded and
    # when it was last touched.
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    # --- RELATIONSHIP ---
    # This line doesn't create a column in the
    # database. Instead, it tells SQLAlchemy:
    # "A Character can have many Images. When
    # I access character.images, go find all
    # CharacterImage rows that point to me."
    #
    # back_populates: creates a two-way link.
    # character.images gets the images.
    # image.character gets the character.
    # Two-way comm channel.
    #
    # cascade="all, delete-orphan": if you
    # delete a character, all their images get
    # deleted too. No orphaned records left
    # behind — like the Empire's "no witnesses"
    # policy, but for data hygiene.
    images = relationship(
        "CharacterImage",
        back_populates="character",
        cascade="all, delete-orphan"
    )

    # --- STRING REPRESENTATION ---
    # __repr__ defines what Python prints when
    # you inspect this object in the terminal.
    # Without it, you'd see something useless
    # like <Character object at 0x7f2b3c>.
    # With it, you see <Character: Varka (Ranger 7)>
    #
    # Purely a quality-of-life feature for
    # debugging — like putting name tags on
    # identical-looking droids.
    def __repr__(self):
        return f"<Character: {self.name} ({self.character_class} {self.level})>"


# ============================================
# CHARACTER IMAGE MODEL
# ============================================
# Each row represents one image associated
# with a character. A character can have many
# images — portraits, action shots, pet
# photos, whatever tells their story.
#
# This is the "many" side of the one-to-many
# relationship. The ForeignKey column is the
# link that says "I belong to Character #X."
# ============================================
class CharacterImage(Base):
    __tablename__ = "character_images"

    id = Column(Integer, primary_key=True, index=True)

    # --- THE LINK ---
    # ForeignKey("characters.id") creates the
    # connection to the characters table.
    # It says: "This column holds a character's
    # id number."
    #
    # This is how databases represent
    # relationships. Instead of stuffing
    # multiple images into one character row
    # (messy, limited), each image gets its
    # own row and just remembers which
    # character it belongs to.
    #
    # Like how every X-Wing in a squadron
    # carries its squadron assignment — the
    # squadron roster doesn't try to physically
    # contain the ships.
    character_id = Column(
        Integer,
        ForeignKey("characters.id"),
        nullable=False
    )

    # --- IMAGE DATA ---
    # file_path: where the image file lives
    # on disk (e.g. "/static/uploads/characters/varka_portrait.jpg")
    file_path = Column(String(255), nullable=False)

    # caption: optional description of the
    # image (e.g. "Varka after the battle of
    # Bryn Shander" or "Frost the arctic fox")
    caption = Column(String(255))

    # is_primary: marks one image as the main
    # portrait shown on the character card in
    # the roster view. Only one image per
    # character should be primary.
    is_primary = Column(Integer, default=0)

    # --- TIMESTAMP ---
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    # --- RELATIONSHIP (back-link) ---
    # The other half of the two-way channel.
    # image.character gets the Character
    # object this image belongs to.
    character = relationship(
        "Character",
        back_populates="images"
    )

    def __repr__(self):
        return f"<CharacterImage: {self.caption or 'No caption'} (Character #{self.character_id})>"
    

# ============================================
# SESSION RECAP MODEL
# ============================================
# Each row represents one session of the
# Godfall campaign. The DM writes these to
# create a running narrative of the
# adventure.
#
# Same pattern as Character: an "owner" model
# that has a one-to-many relationship with
# its associated images.
# ============================================
class SessionRecap(Base):
    __tablename__ = "session_recaps"

    id = Column(Integer, primary_key=True, index=True)

    # --- SESSION NUMBER ---
    # The numeric position in the campaign
    # (Session 1, Session 2, etc).
    #
    # We're letting this be manually entered
    # rather than auto-incrementing, which
    # gives flexibility for retroactive
    # additions or skipped sessions. Like a
    # ship's log where the captain decides
    # what counts as an entry.
    session_number = Column(Integer, nullable=False)

    # --- TITLE ---
    # A short, evocative title for the session.
    # e.g. "The Black Cabin" or "Auril's Wrath"
    title = Column(String(200), nullable=False)

    # --- DATES ---
    # real_date: when the session was actually
    # played. Stored as a proper Date type
    # (no time component, just the day).
    #
    # in_game_date: the date in the world.
    # Stored as a string because fantasy
    # calendars (Hammer 12, 1489 DR) don't fit
    # any standard date format. Trying to
    # squeeze a Forgotten Realms date into a
    # PostgreSQL Date column is like trying
    # to fly a starship into a swamp — wrong
    # tool, wrong terrain.
    real_date = Column(Date)
    in_game_date = Column(String(100))

    # --- CONTENT ---
    # summary: short bullet-point recap shown
    # on the adventure log feed. Keep it
    # punchy — the headline version.
    #
    # body: long-form narrative. This is where
    # markdown formatting lives — headers,
    # bold, italics, lists, etc.
    summary = Column(Text)
    body = Column(Text)

    # --- TIMESTAMPS ---
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    # --- RELATIONSHIP ---
    # Same one-to-many pattern as Character.
    # One session has many images. Delete the
    # session, the images go with it.
    images = relationship(
        "SessionImage",
        back_populates="session",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<SessionRecap #{self.session_number}: {self.title}>"


# ============================================
# SESSION IMAGE MODEL
# ============================================
# Identical structure to CharacterImage,
# just pointed at a different parent.
#
# is_featured: marks the "hero" image shown
# on the adventure log list view. Same
# concept as is_primary for character images,
# different name because the visual purpose
# differs (a character HAS a portrait, a
# session HAS a featured image — different
# semantic flavor).
# ============================================
class SessionImage(Base):
    __tablename__ = "session_images"

    id = Column(Integer, primary_key=True, index=True)

    session_id = Column(
        Integer,
        ForeignKey("session_recaps.id"),
        nullable=False
    )

    file_path = Column(String(255), nullable=False)
    caption = Column(String(255))
    is_featured = Column(Integer, default=0)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    session = relationship(
        "SessionRecap",
        back_populates="images"
    )

    def __repr__(self):
        return f"<SessionImage: {self.caption or 'No caption'} (Session #{self.session_id})>"