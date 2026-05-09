# Godfall — Refinements Etc

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

- **Re-evaluate the lore page layout once 5c is complete** — the
  card-grid-only view felt thin during 5a development, but final
  judgment was deferred until the map is in place and the page has
  meaningful density. After 5c, populate the lore section with real
  content (5-10 entries spanning multiple categories) and assess
  whether the card grid still feels Netflix-y or whether it works in
  context with the map anchor. If it still feels wrong, revisit
  approaches: categorized list view (Approach A), two-pane tome
  layout (Approach B), or a denser card variant.

- **Refine the lore "frost-crystal" card design** — the current
  card has subtle clipped corners and a hover image-zoom effect, but
  doesn't fully sell the "frost crystal" concept. Options to amplify:
  more aggressive clip-path angles for sharper facets, a layered
  back-shape for depth, an animated shimmer that occasionally sweeps
  across the card, frost-texture overlay on edges, stronger glow.
  Tackle alongside the lore page layout re-evaluation above.

- **Smarter pin destinations on the map** — currently pins always
  navigate to the lore detail page (Option A from the 5c discussion).
  Eventually, consider upgrading the hover tooltip to surface a
  "primary action" button that points to whatever's most relevant
  for that location (a connected session, a timeline event, etc.),
  while keeping the lore entry as the default destination. Doesn't
  require schema changes — just smarter tooltip rendering.

- **Mobile polish pass on the map page** — the floating "Frozen
  North" title overlay dominates the viewport on small screens,
  taking up valuable map real estate. Pins also feel small at
  thumb-tap scale. Specific items:

  1. Shrink the title overlay on mobile (or collapse it into a
     small "info" button that expands on tap).
  2. Increase pin tap-target size on mobile — current 40px works
     but 48-56px would be safer for thumb interaction.
  3. Pin tooltip currently appears at the bottom of the viewport
     on hover; on mobile (no hover), tooltips don't show at all.
     Consider tap-to-show, tap-elsewhere-to-dismiss.
  4. Consider a "fit to screen" default zoom or a panable/zoomable
     map (might require a small JS library like `leaflet` or
     `panzoom`). Worth doing if pin density grows.

  This is a fuller mobile polish pass for the map page in particular,
  since it's the most visually demanding page on the site.

- **"Previously on..." home page feature** — TTRPG sessions often
  have a week or more between play, and players (and the DM) forget
  where things stood. Add a recap section to the home page that
  bridges the gap between sessions.

  Hybrid approach:

  1. New small DB model — `PreviouslyOn` — with fields for a
     custom narrative blurb (markdown-supported), an optional
     pinned session reference, and an optional pinned timeline
     event reference. Plus timestamps.
  2. Only one entry is "active" at a time; updating it replaces
     the previous one (or archives it for history if we want to
     get fancy later).
  3. A small DM-only edit form somewhere accessible (e.g.
     `/previously-on/edit`) lets the DM write a fresh blurb
     between sessions. The form lets them link to recent
     content (a session, an event, or both).
  4. The home page renders the active entry below the "Five
     Flames" hero — title like "Previously on Godfall...",
     the DM's blurb, optional thumbnails of the linked session/
     event, and a "Read more" CTA pointing to the linked content.
  5. If no entry exists, the home page just shows the hero as
     it does now. Graceful fallback.

  This pairs well with the auth phase — the edit form should be
  DM-only, but the display is for everyone visiting the site.

  It also makes the home page feel alive instead of just being a
  beautiful but static landing screen. Genuinely useful between
  sessions, especially for groups with longer gaps between plays.

## Architecture & Story Features

- **NPC separation** — NPCs need their own page or a clearly distinct
  subsection of the Roster, so player characters remain the visual
  focus. Probably a separate route (`/npcs`) but reusing the same
  Character model and detail/form templates with `character_type`
  filtering.

