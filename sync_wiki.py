r"""Build the FoxRe public documentation site (MkDocs Material) straight from the project docs.

Single source of truth: the SITE map below. It decides which source docs are published, where they live on the
site, their titles, the section overview pages and the navigation (written into mkdocs.yml) — so pages and nav
can never drift apart. Source docs live in the private repo (`..\docs\`, `..\Engine\README.md`, ...).

Usage (from this folder, or via ..\Tools\sync_pages.py):
  python sync_wiki.py             generate docs/ + nav, then `mkdocs build --strict` (fails on any broken link)
  python sync_wiki.py --serve     generate, then live preview at http://127.0.0.1:8000
  python sync_wiki.py --commit    generate, validate, commit
  python sync_wiki.py --push      generate, validate, commit, push (GitHub Actions deploys Pages)

Two kinds of pages (Luc, 2026-10-23/24): hand-written articles (Start here, Explanations, Modding guides, Library
indexes; sources in ..\docs\site\, copied as written) and reference pages generated from the working documents
(docs\, Engine\README.md) or from repository files ("gen:" sources). Moved pages get redirect stubs (MOVED).

Rules (CLAUDE.md "Docs publishing"): no decorative emojis; statuses PASS / IN PROGRESS / PLANNED;
never publish docs/SAHELAN.md or docs/BATTLEFIELD.md; public site: no game files, no extracted data.
"""
from __future__ import annotations

import argparse
import datetime
import os
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
# MetalGear workspace (private repo); FOXRE_ROOT points at another checkout (a worktree) for previews.
ROOT = os.path.abspath(os.environ.get("FOXRE_ROOT") or os.path.join(HERE, ".."))
OUT = os.path.join(HERE, "docs")
KEEP = {"stylesheets", "javascripts"}                      # hand-maintained assets inside docs/
SRC_BLOB = "https://github.com/WannabeCoderLuc/mgsvtpp-foxre/blob/main/"

