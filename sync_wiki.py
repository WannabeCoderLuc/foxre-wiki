"""Sync and transform the FoxRe GitHub Wiki into a professional, emoji-free,
GitHub Pages-ready MkDocs documentation site.

Usage:
  python sync_wiki.py             # Sync docs, remove emojis, fix links, validate build
  python sync_wiki.py --build     # Also build the static site (to site/)
  python sync_wiki.py --serve     # Start local live-reload server (http://127.0.0.1:8000)
  python sync_wiki.py --commit    # Sync and commit changes to git
  python sync_wiki.py --push      # Sync, commit, and push to origin main
"""

import argparse
import os
import re
import shutil
import subprocess
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DOCS_DIR = os.path.join(SCRIPT_DIR, "docs")
STYLESHEET_DIR = os.path.join(DOCS_DIR, "stylesheets")

DEFAULT_UPSTREAM_URL = "https://github.com/WannabeCoderLuc/mgsvtpp-foxre.wiki.git"
LOCAL_FALLBACK_PATHS = [
    os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".wiki_build")),
    os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".wiki_repo")),
]

# Pages included in the documentation site
PAGE_SLUGS = {
    "Home": "index.md",
    "Roadmap": "Roadmap.md",
    "Session-Log": "Session-Log.md",
    "Engine-Modules": "Engine-Modules.md",
    "Engine-Reflection": "Engine-Reflection.md",
    "Engine-Entities": "Engine-Entities.md",
    "Engine-Core-Architecture": "Engine-Core-Architecture.md",
    "Format-QAR": "Format-QAR.md",
    "Format-FPK": "Format-FPK.md",
    "Format-FOX2": "Format-FOX2.md",
    "Format-FRT": "Format-FRT.md",
    "Format-NAV2": "Format-NAV2.md",
    "MCP-Server": "MCP-Server.md",
    "Tooling": "Tooling.md",
    "Background": "Background.md",
}

# Excluded pages
EXCLUDED_PAGES = {
    "_Sidebar.md",
    "_Footer.md",
    "Battlefield-AI.md",
    "Sahelanthropus.md",
}

# External fallback for removed docs to prevent broken links
EXTERNAL_FALLBACKS = {
    "Sahelanthropus": "https://github.com/WannabeCoderLuc/mgsvtpp-foxre/blob/main/docs/SAHELAN.md",
    "Sahelanthropus.md": "https://github.com/WannabeCoderLuc/mgsvtpp-foxre/blob/main/docs/SAHELAN.md",
    "Battlefield-AI": "https://github.com/WannabeCoderLuc/mgsvtpp-foxre/blob/main/docs/BATTLEFIELD.md",
    "Battlefield-AI.md": "https://github.com/WannabeCoderLuc/mgsvtpp-foxre/blob/main/docs/BATTLEFIELD.md",
}

# Unicode emoji pattern covering all standard emoji blocks and symbols
EMOJI_REGEX = re.compile(
    r"[\U00010000-\U0010ffff]|"
    r"[\u2600-\u27bf]|"
    r"[\u2300-\u23ff]|"
    r"[\u2b50-\u2b55]|"
    r"[\u200d\ufe0e\ufe0f]|"
    r"[🟩🟨⬜✅🔶]"
)


def find_source(source_arg: str | None) -> str:
    """Locate the source directory containing wiki markdown files."""
    if source_arg:
        if os.path.isdir(source_arg):
            return os.path.abspath(source_arg)
        tmp_dir = os.path.join(SCRIPT_DIR, ".upstream_wiki")
        shutil.rmtree(tmp_dir, ignore_errors=True)
        print(f"Cloning upstream wiki from {source_arg}...")
        subprocess.run(["git", "clone", "--depth", "1", source_arg, tmp_dir], check=True)
        return tmp_dir

    for local_path in LOCAL_FALLBACK_PATHS:
        if os.path.isdir(local_path) and os.path.isfile(os.path.join(local_path, "Home.md")):
            print(f"Using local source: {local_path}")
            return local_path

    tmp_dir = os.path.join(SCRIPT_DIR, ".upstream_wiki")
    shutil.rmtree(tmp_dir, ignore_errors=True)
    print(f"Cloning upstream wiki from {DEFAULT_UPSTREAM_URL}...")
    subprocess.run(["git", "clone", "--depth", "1", DEFAULT_UPSTREAM_URL, tmp_dir], check=True)
    return tmp_dir


