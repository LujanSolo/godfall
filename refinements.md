# Godfall — Refinements

A running list of polish items, design tweaks, and ideas to revisit
during the refinement phase. Captured during build so nothing gets
lost in the snowstorm.

---

## Visual & UX

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
  unpredictably (faces or key details can get cut off).

  Interim mitigation already applied: `object-position: center 25%`
  blanket rule biases cropping toward the upper portion of images,
  preserving heads and upper torsos for the common case. Real fix
  still needed.

  Better approach (Option 4 from the discussion):

  1. Add Pillow (Python's image library) to dependencies.
  2. On upload, generate optimized versions: thumbnail (square, ~400px)
     for gallery grids, landscape crop (~1200x675) for hero/featured
     spots, full-size (resized to ~2000px max dimension) for detail
     views.
  3. Allow the uploader to set a focal point (click-to-set
     coordinates) so cropping respects what's important. Store as
     focal_x, focal_y percentages on the image record.
  4. Pillow uses the focal point to decide where to center each
     variant's crop.
  5. Apply across all image displays: character galleries, session
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

- **Map experience overhaul (zoom, towns-as-hubs, in-town events)** —
  the current map handles single-point pins well, but as the campaign
  grows, three related limitations emerge that all want fixing
  together:

  1. *Multiple events at one location.* Several adventures may happen
     at or near the same map point (e.g. four sessions all set in
     Bryn Shander). The current pin model shows one tooltip per
     location, no good way to surface "five things happened here."
     Solution candidates:
     - Pin tooltips become richer, showing a list of related events
       and NPCs alongside the location summary.
     - Pin clicks lead to a "location hub" page that aggregates
       everything tied to that point.
     - Add zoom controls so multiple sub-pins can fan out at a
       location when zoomed in close enough.

  2. *Towns deserve their own pages and own maps.* Major settlements
     (Ten-Towns, Easthaven, Bryn Shander, Targos) have their own
     internal geography — inns, taverns, key buildings, residents.
     Clicking a town pin on the world map should navigate the user
     into a town-specific view with its own map and its own pins
     (already captured in the "Town-level maps" entry below; this
     entry exists to tie it explicitly into the broader map
     overhaul).

  3. *In-town adventures need representation on the world map.* Most
     of an adventure may happen entirely within a single town, and
     that should be visible from the world-map level too. A pin on
     Bryn Shander should hover-preview not just "Bryn Shander —
     Largest of the Ten-Towns" but also "5 sessions, 3 NPCs
     encountered, 2 timeline events" with quick links into each.

  Implementation thinking:

  - The cleanest architecture is to treat each Location lore entry
    as a *hub* with relationships to events, characters, sessions,
    and (optionally) other Location entries (parent/child for
    town-within-region nesting).
  - The hover tooltip becomes a richer summary card showing
    relationship counts and a few key links, not just the lore
    entry blurb.
  - Town pins, when clicked, navigate to the town's detail page —
    which renders that town's own map (per the town-level maps
    refinement) plus the standard lore entry content.
  - Zoom-in behavior is the most ambitious piece. Could be deferred
    until we know the world map actually needs it — or solved
    differently by always navigating into a town hub instead of
    trying to zoom on the world map itself.

  Worth tackling these three together as a single dedicated map
  overhaul phase, since they share so much underlying architecture.

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

- **Unified sigil across the Five Flames frieze** — a future flourish
  for the Tribunal layout: a single rune or sigil spanning the top
  of all five PC panels, partially obscured by each panel, only
  fully resolving when seen as a unified composition. Visual
  reinforcement of the "fragments of one" theme — the sigil is
  whole only when the Flames are aligned. Optional, additive, and
  thematically rich. Build only if the existing layered-panel effect
  feels like it could carry more storytelling weight.