# --------------------------------------------------------------------------------------------------------------
# SITE MAP: (section title, folder, kind, overview text, [(page title, slug, source, one-line description), ...])
#   kind "manual":    hand-written articles, sources in docs/site/ of the project repo; copied as written (links
#                     resolved only). Rewritten by hand at milestone ends, never by tooling.
#   kind "reference": generated from the project's working documents (docs/, Engine/README.md, ...) on every sync.
#   kind "mixed":     both; a source "gen:<name>" is produced by GENERATED[<name>]() at build time.
# --------------------------------------------------------------------------------------------------------------
SITE = [
    ("Start here", "start", "manual", "What the project is, how this site is organised, and the words it uses. "
     "Hand-written.", [
        ("What this project is", "overview", "docs/site/start/Overview.md", "Goal, how the game is built, how we work, where we are."),
        ("How to use this site", "how-to-read", "docs/site/start/How-To-Read.md", "Hand-written vs generated pages, confidence tags, statuses."),
        ("Glossary", "glossary", "docs/site/start/Glossary.md", "Short definitions of the terms used on this site."),
    ]),
    ("Explanations", "explain", "manual", "One topic per page, in plain language: what it is, why it matters, how the "
     "original game does it, how the new engine does it, and how we know. Hand-written; rewritten at the end of "
     "every milestone. Read in order for a full tour.", [
        ("Game data: from disk to objects", "game-data", "docs/site/explain/Game-Data.md", "Archives, packages, DataSets and why names are hashes (M1)."),
        ("Classes, properties and entities", "classes-and-entities", "docs/site/explain/Classes-And-Entities.md", "The engine's type catalogue and how a level becomes live objects (M2)."),
        ("How a frame runs", "frame-loop", "docs/site/explain/Frame-Loop.md", "Game objects, the object manager, updates and messages (M3)."),
        ("The Lua script host", "script-host", "docs/site/explain/Script-Host.md", "The game's Lua, its 5,532 natives, the boot, record and replay (M4)."),
        ("How a mission loads", "mission-load", "docs/site/explain/Mission-Load.md", "Requests, package lists, blocks, script resources, the mission script (M5)."),
        ("Script blocks", "script-blocks", "docs/site/explain/Script-Blocks.md", "8 slots for side content: quests, reinforcements, animals (M5)."),
        ("The iDroid and the language reload", "idroid", "docs/site/explain/IDroid.md", "Why the iDroid's tables load three times per start-up (M5)."),
        ("World streaming and the title screen", "world-streaming", "docs/site/explain/World-Streaming.md", "Locators, map blocks around the player, fades and the title menu's Continue (M6)."),
        ("Routes and navmeshes", "routes-and-navmeshes", "docs/site/explain/Routes-And-Navmeshes.md", "Patrol routes and walkable surfaces (formats M1, runtime M8)."),
        ("How we verify", "verification", "docs/site/explain/Verification.md", "Pass/fail gates, FoxTrace captures, record/replay, claims, confidence tags."),
    ]),
    ("Modding guides", "mods", "manual", "What each finding means for a mod, with a worked (hypothetical) example "
     "of how it would be used. Hand-written; addresses are for PC 1.0.15.4 EN.", [
        ("For modders: findings at a glance", "for-modders", "docs/site/mods/For-Modders.md", "Every finding that matters for modding, in one page."),
        ("Add a package to a mission", "add-a-package", "docs/site/mods/Add-A-Package.md", "Mission package lists are Lua: wrap the package-path function."),
        ("Run your own Lua from a package", "lua-from-packages", "docs/site/mods/Lua-From-Packages.md", "Package scripts run on load, in path order."),
        ("Find and call Lua natives", "lua-natives", "docs/site/mods/Lua-Natives.md", "The binding map, stripped functions, recorded return values."),
        ("Side content with script blocks", "script-blocks", "docs/site/mods/Script-Blocks.md", "Load and unload your own content with the area."),
        ("Patching the iDroid tables", "idroid-tables", "docs/site/mods/IDroid-Tables.md", "Changes that survive the language reload."),
        ("Editing fox2 DataSets", "editing-datasets", "docs/site/mods/Editing-DataSets.md", "Typed entities, loader entities, byte-exact writing."),
        ("Tracing the game with FoxTrace", "foxtrace", "docs/site/mods/FoxTrace.md", "Log-only hooks to see what the game really does."),
        ("Checking community addresses", "claims", "docs/site/mods/Claims.md", "Use the claims ledger before you hook an address."),
    ]),
    ("Reference: engine", "engine", "reference", "Clean-room specifications of Fox Engine subsystems, and the state "
     "of the new engine that implements them. Generated from the project's working documents on every sync; each "
     "statement carries a confidence tag ([V], [D], [I], [?]).", [
        ("Engine modules", "modules", "Engine/README.md", "What exists in Engine/ today and how each module is verified."),
        ("Reflection and type database", "reflection", "docs/engine/Reflection.md", "The class registry: 1,153 classes, their properties and how they are registered."),
        ("Entities and DataSet loading", "entities", "docs/engine/Entities.md", "Typed entity graph, references, how the runtime loads a DataSet, live gate."),
        ("Scheduler", "scheduler", "docs/engine/Scheduler.md", "GameObjectManager, type slots, the per-frame update."),
        ("Messages and commands", "messages", "docs/engine/Messages.md", "MessageBus, SendCommand and SendMessage."),
        ("Script host", "script-host", "docs/engine/ScriptHost.md", "The Lua 5.1 runtime, boot script order, native library registration, title menu (M4, M6; PASS)."),
        ("Resources and mission load", "resources", "docs/engine/Resources.md", "Packages, blocks, script blocks, UI tables and how the game loads a location and a mission (M5, PASS)."),
        ("World streaming and locators", "world", "docs/engine/World.md", "DataIdentifier locator lookup, stage blocks and the title menu (M6, PASS)."),
        ("Claims ledger", "claims", "docs/CLAIMS.md", "Facts from IHHook, Infinite Heaven, V_Framework and the wiki, checked against the executable."),
        ("Claims: contradictions", "claims-contradictions", "docs/CLAIMS_CONTRADICTIONS.md", "Ours vs theirs for every contradicted community address."),
        ("Core architecture notes (2026-10-19)", "core-architecture", "docs/ENGINE.md", "Earlier research notes on boot, Quark systems and the class registry; partly superseded, see banners."),
    ]),
    ("Reference: file formats", "formats", "reference", "Byte-level specifications of the game's file formats, "
     "generated from the project's working documents. Every format listed here is read and re-written identically "
     "for every file of that type in the game.", [
        ("QAR archives", "qar", "docs/formats/QAR.md", "master/*.dat archives, entry encoding, path hashes."),
        ("FPK / FPKD packages", "fpk", "docs/formats/FPK.md", "Packages inside archives; Lua script decoding."),
        ("FOX2 DataSets", "fox2", "docs/formats/FOX2.md", "Entities, properties and the string table."),
        ("FRT route sets", "frt", "docs/formats/FRT.md", "Patrol routes, nodes and route events."),
        ("NAV2 navmeshes", "nav2", "docs/NAVMESH.md", "Walkable surfaces used for path finding."),
        ("FoxData containers", "foxdata", "docs/formats/FOXDATA.md", "Node-tree container shared by terrain and collision files."),
        ("HTRE / TRE2 terrain", "htre", "docs/formats/HTRE.md", "Height maps, terrain patches and height queries."),
        ("GEOM collision", "geom", "docs/formats/GEOM.md", "Collision geometry files (.geom, .geoms, .gskl)."),
    ]),
    ("Project status", "status", "reference", "Where the project stands: milestones with their pass/fail gates, "
     "the numbers, and the full dated log of every working session. Generated on every sync.", [
        ("Roadmap", "roadmap", "docs/ROADMAP.md", "Milestones M0-M14, their order and the gate each one must pass."),
        ("Numbers at a glance", "numbers", "gen:numbers", "Milestones, verified modules and test fixtures, counted at build time."),
        ("Session log", "log", "docs/LOG.md", "Every session, newest first, with addresses and test counts."),
    ]),
    ("Library", "library", "mixed", "Everything the work is built on and produces: sources, tools, test fixtures, "
     "live captures and external references.", [
        ("Sources", "sources", "docs/site/library/Sources.md", "The executable, the data, the running game, community projects, name dictionaries."),
        ("Tools", "tools", "docs/site/library/Tools.md", "What the project built and which third-party tools it uses."),
        ("Test fixtures", "fixtures", "gen:fixtures", "Ground-truth files the engine tests compare against (generated list)."),
        ("Live captures", "captures", "gen:captures", "Every FoxTrace capture run, with its hooks (generated list)."),
        ("External references", "external", "docs/site/library/External.md", "Outside material that shaped the method or the specs."),
        ("MCP server and knowledge DB", "mcp-server", "mgsv_unified_server/AI_GUIDE.md", "The mgsv-unified MCP server: tools, evidence levels, knowledge DB."),
        ("Installed tools", "tooling", "docs/TOOLING.md", "Tool inventory and lessons from AI-assisted RE projects."),
        ("Background", "background", "docs/BACKGROUND.md", "Game, engine and community facts this project builds on."),
    ]),
]
NOT_PUBLISHED = {"docs/SAHELAN.md", "docs/BATTLEFIELD.md", "docs/PROBES.md", "docs/V_FRAMEWORK.md", "docs/README.md",
                 "docs/SAHELAN_FEASIBILITY.md"}
