# ============================================
# GODFALL - backfill_folio.py
# ============================================
# One-off script to assign folio chapters
# to existing lore entries based on their
# category.
#
# Run once after adding the new schema fields:
#   python backfill_folio.py
#
# Safe to run multiple times — it only updates
# entries with no chapter set yet.
# ============================================

from dotenv import load_dotenv
load_dotenv()

from app.database import SessionLocal
from app.models import LoreEntry


# Map existing categories to suggested chapters.
# DM can re-categorize later through the edit form.
CATEGORY_TO_CHAPTER = {
    "Location": "Places of the North",
    "Faction": "Allies & Enemies",
    "Item": "Relics & Curiosities",
    "Deity": "The Forgotten",
    "Creature": "Allies & Enemies",
    "Event": "Whispers & Rumors",
    "Other": "Whispers & Rumors",
}


def main():
    db = SessionLocal()
    try:
        entries = db.query(LoreEntry).filter(
            LoreEntry.folio_chapter.is_(None)
        ).all()

        if not entries:
            print("No entries needing backfill. All entries already have chapters.")
            return

        print(f"Found {len(entries)} entries without chapters. Updating...")

        for entry in entries:
            chapter = CATEGORY_TO_CHAPTER.get(
                entry.category,
                "Whispers & Rumors"  # fallback for unexpected categories
            )
            entry.folio_chapter = chapter
            # Also assume all existing entries are revealed
            # since they were already published before the
            # reveal mechanism existed. DM can re-hide later.
            entry.is_revealed = 1
            print(f"  {entry.title}  →  {chapter}")

        db.commit()
        print(f"\n✓ Updated {len(entries)} entries.")

    finally:
        db.close()


if __name__ == "__main__":
    main()