- **Multiclass level display** — character level is currently a
  single integer, which doesn't represent multiclassed characters
  well. A Ranger 5 / Rogue 2 just shows as "Level 7" on cards and
  dossiers, losing the meaningful breakdown. Options:

  1. *Lightweight:* keep the integer total but add an optional
     "level breakdown" string field (e.g. "Ranger 5 / Rogue 2"
     or "5/2") that displays alongside the total.
  2. *Structured:* add a separate `class_levels` field as a list
     of (class_name, level) pairs. The level total is computed
     from those rather than stored. More work, but supports
     things like rendering each class with its own iconography
     or color treatment.

  Option 1 is the right starting point — it's a 5-minute change
  and handles 95% of the value. Option 2 is overkill unless we
  ever want to do something fancier with multiclass data.

  Display patterns to consider: "Class: Ranger / Rogue" with
  "Level: 7 (5/2)" beneath, or "Ranger 5 / Rogue 2 (Level 7)"
  inline. Either reads well.

## Story-Aware Features

- **"Previously on Godfall..." home page section** — D&D campaigns
  often go a week or more between sessions, and players genuinely
  forget where things stood. A "previously on..." moment on the
  home page would let the DM frame what matters most heading into
  the next session — like the recap intros at the start of a TV
  episode.

  Hybrid approach (the right one):

  1. Add a `Recap` model with fields:
     - `body` (markdown text, the DM's free-form summary)
     - `linked_session_id` (optional FK to SessionRecap)
     - `linked_event_id` (optional FK to TimelineEvent)
     - `linked_character_ids` (optional list, for highlighting NPCs
       newly introduced or returning)
     - `linked_lore_ids` (optional list, for relevant locations or
       items)
     - `is_active` (only one recap is active at a time — the
       current "previously on")
     - timestamps
  2. Add a small DM-only management page at `/recap` for editing
     the active recap.
  3. Render the active recap on the home page below the hero/title
     section, styled atmospherically (parchment scroll, frost-
     edged card, etc.). Linked items appear as small clickable
     references (portraits for characters, location pins for lore,
     etc.) so players can quickly refresh their memory.
  4. Optional polish: archive past recaps so players can scroll
     back through previous "previously on..." moments — like a
     mini journal of how the DM has framed the campaign.

  This pairs naturally with the auth phase (DM-only editing,
  player-readable display) and brings the home page to life as
  more than just decoration. Probably best built RIGHT AFTER auth
  is in place, since the editing controls need to be DM-gated.

- **NPC dossiers should link to timeline events** — character
  dossiers already display a "Mentioned in Lore" section (built
  in sub-phase 5b), but there's no equivalent "Appears in Events"
  section. The data is already there — we set up the
  EventCharacter join table back in Phase 4. We just need to query
  the back-reference.

  Implementation: add a `lore_links` parallel — `event_links` on
  the Character model already exists implicitly via the
  EventCharacter join table; we may need to add a back-reference
  declaration on Character (similar to what we did for
  `lore_links` in 5b). Then add a "Featured in Events" section to
  `characters/detail.html` that loops through the events.

  Should appear for both PCs and NPCs. NPCs benefit most because
  their stories are *defined* by the events they appear in —
  knowing which sessions or timeline beats featured a given NPC
  is exactly the kind of cross-reference that makes the site
  useful.

## Player Engagement Features (the big one)

- **Player accounts and in-session commentary** — the largest
  unbuilt feature on the list, but potentially the most
  transformative. Right now the auth system supports a single DM
  account. This refinement extends it to support player accounts
  and unlocks several connected capabilities:

  Architecture:

  1. Extend the User model to support multiple users with
     different roles ("dm", "player").
  2. Each player user is linked to one or more Character records
     (their PCs).
  3. Player login uses the same flow as DM login but lands them
     in a player session with read-only access to most things and
     write access to specific player-targeted features.

  The headline feature: comment threads on session recaps.

  Players can leave two kinds of comments on each session entry:

  - *In-character (IC):* their character speaks. Avatar shown is
    a small token of the linked character's primary portrait.
    Comment renders with character name + avatar, suggesting
    "this is what my character would say about this session."

  - *Out-of-character (OOC):* the player speaks as themselves.
    Comment renders with plain-text player name, no avatar.
    "Loved that scene where Vellynne pulled the lever" type
    energy. Distinct visual treatment from IC.

  Why this is valuable:

  - In-character commentary becomes its own narrative artifact —
    a chronicle of how each character experienced events from
    their own perspective.
  - Out-of-character commentary keeps the players engaged
    between sessions, building anticipation and shared memory.
  - The DM gets to see how players are processing the campaign
    without interrogating them at the table.

  Implementation considerations:

  - Comment model with fields: author_user_id, session_id, mode
    ("ic" or "ooc"), body (markdown), as_character_id (FK to
    Character, only used for IC comments), created_at, edited_at.
  - Replies/threading: probably worth supporting from day one,
    even if just a single level of nesting. Conversations matter.
  - Permissions: any logged-in player can post; DMs can post and
    moderate (delete any comment); players can edit/delete their
    own.
  - Notifications: optional but nice — a small "X new comments"
    indicator on the home page for players returning between
    sessions.
  - Could later extend the same comment system to timeline
    events and lore entries.

  This is a meaningful expansion of the auth system and a real
  feature unto itself. Best tackled as its own dedicated phase
  rather than a quick polish. Probably comes AFTER most of the
  smaller refinements above are in place — the site needs to
  feel finished before commentary becomes the next layer of
  storytelling.

## Architecture & Story Features

- **NPC separation** — RESOLVED in the Tribunal layout. PCs and NPCs
  now visually separated on the roster page. Keeping the entry here
  for posterity in case we ever want to revisit a fully separate
  `/npcs` route.

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

  Now folded into the broader **Map experience overhaul** entry
  above, since the town-map work is architecturally inseparable
  from the multi-event-at-one-location and in-town-events problems.
  Approach 1 (town maps as their own pages, nested pin system) is
  the favored direction now that we're tackling the whole map
  experience together.

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

- **Backup strategy for the database and uploads** — `godfall.db` and
  `app/static/uploads/` contain everything that isn't reproducible
  from code: characters, sessions, timeline events, lore entries,
  the DM credentials, every uploaded image. Neither is in version
  control (correctly so), which means a hard drive failure = total
  data loss. The site's current "backup story" is whatever the
  laptop's owner remembers to do manually.

  Strategy options, ordered by effort:

  1. *Manual periodic copy.* `cp godfall.db ~/Dropbox/godfall-backups/
     godfall-YYYY-MM-DD.db` once a week. Same for the uploads folder
     (or zip it first). Zero infrastructure, but relies entirely on
     habit.

  2. *Automated local script.* A small shell or Python script that
     runs daily via `cron` (or `launchd` on macOS), copies the
     database and uploads folder to a designated backup location
     (Dropbox, iCloud Drive, an external drive, etc.). Set it once,
     forget it.

  3. *Cloud sync at the OS level.* Place the entire project folder
     inside a synced cloud directory (Dropbox, iCloud Drive,
     OneDrive). The cloud provider handles versioning automatically.
     Easiest, but mixes "workspace" and "backup" concerns and may
     have quirks with the database file being open during writes.

  4. *Production-style backup.* Once the site is deployed (see entry
     below), the production server should have its own automated
     backup pipeline — typically a daily job that snapshots the
     database to an object storage bucket (S3, Backblaze B2, etc.)
     with rotation. This is the "real" answer for a live site.

  Suggested first step: option 1 right now, option 2 when the site
  feels valuable enough to lose, option 4 as part of deployment.

- **Production deployment** — once the refinement work feels
  meaningfully complete, the site needs a real home. Several
  reasonable hosting paths:

  - *Render / Railway / Fly.io* — modern, beginner-friendly hosts
    with free or low-cost tiers and Python/FastAPI support out of
    the box. Push the repo, they handle the rest.
  - *PythonAnywhere* — even simpler, specifically designed for
    Python web apps.
  - *VPS (DigitalOcean, Linode, Hetzner)* — full control, more
    setup work, requires configuring nginx + uvicorn + systemd
    yourself.

  Production deployment also needs to address: HTTPS via Let's
  Encrypt, the Tailwind production build (entry above), a real
  secret key in environment variables, the `secure=True` flag on
  session cookies, and the database backup pipeline (entry above).

  Worth tackling as its own dedicated phase, after most other
  refinements feel done.

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
  mobile redesign tax). Currently superseded by the Tribunal
  layout. May revisit as a signature visual moment in a later phase
  if the site has earned room for spectacle.

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

---

## Notes

Refinements written down stay refinements. Resist the urge to retrofit
them while building forward — context will sharpen what they should
actually become.