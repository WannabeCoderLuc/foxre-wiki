# FoxRe documentation site

Live: https://wannabecoderluc.github.io/foxre-wiki/ — public site of the FoxRe project (reverse engineering *Metal Gear Solid V: The Phantom Pain* and rebuilding its Fox Engine). MkDocs Material, deployed by `.github/workflows/deploy.yml` on every push to `main`.

## How it works
Everything under `docs/` except `docs/stylesheets/` is **generated** — do not edit it by hand.

`sync_wiki.py` holds one `SITE` map (section, page title, slug, source doc, one-line description). From it, it:
- copies each source doc from the project repo (`..\docs\`, `..\Engine\README.md`, `..\mgsv_unified_server\AI_GUIDE.md`) to `docs/<section>/<slug>.md`;
- rewrites cross-references (`[x](Engine-Scheduler)`, `docs\engine\Scheduler.md`, relative `.md` links) to site links; references to unpublished docs become plain text;
- strips decorative emojis and turns status cells into `PASS` / `IN PROGRESS` / `PLANNED` badges;
- generates the home page (milestones from `ROADMAP.md`, modules from `Engine/README.md`, recent sessions from `STATUS.md`) and one overview page per section;
- writes the `nav:` block of `mkdocs.yml`, so navigation always matches the pages;
- runs `mkdocs build --strict` (any broken link fails the run).

The sidebar lists every section and page on every page (no tabs, no hidden sub-pages).

## Commands
| Command | Effect |
|---|---|
| `python sync_wiki.py` | generate + strict build |
| `python sync_wiki.py --serve` | generate + live preview at http://127.0.0.1:8000 |
| `python sync_wiki.py --push` | generate + strict build + commit + push (deploys) |

From the project root: `python Tools\sync_pages.py [--serve|--push]` does the same.

## Adding a page
Add one tuple to `SITE` in `sync_wiki.py` (and, if older docs link to it by a wiki-style name, to `WIKI_NAMES`). Nothing else.

## Rules
No decorative emojis. Statuses as text. Never published: `docs/SAHELAN.md`, `docs/BATTLEFIELD.md` (plus internal probe/framework notes). No game files or extracted data.