# Pages that moved in the 2026-10-24 restructure: old site path -> new site path (redirect stubs are generated).
MOVED = {
    "guide/overview": "start/overview", "guide/glossary": "start/glossary", "guide/game-data": "explain/game-data",
    "guide/classes-and-entities": "explain/classes-and-entities", "guide/frame-loop": "explain/frame-loop",
    "guide/verification": "explain/verification", "guide/scripts-and-missions": "explain/mission-load",
    "guide/for-modders": "mods/for-modders", "guide": "start", "tools/mcp-server": "library/mcp-server",
    "tools/tooling": "library/tooling", "tools/background": "library/background", "tools": "library",
}

# Old GitHub-wiki page names that appear as [text](Name) links in source docs -> source path
WIKI_NAMES = {
    "Home": None, "Roadmap": "docs/ROADMAP.md", "Session-Log": "docs/LOG.md", "Engine-Modules": "Engine/README.md",
    "Engine-Reflection": "docs/engine/Reflection.md", "Engine-Entities": "docs/engine/Entities.md",
    "Engine-Scheduler": "docs/engine/Scheduler.md", "Engine-Messages": "docs/engine/Messages.md", "Engine-ScriptHost": "docs/engine/ScriptHost.md",
    "Engine-Core-Architecture": "docs/ENGINE.md", "Format-QAR": "docs/formats/QAR.md", "Format-FPK": "docs/formats/FPK.md",
    "Format-FOX2": "docs/formats/FOX2.md", "Format-FRT": "docs/formats/FRT.md", "Format-NAV2": "docs/NAVMESH.md",
    "MCP-Server": "mgsv_unified_server/AI_GUIDE.md", "Tooling": "docs/TOOLING.md", "Background": "docs/BACKGROUND.md",
    "Engine-Resources": "docs/engine/Resources.md", "Engine-World": "docs/engine/World.md", "Claims": "docs/CLAIMS.md", "Claims-Contradictions": "docs/CLAIMS_CONTRADICTIONS.md",
    "Sahelanthropus": "docs/SAHELAN.md", "Battlefield-AI": "docs/BATTLEFIELD.md",
    # 2026-10-24 restructure; the old Guide-* names keep working
    "Guide-Overview": "docs/site/start/Overview.md", "Guide-Glossary": "docs/site/start/Glossary.md",
    "Guide-Game-Data": "docs/site/explain/Game-Data.md", "Guide-Classes-And-Entities": "docs/site/explain/Classes-And-Entities.md",
    "Guide-Frame-Loop": "docs/site/explain/Frame-Loop.md", "Guide-Verification": "docs/site/explain/Verification.md",
    "Guide-For-Modders": "docs/site/mods/For-Modders.md", "Guide-Scripts-And-Missions": "docs/site/explain/Mission-Load.md",
}
for _t, _f, _k, _o, _pages in SITE:                      # Start-*, Explain-*, Mods-*, Library-* names for every manual page
    for _pt, _slug, _src, _d in _pages:
        if _src.startswith("docs/site/"):
            _sec = {"start": "Start", "explain": "Explain", "mods": "Mods", "library": "Library"}[_f]
            WIKI_NAMES[_sec + "-" + os.path.splitext(os.path.basename(_src))[0]] = _src

