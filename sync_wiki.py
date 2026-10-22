r"""Build the FoxRe public documentation site (MkDocs Material) straight from the project docs.

Single source of truth: the SITE map below. It decides which source docs are published, where they live on the
site, their titles, the section overview pages and the navigation (written into mkdocs.yml) — so pages and nav
can never drift apart. Source docs live in the private repo (`..\docs\`, `..\Engine\README.md`, ...).

Usage (from this folder, or via ..\Tools\sync_pages.py):
  python sync_wiki.py             generate docs/ + nav, then `mkdocs build --strict` (fails on any broken link)
  python sync_wiki.py --serve     generate, then live preview at http://127.0.0.1:8000
  python sync_wiki.py --commit    generate, validate, commit
  python sync_wiki.py --push      generate, validate, commit, push (GitHub Actions deploys Pages)

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
ROOT = os.path.abspath(os.path.join(HERE, ".."))          # MetalGear workspace (private repo)
OUT = os.path.join(HERE, "docs")
KEEP = {"stylesheets", "javascripts"}                      # hand-maintained assets inside docs/
SRC_BLOB = "https://github.com/WannabeCoderLuc/mgsvtpp-foxre/blob/main/"

# --------------------------------------------------------------------------------------------------------------
# SITE MAP: (section title, folder, overview text, [(page title, slug, source, one-line description), ...])
# --------------------------------------------------------------------------------------------------------------
SITE = [
    ("Guide", "guide", "Plain-language explanations of how the game and its engine work, written for readers "
     "without a reverse-engineering background. Start here. Rewritten at the end of every milestone.", [
        ("What this project is", "overview", "docs/guide/Overview.md", "Goal, how the game is built, how we work, current status."),
        ("Game data: from disk to objects", "game-data", "docs/guide/Game-Data.md", "Archives, packages, DataSets and why names are hashes."),
        ("Classes, properties and entities", "classes-and-entities", "docs/guide/Classes-And-Entities.md", "The engine's type catalogue and how a level becomes live objects."),
        ("How a frame runs", "frame-loop", "docs/guide/Frame-Loop.md", "Game objects, the object manager, updates and messages."),
        ("How we verify", "verification", "docs/guide/Verification.md", "Pass/fail gates, evidence types and confidence tags."),
        ("Glossary", "glossary", "docs/guide/Glossary.md", "Short definitions of the terms used on this site."),
    ]),
    ("Project status", "status", "Where the project stands: milestones with their pass/fail gates, and the full "
     "dated log of every working session.", [
        ("Roadmap", "roadmap", "docs/ROADMAP.md", "Milestones M0-M9 and the gate each one must pass."),
        ("Session log", "log", "docs/LOG.md", "Every session, newest first, with addresses and test counts."),
    ]),
    ("Engine", "engine", "Clean-room specifications of Fox Engine subsystems, and the state of the new engine "
     "that implements them. Each statement carries a confidence tag ([V], [D], [I], [?]).", [
        ("Engine modules", "modules", "Engine/README.md", "What exists in Engine/ today and how each module is verified."),
        ("Reflection and type database", "reflection", "docs/engine/Reflection.md", "The class registry: 1,153 classes, their properties and how they are registered."),
        ("Entities and DataSet loading", "entities", "docs/engine/Entities.md", "Typed entity graph, references, how the runtime loads a DataSet, live gate."),
        ("Scheduler", "scheduler", "docs/engine/Scheduler.md", "GameObjectManager, type slots, the per-frame update."),
        ("Messages and commands", "messages", "docs/engine/Messages.md", "MessageBus, SendCommand and SendMessage."),
        ("Script host", "script-host", "docs/engine/ScriptHost.md", "The Lua 5.1 runtime, boot script order and native library registration (M4, in progress)."),
        ("Core architecture notes (2026-10-19)", "core-architecture", "docs/ENGINE.md", "Earlier research notes on boot, Quark systems and the class registry; partly superseded, see banners."),
    ]),
    ("File formats", "formats", "Byte-level specifications of the game's file formats. Every format listed here is "
     "read and re-written identically for every file of that type in the game.", [
        ("QAR archives", "qar", "docs/formats/QAR.md", "master/*.dat archives, entry encoding, path hashes."),
        ("FPK / FPKD packages", "fpk", "docs/formats/FPK.md", "Packages inside archives; Lua script decoding."),
        ("FOX2 DataSets", "fox2", "docs/formats/FOX2.md", "Entities, properties and the string table."),
        ("FRT route sets", "frt", "docs/formats/FRT.md", "Patrol routes, nodes and route events."),
        ("NAV2 navmeshes", "nav2", "docs/NAVMESH.md", "Walkable surfaces used for path finding."),
    ]),
    ("Tools", "tools", "The tooling the project is built with: the MCP server that gives the AI agent access to "
     "the binary, the data and the running game, plus installed tools and background notes.", [
        ("MCP server and knowledge DB", "mcp-server", "mgsv_unified_server/AI_GUIDE.md", "The mgsv-unified MCP server: tools, evidence levels, knowledge DB."),
        ("Installed tools", "tooling", "docs/TOOLING.md", "Tool inventory and lessons from AI-assisted RE projects."),
        ("Background", "background", "docs/BACKGROUND.md", "Game, engine and community facts this project builds on."),
    ]),
]
NOT_PUBLISHED = {"docs/SAHELAN.md", "docs/BATTLEFIELD.md", "docs/PROBES.md", "docs/V_FRAMEWORK.md", "docs/README.md"}

# Old GitHub-wiki page names that appear as [text](Name) links in source docs -> source path
WIKI_NAMES = {
    "Home": None, "Roadmap": "docs/ROADMAP.md", "Session-Log": "docs/LOG.md", "Engine-Modules": "Engine/README.md",
    "Engine-Reflection": "docs/engine/Reflection.md", "Engine-Entities": "docs/engine/Entities.md",
    "Engine-Scheduler": "docs/engine/Scheduler.md", "Engine-Messages": "docs/engine/Messages.md", "Engine-ScriptHost": "docs/engine/ScriptHost.md",
    "Engine-Core-Architecture": "docs/ENGINE.md", "Format-QAR": "docs/formats/QAR.md", "Format-FPK": "docs/formats/FPK.md",
    "Format-FOX2": "docs/formats/FOX2.md", "Format-FRT": "docs/formats/FRT.md", "Format-NAV2": "docs/NAVMESH.md",
    "MCP-Server": "mgsv_unified_server/AI_GUIDE.md", "Tooling": "docs/TOOLING.md", "Background": "docs/BACKGROUND.md",
    "Guide-Overview": "docs/guide/Overview.md", "Guide-Game-Data": "docs/guide/Game-Data.md",
    "Guide-Classes-And-Entities": "docs/guide/Classes-And-Entities.md", "Guide-Frame-Loop": "docs/guide/Frame-Loop.md",
    "Guide-Verification": "docs/guide/Verification.md", "Guide-Glossary": "docs/guide/Glossary.md",
    "Sahelanthropus": "docs/SAHELAN.md", "Battlefield-AI": "docs/BATTLEFIELD.md",
}

EMOJI = re.compile("[\U0001F000-\U0001FAFF☀-➿⬀-⯿️‍]")
GLYPH_STATUS = {"✅": "PASS", "\U0001F536": "IN PROGRESS", "⬜": "PLANNED"}


def site_path_of() -> dict[str, str]:
    """source path -> site page path (relative to docs/)."""
    m = {}
    for _t, folder, _o, pages in SITE:
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

-   **[Guide](guide/index.md)**

    Plain-language explanations of how the game's data and engine work. Start here.

-   **[Engine](engine/index.md)**

    Specifications of engine subsystems and the state of the new engine.

-   **[File formats](formats/index.md)**

    Byte-level format specs, each verified on every game file.

-   **[Project status](status/index.md)**

    Roadmap with milestone gates, and the full session log.

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
    for title, folder, _o, pages in SITE:
        lines.append(f"  - {title}:")
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
    for title, folder, overview, pages in SITE:
        os.makedirs(os.path.join(OUT, folder), exist_ok=True)
        open(os.path.join(OUT, folder, "index.md"), "w", encoding="utf-8").write(section_index(title, folder, overview, pages))
        for pt, slug, src, _d in pages:
            assert src not in NOT_PUBLISHED, src
            page = f"{folder}/{slug}.md"
            text = open(os.path.join(ROOT, src), encoding="utf-8").read()
            body = first_heading_strip(transform(text, src, page), pt)
            body += f"\n\n---\n<small>Source: `{src}` in the project repository &middot; generated {stamp}.</small>\n"
            open(os.path.join(OUT, page), "w", encoding="utf-8").write(body)
    open(os.path.join(OUT, "index.md"), "w", encoding="utf-8").write(home())
    # nav -> mkdocs.yml (replace everything after the 'nav:' line)
    y = os.path.join(HERE, "mkdocs.yml")
    cfg = open(y, encoding="utf-8").read()
    cfg = cfg.split("\nnav:\n")[0].rstrip() + "\n\n" + nav_yaml()
    open(y, "w", encoding="utf-8").write(cfg)
    n = sum(len(p) for *_x, p in SITE)
    print(f"generated {n} pages + {len(SITE)} section overviews + home -> {OUT}")


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
