from dotenv import load_dotenv
load_dotenv()

from app.database import SessionLocal
from app.models import LoreEntry


RENAMES = {
    "Allies & Enemies": "Allies, Enemies & Other Dalefolk",
    "The Frostmaiden's Court": "Gods & Mysteries",
    "The Forgotten": "Gods & Mysteries",
}


def main():
    db = SessionLocal()
    try:
        updated = 0
        for old_name, new_name in RENAMES.items():
            entries = db.query(LoreEntry).filter(
                LoreEntry.folio_chapter == old_name
            ).all()
            for entry in entries:
                print(f"  {entry.title}: '{old_name}' → '{new_name}'")
                entry.folio_chapter = new_name
                updated += 1

        if updated:
            db.commit()
            print(f"\n✓ Updated {updated} entries.")
        else:
            print("No entries needed migration.")
    finally:
        db.close()


if __name__ == "__main__":
    main()