EMOJI = re.compile("[\U0001F000-\U0001FAFF☀-➿⬀-⯿️‍]")
GLYPH_STATUS = {"✅": "PASS", "\U0001F536": "IN PROGRESS", "⬜": "PLANNED"}


def site_path_of() -> dict[str, str]:
    """source path -> site page path (relative to docs/)."""
    m = {}
    for _t, folder, _k, _o, pages in SITE:
        for _pt, slug, src, _d in pages:
            m[src] = f"{folder}/{slug}.md"
    return m


SRC_TO_SITE = site_path_of()


def norm(p: str) -> str:
    p = p.replace("\\", "/").lstrip("./")
    for prefix in ("..//", "../"):
        while p.startswith(prefix):
            p = p[len(prefix):]
    return p


def rel(from_page: str, to_page: str) -> str:
    return os.path.relpath(to_page, os.path.dirname(from_page) or ".").replace("\\", "/")


def resolve_src(token: str, current_src: str) -> str | None:
    """Turn a reference found in a source doc into a source path (or None)."""
    t = token.split("#")[0]
    if t in WIKI_NAMES:
        return WIKI_NAMES[t]
    t = norm(t)
    if t in SRC_TO_SITE or t in NOT_PUBLISHED:
        return t
    for cand in (f"docs/{t}", f"docs/engine/{t}", f"docs/formats/{t}", f"docs/guide/{t}",
                 os.path.normpath(os.path.join(os.path.dirname(current_src), t)).replace("\\", "/")):
        if cand in SRC_TO_SITE or cand in NOT_PUBLISHED:
            return cand
    return None


