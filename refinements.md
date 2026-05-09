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

- **Add safeguard step against deletions** - especially on the character dossier page

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
  the schema without nuking `godfall.db`. Add this once we have real
  character data we care about preserving.

- **Pin Python version** — note in README that the project targets
  Python 3.12. Future-proofs setup if 3.13/3.14 introduce more breaking
  changes.

---

