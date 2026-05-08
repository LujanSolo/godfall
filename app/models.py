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
    player_name = Column(String(100), nullable=False)
    race = Column(String(50), nullable=False)
    character_class = Column(String(50), nullable=False)

    # We call it "character_class" instead of
    # "class" because "class" is a reserved
    # keyword in Python — it's how you define
    # classes (like this very model). Using it
    # as a column name would confuse Python.
    # Like naming your pet Wookiee "Chewbacca"
    # when there's already a Chewbacca on the
    # ship — things get confusing fast.

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