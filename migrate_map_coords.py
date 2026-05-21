# ============================================
# GODFALL - migrate_map_coords.py
# ============================================
# Converts existing map pin coordinates from
# percentage-based (0-100) to pixel-based
# coordinates matching the world map image
# dimensions.
#
# Like recalibrating a nav computer from
# relative bearings to absolute galactic
# coordinates. Same destinations, more
# precise math.
#
# Run once:
#   python migrate_map_coords.py
# ============================================

from dotenv import load_dotenv
load_dotenv()

from app.database import SessionLocal
from app.models import LoreEntry

# World map image dimensions in pixels
MAP_WIDTH = 1500
MAP_HEIGHT = 1054


def main():
    db = SessionLocal()
    try:
        entries = (
            db.query(LoreEntry)
            .filter(LoreEntry.lat.is_not(None))
            .filter(LoreEntry.lng.is_not(None))
            .all()
        )

        if not entries:
            print("No entries with coordinates found.")
            return

        print(f"Found {len(entries)} entries with coordinates.\n")

        for entry in entries:
            old_lat = entry.lat
            old_lng = entry.lng

            # Only convert if values look like percentages (0-100)
            # If they're already pixel values (> 100), skip
            if old_lat <= 100 and old_lng <= 100:
                new_y = (old_lat / 100) * MAP_HEIGHT
                new_x = (old_lng / 100) * MAP_WIDTH

                entry.lat = round(new_y, 2)
                entry.lng = round(new_x, 2)

                print(f"  {entry.title}: ({old_lng:.1f}%, {old_lat:.1f}%) → ({entry.lng:.0f}px, {entry.lat:.0f}px)")
            else:
                print(f"  SKIP {entry.title}: values already look like pixels ({old_lng}, {old_lat})")

        db.commit()
        print(f"\n✓ Migration complete.")

    finally:
        db.close()


if __name__ == "__main__":
    main()