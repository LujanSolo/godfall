# ============================================
# GODFALL - migrate_npcs_to_lore.py
# ============================================
# Migrates NPC records from the Character table
# to the LoreEntry table. Each NPC becomes a
# lore entry with:
#
#   - category = "Character"
#   - chapter = "Allies, Enemies & Other Dalefolk"
#   - title = character name
#   - subtitle = race · class · level · status
#   - body = markdown combining backstory, gear,
#            traits, and companions
#   - is_revealed = 1 (already known to players)
#   - is_secret = 0
#   - images copied to lore_images table
#
# Run once:
#   python migrate_npcs_to_lore.py
#
# Safe to run multiple times — checks for
# existing entries by title before creating
# duplicates.
# ============================================

from dotenv import load_dotenv
load_dotenv()

from app.database import SessionLocal, engine, Base
from app.models import Character, CharacterImage, LoreEntry, LoreImage
from pathlib import Path


def build_subtitle(npc):
    """Build a subtitle from structured fields."""
    parts = []
    if npc.race:
        parts.append(npc.race)
    if npc.character_class:
        if npc.level:
            parts.append(f"{npc.character_class} {npc.level}")
        else:
            parts.append(npc.character_class)
    if npc.status and npc.status != "Active":
        parts.append(npc.status)
    return " · ".join(parts) if parts else None


def build_body(npc):
    """
    Build a markdown body from the NPC's
    structured text fields. Each non-empty
    field becomes a headed section.
    """
    sections = []

    if npc.one_liner:
        sections.append(f"> *{npc.one_liner}*\n")

    if npc.backstory:
        sections.append(f"## Background\n\n{npc.backstory}")

    if npc.notable_traits:
        sections.append(f"## Notable Traits\n\n{npc.notable_traits}")

    if npc.top_magic_items:
        sections.append(f"## Notable Gear\n\n{npc.top_magic_items}")

    if npc.pets_companions:
        sections.append(f"## Pets & Companions\n\n{npc.pets_companions}")

    return "\n\n".join(sections) if sections else None


def main():
    db = SessionLocal()
    try:
        # Find all NPCs
        npcs = (
            db.query(Character)
            .filter(Character.character_type == "npc")
            .order_by(Character.name)
            .all()
        )

        if not npcs:
            print("No NPCs found to migrate.")
            return

        print(f"Found {len(npcs)} NPCs to migrate.\n")

        created = 0
        skipped = 0

        for npc in npcs:
            # Check if a lore entry with this title
            # already exists (prevents duplicates on
            # re-run)
            existing = (
                db.query(LoreEntry)
                .filter(LoreEntry.title == npc.name)
                .filter(LoreEntry.category == "NPC")
                .first()
            )

            if existing:
                print(f"  SKIP: {npc.name} (already exists as lore entry #{existing.id})")
                skipped += 1
                continue

            # Build the lore entry
            subtitle = build_subtitle(npc)
            body = build_body(npc)

            # Determine position based on importance
            # Major NPCs get lower numbers (appear first)
            position_map = {
                "major": 10,
                "minor": 50,
                "cameo": 90,
            }
            position = position_map.get(npc.importance, 50)

            new_entry = LoreEntry(
                title=npc.name,
                category="NPC",
                subtitle=subtitle,
                body=body,
                is_secret=0,
                is_revealed=1,
                folio_chapter="Allies, Enemies & Other Dalefolk",
                folio_layout="bestiary",
                folio_position=position,
            )
            db.add(new_entry)
            db.flush()  # Get the new entry's ID

            # Copy images from CharacterImage to LoreImage
            for char_img in npc.images:
                lore_img = LoreImage(
                    lore_id=new_entry.id,
                    file_path=char_img.file_path,
                    caption=char_img.caption,
                    is_featured=char_img.is_primary,
                )
                db.add(lore_img)

            print(f"  ✓ {npc.name} → Lore Entry #{new_entry.id}"
                  f" ({len(npc.images)} images copied)")
            created += 1

        db.commit()
        print(f"\n✓ Migration complete: {created} created, {skipped} skipped.")

        if created > 0:
            print("\nNPCs have been copied to the Lore table.")
            print("The original Character records still exist.")
            print("Once you've verified everything looks correct,")
            print("you can delete the old NPC Character records")
            print("by running: python cleanup_old_npcs.py")

    finally:
        db.close()


if __name__ == "__main__":
    main()