- **Progressive NPC reveal (knowledge-gating)** — NPC character cards
  should reflect what the *party* currently knows about that NPC, not
  the full DM-side dossier. When the party first learns of an NPC by
  name, their card might show only a portrait and a name. As the
  party encounters them, learns lore about them, or witnesses key
  events, additional fields unlock and become visible: race, class,
  history excerpts, motivations, magic items, secrets, etc.

  Implementation sketch:

  1. Add a `discovery_state` model (or a JSON field on Character)
     tracking which fields are "revealed" for each NPC.
  2. Add DM-side controls on the NPC dossier: a series of toggles for
     each field marking it as discovered or hidden.
  3. The detail template renders only revealed fields when viewed by
     a player; DM view shows everything with discovery toggles.
  4. Optional: tie discovery to in-game triggers — e.g., linking an
     NPC to a timeline event the party witnessed could auto-reveal
     certain fields.
  5. Optional: a small "Newly discovered" indicator when a field
     transitions from hidden to revealed since the player's last
     visit.

  This pairs naturally with the auth phase (DM vs. player views)
  and the alternate-timeline concept. Genuinely transformative
  feature for a campaign companion site — it makes the site itself
  part of the storytelling.

- **Town-level maps (nested mapping)** — beyond the regional world
  map, each major settlement (the Ten-Towns, Easthaven, Bryn
  Shander, Targos, etc.) deserves its own zoomed-in map showing
  notable buildings, NPCs, and points of interest within the town.
  Two architectural approaches to consider:

  *Approach 1: Town maps as their own pages.* A regional pin for
  Bryn Shander on the world map links to either the lore entry or
  directly to a `/map/bryn-shander` page with a town map. Nested
  pin system — pins on the world map reveal town maps, pins on town
  maps reveal building/NPC details.

  *Approach 2: Town maps embedded in lore entries.* A Location-type
  lore entry for a town has an optional `town_map` field with its
  own pin coordinates. The detail page renders that map alongside
  the lore. No new routes; just an enrichment of the lore detail.

  Approach 1 is more powerful and scalable but means more
  infrastructure (zoom states, breadcrumb navigation, possibly
  zooming/panning UI). Approach 2 is simpler and keeps lore entries
  as self-contained units.

  Decide which approach when there's actual content to populate it
  with. Probably revisit after a few towns have been visited in
  play and the right shape becomes obvious.

  Either approach pairs beautifully with the "map as session
  backdrop" concept — clicking into a town during play to reference
  building locations or NPCs.

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
  unused variables, undefined references, etc.), enforces PEP 8, and
  runs in milliseconds. Would have caught the missing `event_end_date`
  parameter in `event_update` before runtime. Also clean up the import
  ordering in older route files (`sessions.py`, `characters.py`) so
  all imports are grouped at the top per convention.

- **Extract repeated template fragments** — the "lore link row"
  pattern is now copy-pasted across `characters/detail.html`,
  `timeline/detail.html`, and `lore/detail.html` (connected events
  list). Extract into `_lore_link_row.html` and reference via
  `{% include %}`. The "two-times rule" applies once we have three
  callers.

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

- **Map as session backdrop** — once the dedicated map page exists,
  consider polishing it for use on a tablet during actual sessions:
  large pins, easier-to-tap targets, possibly a "spotlight" mode that
  dims everything except a highlighted region. Pairs well with
  progressive NPC reveal and town-level maps — clicking a pin during
  play could surface newly-learned info live, then drill down into
  a town map when the party arrives at a settlement.

- **"Previously On" history archive** — extension of the home page
  recap feature. Once the basic version is in place, consider
  archiving past recap blurbs so players can scroll back through
  the "story so far" as a series of bite-sized summaries. Could
  work as a small archive page, or as a vertical stack on the home
  page showing the last 3-5 recaps. Useful for new players joining
  mid-campaign.

---

## Notes

Refinements written down stay refinements. Resist the urge to retrofit
them while building forward — context will sharpen what they should
actually become.