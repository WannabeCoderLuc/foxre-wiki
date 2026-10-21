# FoxRe Documentation Site

> **Live Website:** [https://wannabecoderluc.github.io/foxre-wiki/](https://wannabecoderluc.github.io/foxre-wiki/)  
> **Source Repository:** [WannabeCoderLuc/mgsvtpp-foxre](https://github.com/WannabeCoderLuc/mgsvtpp-foxre)  
> **Documentation Target:** *Metal Gear Solid V: The Phantom Pain* (PC 1.0.15.4 EN)

This repository contains the GitHub Pages documentation website for the **FoxRe** reverse engineering project, powered by **MkDocs Material**. It provides clean-room, test-gated architectural specifications and reverse-engineering research for Konami's Fox Engine.

---

## Key Features

- **Pure Markdown Core:** All documentation lives as standard `.md` files in `docs/`.
- **Professional Tactical Theme:** Sleek dark-mode aesthetic (slate background with Fox amber accents), custom badges, and zero decorative emojis.
- **Fast Client-Side Search:** Full-text offline indexing with search suggestions and deep-link highlighting.
- **Automated GitHub Pages Deployment:** Built and published automatically via GitHub Actions on every push to `main`.
- **AI-Friendly Update Pipeline:** Single-command synchronization script (`sync_wiki.py`) that pulls upstream docs, standardizes formatting, validates links, and commits/pushes updates.

---

## Directory Structure

```
FoxRe_Wiki/
├── .github/
│   └── workflows/
│       └── deploy.yml          # GitHub Pages build and deployment workflow
├── docs/
│   ├── index.md                # Homepage / project dashboard
│   ├── Roadmap.md              # Milestone tracking and acceptance gates
│   ├── Session-Log.md          # Chronological development log
│   ├── Engine-Modules.md       # Engine core modules overview
│   ├── Engine-Core-Architecture.md # Startup chain, Quark system table, ClassDescriptor
│   ├── Engine-Reflection.md    # Runtime type database and property tables
│   ├── Engine-Entities.md      # Typed entity graph and reference closure
│   ├── Format-QAR.md           # QAR container specification
│   ├── Format-FPK.md           # FPK package format and Lua bytecode
│   ├── Format-FOX2.md          # FOX2 DataSet serialization
│   ├── Format-FRT.md           # Route datasets and route event types
│   ├── Format-NAV2.md          # Navigation mesh topology and routing
│   ├── MCP-Server.md           # Model Context Protocol server tooling
│   ├── Tooling.md              # Disassembly, decompression, and verification tools
│   ├── Background.md           # Project history, licensing, and clean-room methodology
│   └── stylesheets/
│       └── extra.css           # High-tech / tactical CSS styling and badges
├── mkdocs.yml                  # MkDocs site configuration and navigation
├── requirements.txt            # Python dependencies for building the site
├── sync_wiki.py                # Automated documentation sync and transformation tool
└── README.md                   # This documentation file
```

---

## Updating Documentation (AI & Developer Guide)

The documentation is designed to be easily updated by developers or automated AI agents.

### Automated Sync (Recommended)

To pull the latest documentation, strip decorative emojis, fix internal links, validate the build, and push to GitHub Pages:

```bash
python sync_wiki.py --push
```

### Command-Line Options

| Command | Action |
|---|---|
| `python sync_wiki.py` | Syncs markdown files from local source or upstream wiki, cleans formatting, and validates the build. |
| `python sync_wiki.py --build` | Synchronizes docs and compiles the static HTML site into `site/`. |
| `python sync_wiki.py --serve` | Starts a live development server at `http://127.0.0.1:8000` with hot reloading. |
| `python sync_wiki.py --commit "Message"` | Syncs docs and commits the changes to git. |
| `python sync_wiki.py --push` | Syncs, validates, commits, and pushes to `origin main`. |
| `python sync_wiki.py --source <path_or_url>` | Specifies a custom local directory or remote git URL as the documentation source. |

### Manual Edits

You can edit or add `.md` files directly in `docs/`:

1. Place or edit `.md` files inside `docs/`.
2. If adding a new page, add its entry to `nav` in `mkdocs.yml`.
3. Test locally with `python -m mkdocs serve`.
4. Commit and push to `main` — GitHub Actions will automatically deploy the changes to GitHub Pages.

---

## Local Development

To run the site locally:

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Launch the local live-reload server
python -m mkdocs serve
```

The site will be accessible at: `http://127.0.0.1:8000/foxre-wiki/` (or `http://127.0.0.1:8000/`).

---

## GitHub Pages Setup

To activate the GitHub Pages site on the repository:

1. Go to repository **Settings** -> **Pages**.
2. Under **Build and deployment** -> **Source**, select **GitHub Actions**.
3. Push to `main` (or run `python sync_wiki.py --push`).
4. The deployment action will build the site and publish it to `https://wannabecoderluc.github.io/foxre-wiki/`.