def clean_emojis(text: str) -> str:
    """Replace status emojis with professional badges/tags, and remove decorative emojis."""
    # Progress bar transformation
    text = re.sub(
        r"[🟩🟨⬜]{5,}",
        lambda m: f'<div class="progress-bar-container"><div class="progress-bar-fill" style="width: {min(100, int((m.group(0).count("🟩") + m.group(0).count("🟨")*0.5) / len(m.group(0)) * 100))}%"></div></div>',
        text,
    )

    # Status indicators
    text = text.replace("✅", '<span class="status-badge status-pass">PASS</span>')
    text = text.replace("🔶", '<span class="status-badge status-wip">IN PROGRESS</span>')
    text = text.replace("⬜", '<span class="status-badge status-planned">PLANNED</span>')

    # Remove remaining emojis
    text = EMOJI_REGEX.sub("", text)

    # Clean up double spaces or awkward spacing after emoji removal
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"^[-*]\s+", "- ", text, flags=re.MULTILINE)
    text = re.sub(r"^#{1,6}\s+", lambda m: m.group(0).strip() + " ", text, flags=re.MULTILINE)

    return text


def fix_internal_links(text: str) -> str:
    """Fix internal wiki links and wrap unbackticked code calls so markdown does not parse them as broken links."""
    # Wrap function calls like vtbl[0x208](&id) or handler[bb[5]](update) in inline backticks
    text = re.sub(
        r"(?<!`)\b([a-zA-Z_]\w*(?:->\w+)?)\s*(\[[^\]\r\n]*\[[^\]\r\n]*\][^\]\r\n]*\]|\[[^\]\r\n]*\])\(([^)\r\n]*)\)(?!`)",
        r"`\1\2(\3)`",
        text,
    )

    # Fix markdown links [Label](Target) where Target matches a wiki page or fallback
    def replace_link(m):
        label = m.group(1)
        target = m.group(2)

        # Check external fallbacks
        if target in EXTERNAL_FALLBACKS:
            return f"[{label}]({EXTERNAL_FALLBACKS[target]})"

        # Parse anchor if present
        anchor = ""
        page_name = target
        if "#" in target:
            page_name, anchor = target.split("#", 1)
            anchor = "#" + anchor

        if page_name in PAGE_SLUGS:
            resolved = PAGE_SLUGS[page_name] + anchor
            return f"[{label}]({resolved})"

        if page_name in EXTERNAL_FALLBACKS:
            return f"[{label}]({EXTERNAL_FALLBACKS[page_name]}{anchor})"

        return m.group(0)

    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", replace_link, text)

    # Clean up note banners
    text = text.replace("🏠 Home", "Home").replace("🗺️ Roadmap", "Roadmap")

    return text


