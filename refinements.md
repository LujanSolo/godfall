# Godfall — Refinements

A running list of polish items, design tweaks, and ideas to revisit
during the refinement phase. Captured during build so nothing gets
lost in the snowstorm.

---

## Visual & UX

- **Character card layout** — switch from centered grid to **Option 6
  (banner-style horizontal cards)** with responsive vertical-on-mobile
  adaptation. Portrait left, info right on desktop. Portrait top, info
  below on mobile. Editorial "intelligence briefing" feel.

- **Custom mobile menu icon** — replace the standard hamburger lines
  with something more thematic (frosted snowflake, d20, illuminated
  rune, etc). Search `*** REFINEMENT TARGET ***` in `base.html` to find
  the swap point.

- **Delete confirmation modals** — currently every delete action uses
  the browser's built-in `confirm()` dialog. It's functional but ugly
  (looks like a system error mid-page, can't be styled, can be
  suppressed by browsers, breaks the immersive Frostmaiden feel).
  Replace across the site with a custom HTMX-driven modal: styled to
  match the design, triggered via `hx-get` to render a confirmation
  panel, with an explicit "type the name to confirm" input for high-
  stakes deletes (characters, sessions). Applies anywhere the user can
  destroy data: characters, sessions, individual images, future
  timeline events, and lore entries.

  Note: this is a UX upgrade, not a security fix. Real authorization
  lives on the server (added in the auth phase).

- **Auto-adjusting images for galleries and previews** — when an image
  is uploaded, generate multiple sized/cropped variants on the server
  rather than relying on browser CSS cropping. Currently we use
  `object-cover` to fit any image into any container, which crops
  unpredictably (faces or key details can get cut off). Better
  approach:

  1. Add Pillow (Python's image library) to dependencies.
  2. On upload, generate optimized versions: thumbnail (square, ~400px)
     for gallery grids, landscape crop (~1200x675) for hero/featured
     spots, full-size (resized to ~2000px max dimension) for detail
     views.
  3. Optionally, allow the uploader to set a focal point (click-to-set
     coordinates) so cropping respects what's important.
  4. Apply across all image displays: character galleries, session
     galleries, timeline event galleries, hover previews.

  This dramatically improves visual quality and reduces page weight
  (no more loading full-resolution images for tiny thumbnails). Worth
  doing once we have enough images uploaded to feel the pain.

## Architecture

- **NPC separation** — NPCs need their own page or a clearly distinct
  subsection of the Roster, so player characters remain the visual
  focus. Probably a separate route (`/npcs`) but reusing the same
  Character model and detail/form templates with `character_type`
  filtering.

## Production-Readiness

- **Tailwind production build** — switch from CDN
  (`cdn.tailwindcss.com`) to a proper compiled stylesheet. Set up
  Tailwind CLI to scan templates, purge unused classes, output a small
  optimized CSS file. Removes the dev-only warning and dramatically
  reduces page weight.

- **Database migrations (Alembic)** — install Alembic so we can change
  the schema without nuking `godfall.db` or doing manual ALTER TABLE
  commands. Add this once we have real character data we care about
  preserving.

- **Pin Python version** — note in README that the project targets
  Python 3.12. Future-proofs setup if 3.13/3.14 introduce more breaking
  changes.

- **Add a linter (`ruff`)** — install and configure `ruff`, the modern
  Python linter. It auto-flags style inconsistencies (import order,
  unused variables, etc.), enforces PEP 8, and runs in milliseconds.
  Also clean up the import ordering in older route files (`sessions.py`,
  `characters.py`) so all imports are grouped at the top per
  convention.

---

## Cut from Roadmap

- **Standalone Photo & Art Gallery** (was Phase 4) — cut. Images
  naturally live where they belong: character dossiers, NPC dossiers,
  session recaps, and timeline events. A general gallery would either
  duplicate those views or compete with them for content. No coding
  benefit either — the upload patterns we already built are the
  reusable foundation.

## Future Ideas (not on roadmap)

- **Media library admin view** — different from a public gallery.
  Behind-the-scenes view of every image uploaded across the site, with
  search/filter/retag/delete capability. Useful only if image volume
  grows unwieldy. Build only if needed.

- **Fanned hand of cards layout** — considered for the character
  roster but rejected for now (too brittle for changing party sizes,
  mobile redesign tax). May revisit as a signature visual moment in a
  later phase if the site has earned room for spectacle.

- **Alternate timeline layer** — a second visual track on the timeline
  showing the "original" history that Xylos's Final Wish overwrote.
  Could appear as a ghost-line that fades in on a special interaction,
  or a toggle that swaps which timeline is shown. Story-rich feature,
  but only meaningful once players are deep enough into the campaign
  to encounter the truth.

- **Visual time-spans on the timeline** — currently multi-day events
  show as a single node with a date range label. A more expressive
  version would render them as bars spanning a section of the
  timeline. Requires real date-based positioning (vs. our current
  sort_order approach), which means parsing fantasy calendar strings.
  Significant effort. Build only if event durations become a major
  storytelling element.

---

## Notes

Refinements written down stay refinements. Resist the urge to retrofit
them while building forward — context will sharpen what they should
actually become.