def block_spacing(text: str) -> str:
    """Python-Markdown only starts a table or list after a blank line; GitHub does not need one.
    Insert the blank line before a table header / first list item that directly follows a paragraph."""
    out, fence = [], False
    lines = text.split("\n")
    for i, line in enumerate(lines):
        s = line.lstrip()
        if s.startswith(("```", "~~~")):
            fence = not fence
        prev = out[-1].strip() if out else ""
        if not fence and prev.startswith("|") and s and not s.startswith("|"):
            out.append("")                     # text right after a table would become a table row
            prev = ""
        if not fence and prev and not prev.startswith(("|", "#", ">", "<")) \
                and not re.match(r"([-*+]|\d+\.) ", prev):
            nxt = lines[i + 1].strip() if i + 1 < len(lines) else ""
            starts_table = s.startswith("|") and re.match(r"^\|?\s*:?-{3,}", nxt)
            starts_list = line == s and (re.match(r"[-*+] \S", s) or re.match(r"\d+\. \S", s))
            if starts_table or starts_list:
                out.append("")
        out.append(line)
    return "\n".join(out)


def transform(text: str, src: str, page: str) -> str:
    text = block_spacing(text)
    for g, word in GLYPH_STATUS.items():
        text = text.replace(g, word)
    text = EMOJI.sub("", text)

    # [text](Target) links: wiki names or relative .md paths
    def link(m):
        label, target = m.group(1), m.group(2)
        if re.match(r"^(https?:|mailto:|#)", target):
            return m.group(0)
        anchor = "#" + target.split("#", 1)[1] if "#" in target else ""
        s = resolve_src(target, src)
        if s is None:
            return m.group(0) if target.endswith((".png", ".svg", ".jpg")) else label
        if s in NOT_PUBLISHED:
            return f"{label} (not published)"
        return f"[{label}]({rel(page, SRC_TO_SITE[s])}{anchor})"
    text = re.sub(r"(?<!!)\[([^\]]+)\]\(([^)\s]+)\)", link, text)

    # `docs\x\Y.md`-style code references -> links when the doc is published
    def code(m):
        s = resolve_src(m.group(1), src)
        if s in SRC_TO_SITE:
            return f"[`{m.group(1)}`]({rel(page, SRC_TO_SITE[s])})"
        return m.group(0)
    text = re.sub(r"`((?:\.\.[\\/])?(?:docs|Engine|mgsv_unified_server)[\\/][\w\\/.-]+\.md)`", code, text)

    # status words in table cells -> badges
    text = re.sub(r"(?<=\| )`?(PASS|IN PROGRESS|PLANNED)`?(?= \|)",
                  lambda m: f'<span class="status {m.group(1).lower().replace(" ", "-")}">{m.group(1)}</span>', text)
    return text


def first_heading_strip(text: str, title: str) -> str:
    """Use the site title as the page H1; drop the source's own first H1."""
    lines = text.splitlines()
    for i, l in enumerate(lines[:5]):
        if l.startswith("# "):
            del lines[i]
            break
    return f"# {title}\n\n" + "\n".join(lines).lstrip("\n")


def section_index(title: str, folder: str, overview: str, pages) -> str:
    out = [f"# {title}", "", overview, "", '<div class="grid cards" markdown>', ""]
    for pt, slug, _src, desc in pages:
        out += [f"-   **[{pt}]({slug}.md)**", "", f"    {desc}", ""]
    out += ["</div>", ""]
    return "\n".join(out)


