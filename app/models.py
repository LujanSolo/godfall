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
    Float,
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
from datetime import datetime, timezone

# Base: the ancestor class we created in
# database.py. Every model inherits from it.
from app.database import Base


# ============================================
# TIMEZONE-AWARE NOW
# ============================================
# utc_now() is deprecated as of
# Python 3.12 because it returns a "naive"
# datetime with no timezone info. The modern
# pattern is datetime.now(timezone.utc),
# which returns the same UTC time but with
# its timezone explicitly attached.
#
# We wrap it in a tiny helper so we can pass
# it as a default to Column() — SQLAlchemy
# expects a callable (a function reference),
# not a value, when using "default=" with
# something that should be evaluated each
# time a row is created.
#
# Like setting a clock that's always honest
# about which time zone it's reading from.
# ============================================
def utc_now():
    return datetime.now(timezone.utc)


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
    character_subclass = Column(String(100))

    # We call it "character_class" instead of
    # "class" because "class" is a reserved
    # keyword in Python — it's how you define
    # classes (like this very model). Using it
    # as a column name would confuse Python.

    level = Column(Integer, default=1)
    level_display = Column(String(50))
    age = Column(String(30))

    # --- MULTICLASS & COMBAT STATS ---
    # class_detail is a free-text field for
    # multiclass breakdowns: "Ranger 5 / Rogue 2".
    # Displayed alongside the total level.
    class_detail = Column(String(100))

    # Quick-glance combat stats. These are the
    # numbers a player checks most often during
    # play. Nullable because not every field
    # applies to every character (spell_dc is
    # irrelevant for non-casters).
    armor_class = Column(Integer)
    proficiency_bonus = Column(Integer)
    spell_dc = Column(Integer)
    hit_points = Column(Integer)
    speed = Column(String(50))
    initiative_bonus = Column(Integer)

    # --- OUT-OF-COMBAT REFERENCE ---
    # The passives a DM checks without asking
    # for a roll. Like having a sensor array
    # that's always running in the background.
    passive_perception = Column(Integer)
    passive_investigation = Column(Integer)
    passive_insight = Column(Integer)

    # Inspiration — binary toggle.
    has_inspiration = Column(Integer, default=0)

    # Languages and senses stored as JSON strings.
    # Each is a list of objects:
    #   languages: ["Common", "Elvish", "Dwarvish"]
    #   senses: [{"name": "Darkvision", "detail": "120 ft."},
    #            {"name": "Blindsight", "detail": "10 ft."}]
    languages = Column(Text)
    senses = Column(Text)
    resistances = Column(Text)

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
    # default=utc_now runs when a
    # record is CREATED.
    # onupdate=utc_now runs when a
    # record is MODIFIED.
    #
    # Like a ship's log — you always know
    # when something was first recorded and
    # when it was last touched.
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

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
        "CharacterImage", back_populates="character", cascade="all, delete-orphan"
    )

    # --- LORE BACK-REFERENCE ---
    # This is the OTHER side of the LoreCharacter
    # join table relationship.
    #
    # In Phase 5a, we set up LoreEntry.character_links
    # so a lore entry could navigate to its
    # linked characters. The connection is
    # inherently two-way — same join table — but
    # SQLAlchemy needs both ends declared
    # explicitly so it knows how to traverse
    # them in Python.
    #
    # Now we can write character.lore_links and
    # get all the LoreCharacter rows pointing to
    # this character. From there, link.lore_entry
    # gets us the actual lore entry.
    #
    # No new database table. No new data. Just a
    # new way to look at what's already there.
    # Like turning the holocron over and reading
    # the reflection on the other side.
    lore_links = relationship("LoreCharacter", back_populates="character")

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
    character_id = Column(Integer, ForeignKey("characters.id"), nullable=False)

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
    uploaded_at = Column(DateTime, default=utc_now)

    # --- RELATIONSHIP (back-link) ---
    # The other half of the two-way channel.
    # image.character gets the Character
    # object this image belongs to.
    character = relationship("Character", back_populates="images")

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
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    # --- RELATIONSHIP ---
    # Same one-to-many pattern as Character.
    # One session has many images. Delete the
    # session, the images go with it.
    images = relationship(
        "SessionImage", back_populates="session", cascade="all, delete-orphan"
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

    session_id = Column(Integer, ForeignKey("session_recaps.id"), nullable=False)

    file_path = Column(String(255), nullable=False)
    caption = Column(String(255))
    is_featured = Column(Integer, default=0)
    uploaded_at = Column(DateTime, default=utc_now)

    session = relationship("SessionRecap", back_populates="images")

    def __repr__(self):
        return f"<SessionImage: {self.caption or 'No caption'} (Session #{self.session_id})>"


# ============================================
# TIMELINE EVENT MODEL
# ============================================
# Major story beats from the campaign.
# Each event becomes a node on the timeline.
#
# Distinct from SessionRecap because:
#   - A single session might cover multiple
#     events (or zero, if the party shopped
#     all night).
#   - An event might span several sessions
#     (a long siege, an ongoing investigation).
#   - The timeline is curated narrative; the
#     adventure log is chronological play.
#
# Like the difference between a movie's
# IMDb trivia page (events) and the actual
# shooting schedule (sessions).
# ============================================
class TimelineEvent(Base):
    __tablename__ = "timeline_events"

    id = Column(Integer, primary_key=True, index=True)

    # --- TITLE ---
    # Evocative event name. e.g. "The Black
    # Cabin Incident" or "Auril Revealed."
    title = Column(String(200), nullable=False)

    # --- IN-GAME DATE ---
    # Same string-based approach as session
    # in_game_date — fantasy calendars don't
    # fit standard date types.
    event_date = Column(String(100))

    # --- OPTIONAL END DATE ---
    # For multi-day events. If left empty, the
    # event is treated as a single point in time.
    # When set, the detail and timeline render
    # the event as a span (e.g. "Hammer 12-18").
    #
    # Like a stardate range vs. a single stardate.
    # Some missions take a day. Some take a week.
    event_end_date = Column(String(100))

    # --- SORT ORDER ---
    # Integer that controls the timeline's
    # left-to-right ordering. We use this
    # instead of date because:
    #   1. In-game date strings can't sort
    #      reliably ("Hammer 12" vs "Frostfall")
    #   2. You may want events that share a
    #      date in a specific order
    #   3. You can insert events between
    #      others by adjusting numbers
    #
    # Convention: leave gaps. Start with
    # 100, 200, 300 instead of 1, 2, 3 — that
    # way you can insert at 150, 250 later
    # without renumbering everything.
    #
    # Like seat numbers in a theater that
    # leave room between rows for ushers.
    sort_order = Column(Integer, default=0, nullable=False)

    # --- HOVER SUMMARY ---
    # Short text shown in the tooltip when
    # the user hovers over the timeline node.
    # Keep it tight — 1-2 sentences max.
    summary = Column(Text)

    # --- FULL NARRATIVE ---
    # Long-form markdown narrative for the
    # event detail page. Renders with the
    # same | markdown filter we set up.
    body = Column(Text)

    # --- MILESTONE FLAG ---
    # Marks story-critical events that should
    # render larger or with extra emphasis on
    # the timeline. Think "the dragon arrives"
    # vs "the party bought a wagon."
    #
    # Stored as Integer (0/1) for SQLite
    # compatibility — same pattern we used
    # for is_primary on character images.
    is_milestone = Column(Integer, default=0, nullable=False)

    # --- TIMESTAMPS ---
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    # --- RELATIONSHIPS ---
    # An event has many images (one-to-many,
    # same as Character/Session).
    images = relationship(
        "EventImage", back_populates="event", cascade="all, delete-orphan"
    )

    # An event has many character connections
    # via the EventCharacter join table.
    # The cascade handles cleanup if the
    # event is deleted.
    character_links = relationship(
        "EventCharacter", back_populates="event", cascade="all, delete-orphan"
    )

    lore_links = relationship("LoreEvent", back_populates="event")

    def __repr__(self):
        return f"<TimelineEvent: {self.title}>"


# ============================================
# EVENT IMAGE MODEL
# ============================================
# Same structure as CharacterImage and
# SessionImage. By now this pattern should
# feel comfortable — three near-identical
# image tables, each tied to a different
# parent.
#
# In a more advanced design, we might
# unify these into a single polymorphic
# "Image" table. We won't — the duplication
# is small, and keeping them separate makes
# each table's purpose unambiguous. Like
# having three identical airlock procedures
# rather than one universal one with a
# bunch of conditional branches.
# =======================================
class EventImage(Base):
    __tablename__ = "event_images"

    id = Column(Integer, primary_key=True, index=True)

    event_id = Column(Integer, ForeignKey("timeline_events.id"), nullable=False)

    file_path = Column(String(255), nullable=False)
    caption = Column(String(255))
    is_featured = Column(Integer, default=0)
    uploaded_at = Column(DateTime, default=utc_now)

    event = relationship("TimelineEvent", back_populates="images")

    def __repr__(self):
        return f"<EventImage: {self.caption or 'No caption'} (Event #{self.event_id})>"


# ============================================
# EVENT-CHARACTER JOIN TABLE
# ============================================
# This is the new structural concept:
# many-to-many relationships.
#
# One event can include many characters.
# One character can appear in many events.
# Neither table can hold the relationship
# directly — there's no good way to put
# "many things" in a single column.
#
# So we create a third table that sits in
# the middle. Each row says "Event X is
# linked to Character Y." Add 50 such rows
# and you've described 50 connections.
#
# Star Wars parallel: think of it like
# pilot rosters. The Pilot table doesn't
# list which Squadrons each pilot has been
# in, and the Squadron table doesn't list
# every pilot. Instead, there's a separate
# "PilotAssignments" log: each entry pairs
# one pilot with one squadron and the dates
# they served. Same idea here.
#
# We're adding an extra field — "role" —
# to enrich the connection. This is a
# powerful pattern: join tables can hold
# their own data describing the nature of
# the relationship.
# ============================================
class EventCharacter(Base):
    __tablename__ = "event_characters"

    id = Column(Integer, primary_key=True, index=True)

    # --- THE TWO LINKS ---
    event_id = Column(Integer, ForeignKey("timeline_events.id"), nullable=False)
    character_id = Column(Integer, ForeignKey("characters.id"), nullable=False)

    # --- ROLE ---
    # Optional text describing how the
    # character relates to this event.
    # e.g. "Witness," "Antagonist,"
    # "Saved by the party," "Casualty"
    role = Column(String(100))

    # --- TIMESTAMP ---
    # When this connection was created.
    # Useful for an audit trail.
    created_at = Column(DateTime, default=utc_now)

    # --- BACK-LINKS ---
    # Each row in this join table can navigate
    # to its event and its character.
    event = relationship("TimelineEvent", back_populates="character_links")
    character = relationship("Character")

    def __repr__(self):
        return (
            f"<EventCharacter: Event #{self.event_id} ↔ Character #{self.character_id}>"
        )


# ============================================
# LORE ENTRY MODEL
# ============================================
# A single piece of world lore — a location,
# faction, magic item, deity, myth, etc.
#
# Unified into one model with a "category"
# field rather than separate tables per type.
# This keeps our codebase simple while still
# letting us filter and group meaningfully.
#
# Like a single field manual that organizes
# entries by chapter (category) rather than
# having a different book for every topic.
# ============================================
class LoreEntry(Base):
    __tablename__ = "lore_entries"

    id = Column(Integer, primary_key=True, index=True)

    # --- TITLE ---
    title = Column(String(200), nullable=False)

    # --- CATEGORY ---
    # Location, Faction, Item, Deity, Myth,
    # Other... we'll start with a few common
    # ones and you can add new categories on
    # the fly. The form will offer a dropdown
    # but accept any value, so adding "Tribe"
    # or "Magic" doesn't need a code change.
    #
    # Stored as a simple string. Could be an
    # enum if we wanted strict validation, but
    # flexibility wins here — campaigns are
    # weird and varied.
    category = Column(String(50), nullable=False, default="Other")

    # --- SUBTITLE ---
    # Optional flavor descriptor.
    # e.g. "Frost Giant Stronghold" or
    # "Ten-Towns' Largest Settlement"
    subtitle = Column(String(200))

    # --- BODY ---
    # Long-form markdown narrative. Same
    # treatment as session/event bodies —
    # rendered with the | markdown filter.
    body = Column(Text)

    # --- MAP COORDINATES (added in 5c) ---
    # Latitude/longitude on the campaign map.
    # Defined as Float so we can store decimal
    # positioning. Nullable because non-location
    # entries (factions, items, deities) don't
    # have a place on the map.
    #
    # We're using "lat" and "lng" naming even
    # though for our purposes they're really
    # just X/Y coordinates on an image. The
    # convention is widely understood and will
    # feel familiar if we ever upgrade to a
    # real geographic mapping library.
    lat = Column(Float)
    lng = Column(Float)

    # --- IS SECRET ---
    # Marks entries the players haven't
    # discovered yet. Once we add auth in
    # Phase 6, secret entries will be
    # DM-only. For now the field is here
    # but doesn't do anything functionally.
    #
    # Stored as Integer (0/1) for SQLite
    # consistency with our other booleans.
    is_secret = Column(Integer, default=0, nullable=False)

    # --- FOLIO / CODEX FIELDS ---
    # Which chapter this entry belongs to in
    # the codex (e.g. "Places of the North",
    # "Allies & Enemies", etc.). Free-text so
    # the DM can name chapters dynamically;
    # the form constrains via dropdown for
    # consistency.
    folio_chapter = Column(String(100), index=True)

    # Which page-template treatment this entry
    # gets on the spread: "cathedral" (one
    # spotlight entry per page), "bestiary"
    # (grid of 4-6), "glossary" (textual list).
    # Default to bestiary as the safest mid-
    # density treatment.
    folio_layout = Column(String(20), default="bestiary")

    # Order within the chapter. Lower values
    # appear first. Gaps in numbering are
    # fine (10, 20, 30 lets you insert at 15
    # later without renumbering everything).
    folio_position = Column(Integer, default=0)

    # Whether players can see this entry on
    # the codex. Separate from is_secret:
    #   is_secret = DM-only forever
    #   is_revealed = "the party has
    #     discovered this in the campaign"
    # An entry can be is_secret=0 and
    # is_revealed=0 (not a secret per se, but
    # the party hasn't found it yet).
    is_revealed = Column(Integer, default=0)

    # --- TIMESTAMPS ---
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    # --- RELATIONSHIPS ---
    images = relationship(
        "LoreImage", back_populates="lore_entry", cascade="all, delete-orphan"
    )

    character_links = relationship(
        "LoreCharacter", back_populates="lore_entry", cascade="all, delete-orphan"
    )

    event_links = relationship(
        "LoreEvent", back_populates="lore_entry", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<LoreEntry: {self.title} ({self.category})>"


# ============================================
# LORE IMAGE MODEL
# ============================================
# Same pattern as every other image table.
# By now this should feel like routine.
# ============================================
class LoreImage(Base):
    __tablename__ = "lore_images"

    id = Column(Integer, primary_key=True, index=True)

    lore_id = Column(Integer, ForeignKey("lore_entries.id"), nullable=False)

    file_path = Column(String(255), nullable=False)
    caption = Column(String(255))
    is_featured = Column(Integer, default=0)
    uploaded_at = Column(DateTime, default=utc_now)

    lore_entry = relationship("LoreEntry", back_populates="images")

    def __repr__(self):
        return f"<LoreImage: {self.caption or 'No caption'} (Lore #{self.lore_id})>"


# ============================================
# LORE-CHARACTER JOIN TABLE
# ============================================
# Same many-to-many pattern as EventCharacter.
# Links lore entries to characters with an
# optional descriptor of how they relate.
#
# Examples of "relationship" values:
#   "Worships," "Founded by," "Killed by,"
#   "Crafted by," "Hunted by," "Avatar of"
# ============================================
class LoreCharacter(Base):
    __tablename__ = "lore_characters"

    id = Column(Integer, primary_key=True, index=True)

    lore_id = Column(Integer, ForeignKey("lore_entries.id"), nullable=False)
    character_id = Column(Integer, ForeignKey("characters.id"), nullable=False)

    # --- DESCRIPTOR ---
    # How the character relates to this lore.
    # Optional — not every connection needs
    # a label.
    relationship_type = Column(String(100))

    created_at = Column(DateTime, default=utc_now)

    # --- BACK-LINKS ---
    lore_entry = relationship("LoreEntry", back_populates="character_links")
    character = relationship("Character", back_populates="lore_links")

    def __repr__(self):
        return f"<LoreCharacter: Lore #{self.lore_id} ↔ Character #{self.character_id}>"


# ============================================
# LORE-EVENT JOIN TABLE
# ============================================
# Same pattern, different connection.
# Links lore entries to timeline events.
#
# Examples of "relevance":
#   "First appearance," "Destroyed during,"
#   "Site of," "Origin"
# ============================================
class LoreEvent(Base):
    __tablename__ = "lore_events"

    id = Column(Integer, primary_key=True, index=True)

    lore_id = Column(Integer, ForeignKey("lore_entries.id"), nullable=False)
    event_id = Column(Integer, ForeignKey("timeline_events.id"), nullable=False)

    relevance = Column(String(100))

    created_at = Column(DateTime, default=utc_now)

    lore_entry = relationship("LoreEntry", back_populates="event_links")
    event = relationship("TimelineEvent", back_populates="lore_links")

    def __repr__(self):
        return f"<LoreEvent: Lore #{self.lore_id} ↔ Event #{self.event_id}>"


# ============================================
# USER MODEL
# ============================================
# A single row will ever exist in this table:
# the DM. We use a real database table rather
# than just an environment variable so:
#
#   1. The password can be changed via UI
#      (later refinement — change-password
#      page) without a server restart.
#   2. We have flexibility to add more users
#      later if we ever decide to.
#   3. The pattern matches how real auth
#      systems work, so the code teaches a
#      reusable concept.
#
# Like having an Imperial credentials
# database with one chip in it. Could grow
# to thousands. Doesn't have to.
# ============================================
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    # --- IDENTITY ---
    # Email address (also serves as the login
    # identifier). Marked unique because two
    # users can't share the same email.
    email = Column(String(255), unique=True, nullable=False, index=True)

    # --- PASSWORD HASH ---
    # We NEVER store the password itself.
    # Only the bcrypt hash. bcrypt hashes are
    # one-way — you can verify a password
    # against a hash, but you can't reverse a
    # hash back to a password.
    #
    # The String length is 60 because that's
    # the standard length of a bcrypt hash.
    password_hash = Column(String(60), nullable=False)

    # --- ROLE ---
    # Currently only "dm" exists, but having
    # a role field means we can later add
    # "player" or other roles without a
    # schema change.
    role = Column(String(20), default="dm", nullable=False)

    # --- TIMESTAMPS ---
    created_at = Column(DateTime, default=utc_now)
    last_login_at = Column(DateTime)

    def __repr__(self):
        return f"<User: {self.email} ({self.role})>"