def sync_docs(source_dir: str) -> None:
    """Sync, transform, and write markdown files into docs/."""
    os.makedirs(DOCS_DIR, exist_ok=True)
    os.makedirs(STYLESHEET_DIR, exist_ok=True)

    # Clean existing markdown files in docs/
    for existing in os.listdir(DOCS_DIR):
        existing_path = os.path.join(DOCS_DIR, existing)
        if os.path.isfile(existing_path) and existing.endswith(".md"):
            os.remove(existing_path)

    copied_count = 0
    for fname in os.listdir(source_dir):
        if not fname.endswith(".md"):
            continue
        if fname in EXCLUDED_PAGES:
            continue

        src_path = os.path.join(source_dir, fname)
        target_name = PAGE_SLUGS.get(fname[:-3], fname)
        dst_path = os.path.join(DOCS_DIR, target_name)

        content = open(src_path, encoding="utf-8").read()
        cleaned = clean_emojis(content)
        final_text = fix_internal_links(cleaned)

        # Enhance homepage header & clean quick-links table
        if target_name == "index.md":
            final_text = re.sub(
                r"<div align=\"center\">\s*#\s*mgsvtpp-foxre",
                '<div class="wiki-hero">\n\n# FoxRe Wiki\n\n### Fox Engine Reverse Engineering & Architecture Reference\n\n'
                '<div class="hero-badges">\n'
                '<span class="hero-badge">Target: PC 1.0.15.4 EN</span>\n'
                '<span class="hero-badge">Runtime Hooks Only</span>\n'
                '<span class="hero-badge">Clean-Room Verified</span>\n'
                '<span class="hero-badge">Machine-Checked Gates</span>\n'
                '</div>\n',
                final_text,
            )
            # Remove any broken game systems row from the quick navigation table
            final_text = re.sub(
                r"\|\s*Game systems\s*\|[^\n]+\n?",
                "",
                final_text,
            )

        with open(dst_path, "w", encoding="utf-8") as f:
            f.write(final_text)
        copied_count += 1

    print(f"Successfully processed and synced {copied_count} pages into {DOCS_DIR}")


def validate_mkdocs() -> bool:
    """Run mkdocs build to validate configuration and links."""
    print("Validating MkDocs build...")
    res = subprocess.run(["python", "-m", "mkdocs", "build", "--strict"], cwd=SCRIPT_DIR)
    if res.returncode == 0:
        print("MkDocs validation passed with zero errors!")
        return True
    else:
        print("MkDocs validation encountered warnings or errors.", file=sys.stderr)
        return False


def git_commit_and_push(commit_msg: str, push: bool = False) -> None:
    """Stage, commit, and optionally push changes to git."""
    subprocess.run(["git", "add", "-A"], cwd=SCRIPT_DIR, check=True)
    status = subprocess.run(["git", "status", "--porcelain"], cwd=SCRIPT_DIR, capture_output=True, text=True).stdout
    if not status.strip():
        print("Working tree clean, nothing to commit.")
        return

    subprocess.run(["git", "commit", "-m", commit_msg], cwd=SCRIPT_DIR, check=True)
    print(f"Committed changes: '{commit_msg}'")

    if push:
        print("Pushing to origin main...")
        subprocess.run(["git", "push", "-u", "origin", "main"], cwd=SCRIPT_DIR, check=True)
        print("Pushed successfully to remote!")


def main():
    parser = argparse.ArgumentParser(description="FoxRe Wiki Sync and Builder")
    parser.add_argument("--source", help="Source directory or git repository URL")
    parser.add_argument("--build", action="store_true", help="Build static site")
    parser.add_argument("--serve", action="store_true", help="Start development server")
    parser.add_argument("--commit", nargs="?", const="Update documentation (auto-sync)", help="Commit changes to git")
    parser.add_argument("--push", action="store_true", help="Push to git remote origin main")

    args = parser.parse_args()

    source_dir = find_source(args.source)
    sync_docs(source_dir)

    success = validate_mkdocs()
    if not success and (args.commit or args.push):
        print("Aborting git commit/push due to build errors.", file=sys.stderr)
        sys.exit(1)

    if args.commit or args.push:
        msg = args.commit if isinstance(args.commit, str) else "Update documentation (auto-sync)"
        git_commit_and_push(msg, push=args.push)

    if args.serve:
        print("Starting MkDocs live server at http://127.0.0.1:8000 ...")
        subprocess.run(["python", "-m", "mkdocs", "serve"], cwd=SCRIPT_DIR)


if __name__ == "__main__":
    main()