# --------------------------------------------------------------------------------------------------------------
# Generated pages ("gen:<name>" sources): built from files of the project repo at sync time
# --------------------------------------------------------------------------------------------------------------
FIXTURE_NOTES = {
    "m3_frame_trace.json": "M3: updater-vector changes and the 43 bus messages from boot to free roam (2 identical boots).",
    "m4_lua_boot.json": "M4/M5: the 170 Lua chunks of a cold boot to free roam, in load order, plus library registrations.",
    "m4_lua_bindings.json": "M4: binding map, 399 libraries / 5,532 natives with addresses, kinds, enum values, boot points.",
    "m4_lua_consts.json": "M4: Lua constant tables read statically from the executable.",
    "m4_lua_returns.json": "M4: recorded native return values (FoxTrace luaret captures) used for record/replay.",
    "m5_save_image.json": "M5: the minimal save values behind TppScriptVars.LoadVarsFromSlot (from a live dump).",
    "f30010_identifiers.json": "M2: names, classes and world positions of 17 objects asked from the running game.",
}


def gen_fixtures() -> str:
    d = os.path.join(ROOT, "Engine", "tests", "fixtures")
    rows = []
    for name in sorted(os.listdir(d)) if os.path.isdir(d) else []:
        p = os.path.join(d, name)
        size = sum(os.path.getsize(os.path.join(dp, f)) for dp, _x, fs in os.walk(p) for f in fs) if os.path.isdir(p) \
            else os.path.getsize(p)
        rows.append(f"| `{name}` | {size / 1024:,.0f} KB | {FIXTURE_NOTES.get(name, 'see the test that loads it')} |")
    return ("# Test fixtures\n\nGround truth the engine tests (`Engine/tests/`) compare against. Each comes from the "
            "running game or the executable, never from our own code. Contents stay in the project repository "
            "(no game data); this list is generated at every sync.\n\n| Fixture | Size | What it holds |\n|---|---|---|\n"
            + "\n".join(rows) + "\n")


def gen_captures() -> str:
    d = os.path.join(ROOT, "Memory", "research")
    rows = []
    for name in sorted(os.listdir(d)) if os.path.isdir(d) else []:
        cfg = os.path.join(d, name, "FoxTrace.cfg")
        if not (name.startswith("trace_") and os.path.isfile(cfg)):
            continue
        hooks = [l.split()[1] for l in open(cfg, encoding="utf-8", errors="replace")
                 if l.split() and l.split()[0] in ("hook", "luaret")]
        runs = len([r for r in os.listdir(os.path.join(d, name)) if r.startswith("run")])
        m = re.match(r"trace_(.+)_(\d{8})_(\d{6})$", name)
        what, day = (m.group(1), f"{m.group(2)[:4]}-{m.group(2)[4:6]}-{m.group(2)[6:]}") if m else (name, "")
        shown = ", ".join(f"`{h}`" for h in hooks[:6]) + (f" and {len(hooks) - 6} more" if len(hooks) > 6 else "")
        rows.append(f"| {day} | `{what}` | {runs} | {len(hooks)} | {shown} |")
    rows.sort(reverse=True)
    return ("# Live captures\n\nEvery FoxTrace capture: the game booted with log-only hooks, usually twice, then "
            "restored. Raw logs stay in the private workspace; findings go to the Reference pages. Generated list, "
            "newest first.\n\n| Date | Capture | Runs | Hooks | Hooked |\n|---|---|:-:|:-:|---|\n"
            + "\n".join(rows) + "\n")


def gen_numbers() -> str:
    ms = milestones()
    mrows = "\n".join(f"| {i} {t} | {badge(st)} |" for i, t, _d, st in ms)
    mods = [l for l in open(os.path.join(ROOT, "Engine", "README.md"), encoding="utf-8").read().splitlines()
            if l.startswith("| `")]
    tests = len([f for f in os.listdir(os.path.join(ROOT, "Engine", "tests")) if f.startswith("test_")])
    fx = len(os.listdir(os.path.join(ROOT, "Engine", "tests", "fixtures")))
    return (f"# Numbers at a glance\n\nCounted from the project repository at build time.\n\n"
            f"- Milestones passed: **{sum(st == 'PASS' for *_x, st in ms)} of {len(ms)}**\n"
            f"- Verified engine modules: **{len(mods)}** (table on the [home page](../index.md))\n"
            f"- Test files: **{tests}**, ground-truth fixtures: **{fx}**\n\n"
            f"| Milestone | Status |\n|---|:-:|\n{mrows}\n")


GENERATED = {"fixtures": gen_fixtures, "captures": gen_captures, "numbers": gen_numbers}


def redirect(target: str) -> str:
    return (f'<!doctype html><html><head><meta charset="utf-8"><title>Moved</title>'
            f'<meta http-equiv="refresh" content="0; url={target}"><link rel="canonical" href="{target}">'
            f'</head><body>This page moved to <a href="{target}">{target}</a>.</body></html>\n')


def milestones() -> list[tuple[str, str, str]]:
    t = open(os.path.join(ROOT, "docs", "ROADMAP.md"), encoding="utf-8").read()
    out = []
    for m in re.finditer(r"^## (M\d+) ([^\n]*)$", t, re.M):
        rest = m.group(2)
        st = "PASS" if "[PASS]" in rest else "IN PROGRESS" if "[IN PROGRESS]" in rest else "PLANNED"
        title = re.split(r"\[(?:PASS|IN PROGRESS|PLANNED)\]", rest, maxsplit=1)[0].strip()
        detail = rest.split("—", 1)[1].strip() if "—" in rest else ""
        out.append((m.group(1), title, detail, st))
    return out


def badge(st: str) -> str:
    return f'<span class="status {st.lower().replace(" ", "-")}">{st}</span>'


def home() -> str:
    ms = milestones()
    done = sum(st == "PASS" for *_, st in ms)
    cur = next((f"{i} {t}" for i, t, _d, st in ms if st == "IN PROGRESS"), "")
    rows = "\n".join(f"| {i} | {t} | {d} | {badge(st)} |" for i, t, d, st in ms)
    status = open(os.path.join(ROOT, "STATUS.md"), encoding="utf-8").read()
    recent = status.split("## Recent log", 1)[1].split("\n", 1)[1].strip() if "## Recent log" in status else ""
    recent = transform(recent, "STATUS.md", "index.md")
    mods = [l for l in open(os.path.join(ROOT, "Engine", "README.md"), encoding="utf-8").read().splitlines()
            if l.startswith("| `")]
    mods = "\n".join(transform(l, "Engine/README.md", "index.md") for l in mods)
    return f"""---
hide:
  - toc
---

<div class="hero" markdown>

# FoxRe

**Reverse engineering *Metal Gear Solid V: The Phantom Pain* and rebuilding its Fox Engine — clean-room, test-gated.**

PC 1.0.15.4 &middot; runtime analysis only &middot; no game files published &middot; every claim backed by a pass/fail test

**{done} of {len(ms)} milestones passed** &middot; current: **{cur}**

</div>

<div class="grid cards" markdown>

-   **[Start here](start/index.md)**

    What the project is and how this site is organised.

-   **[Explanations](explain/index.md)**

    One topic per page in plain language: what it is, why it matters, how the engine does it.

-   **[Modding guides](mods/index.md)**

    What the findings mean for a mod, each with a worked example.

-   **[Reference](engine/index.md)**

    Generated specifications: [engine](engine/index.md) and [file formats](formats/index.md), with confidence tags.

-   **[Project status](status/index.md)**

    Roadmap with milestone gates, numbers and the full session log.

-   **[Library](library/index.md)**

    Sources, tools, test fixtures, live captures, external references.

</div>

## Milestones

| | Milestone | Scope | Status |
|---|---|---|:-:|
{rows}

## Verified engine modules

| Module | Language | Specification | State | Gate (on all game files) |
|---|---|---|---|---|
{mods}

## Latest sessions

{recent}

[Full session log](status/log.md)
"""


def nav_yaml() -> str:
    lines = ["nav:", "  - Home: index.md"]
    for title, folder, _k, _o, pages in SITE:
        lines.append(f"  - \"{title}\":")
        lines.append(f"      - {folder}/index.md")
        for pt, slug, _s, _d in pages:
            lines.append(f"      - \"{pt}\": {folder}/{slug}.md")
    return "\n".join(lines) + "\n"


def generate() -> None:
    for name in os.listdir(OUT):
        if name in KEEP:
            continue
        p = os.path.join(OUT, name)
        shutil.rmtree(p) if os.path.isdir(p) else os.remove(p)
    stamp = datetime.date.today().isoformat()
    for title, folder, kind, overview, pages in SITE:
        os.makedirs(os.path.join(OUT, folder), exist_ok=True)
        open(os.path.join(OUT, folder, "index.md"), "w", encoding="utf-8").write(section_index(title, folder, overview, pages))
        for pt, slug, src, _d in pages:
            assert src not in NOT_PUBLISHED, src
            page = f"{folder}/{slug}.md"
            if src.startswith("gen:"):
                text = GENERATED[src[4:]]()
                note = f"Generated {stamp} from the project repository."
            elif src.startswith("docs/site/"):
                text = open(os.path.join(ROOT, src), encoding="utf-8").read()
                note = f"Hand-written article (`{src}`) &middot; published {stamp}."
            else:
                text = open(os.path.join(ROOT, src), encoding="utf-8").read()
                note = f"Source: `{src}` in the project repository &middot; generated {stamp}."
            body = first_heading_strip(transform(text, src, page), pt)
            body += f"\n\n---\n<small>{note}</small>\n"
            open(os.path.join(OUT, page), "w", encoding="utf-8").write(body)
    for old, new in MOVED.items():                       # redirect stubs for pages that moved
        d = os.path.join(OUT, *old.split("/"))
        if os.path.exists(os.path.join(OUT, old + ".md")):
            continue
        os.makedirs(d, exist_ok=True)
        target = "../" * (old.count("/") + 1) + new + "/"
        open(os.path.join(d, "index.html"), "w", encoding="utf-8").write(redirect(target))
    open(os.path.join(OUT, "index.md"), "w", encoding="utf-8").write(home())
    # nav -> mkdocs.yml (replace everything after the 'nav:' line)
    y = os.path.join(HERE, "mkdocs.yml")
    cfg = open(y, encoding="utf-8").read()
    cfg = cfg.split("\nnav:\n")[0].rstrip() + "\n\n" + nav_yaml()
    open(y, "w", encoding="utf-8").write(cfg)
    n = sum(len(p) for *_x, p in SITE)
    print(f"generated {n} pages + {len(SITE)} section overviews + home + {len(MOVED)} redirects -> {OUT}")


def mkdocs(*args) -> int:
    return subprocess.run([sys.executable, "-m", "mkdocs", *args], cwd=HERE).returncode


def git(*args, check=True):
    return subprocess.run(["git", *args], cwd=HERE, check=check, capture_output=True, text=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--serve", action="store_true")
    ap.add_argument("--commit", action="store_true")
    ap.add_argument("--push", action="store_true")
    a = ap.parse_args()
    generate()
    if a.serve:
        sys.exit(mkdocs("serve"))
    if mkdocs("build", "--strict", "--quiet") != 0:
        sys.exit("mkdocs build --strict failed (broken link or config error) - nothing committed")
    raw = []
    for dp, _d, fs in os.walk(os.path.join(HERE, "site")):
        for f in fs:
            if f.endswith(".html") and re.search(r"\|\s*:?-{3,}", open(os.path.join(dp, f), encoding="utf-8").read()):
                raw.append(os.path.relpath(os.path.join(dp, f), HERE))
    if raw:
        sys.exit("unrendered markdown table in: " + ", ".join(raw))
    print("mkdocs build --strict: OK (no raw tables)")
    if a.commit or a.push:
        git("add", "-A")
        if git("status", "--porcelain").stdout.strip():
            git("commit", "-m", f"Site update {datetime.date.today()} (generated from project docs)")
            print("committed")
        else:
            print("no changes")
        if a.push:
            git("push", "origin", "main")
            print("pushed: GitHub Actions will deploy https://wannabecoderluc.github.io/foxre-wiki/")


if __name__ == "__main__":
    main()
