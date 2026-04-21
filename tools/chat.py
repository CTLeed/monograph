#!/usr/bin/env python3
"""Monograph Level-1 chat helper.

Interpolates a prepared prompt, copies it to the Windows clipboard,
opens the selected AI chat in your default browser, then reads the
response back from the clipboard after you paste + submit + copy.

Subcommands:
    pick      Refill backlog.txt with new product suggestions.
    research  Gather research notes for an upcoming issue.

Providers:
    claude    https://claude.ai/new
    chatgpt   https://chatgpt.com/
    gemini    https://gemini.google.com/app

Requires no Python packages. Uses Windows PowerShell for clipboard I/O.
"""

from __future__ import annotations

import argparse
import datetime as dt
import re
import subprocess
import sys
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ISSUES_DIR = ROOT / "issues"
NOTES_DIR = ROOT / "notes"
BACKLOG_FILE = ROOT / "backlog.txt"
PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"

PROVIDERS = {
    "claude": "https://claude.ai/new",
    "chatgpt": "https://chatgpt.com/",
    "gemini": "https://gemini.google.com/app",
}

MONTHS = ("", "January", "February", "March", "April", "May", "June",
          "July", "August", "September", "October", "November", "December")

ISSUE_FILE_RE = re.compile(r"^(\d{3})-([a-z0-9\-]+)\.html$")


# --- Dates & slugs -----------------------------------------------------
def next_tuesday() -> dt.date:
    d = dt.date.today()
    delta = (1 - d.weekday()) % 7
    if delta == 0:
        delta = 7
    return d + dt.timedelta(days=delta)


def slugify(s: str) -> str:
    s = s.lower().replace("&", "and")
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s or "product"


# --- Clipboard (Windows PowerShell) -----------------------------------
import tempfile


def clip_copy(text: str) -> None:
    """Copy a string to the Windows clipboard via PowerShell Set-Clipboard.

    PowerShell's stdin pipeline mangles non-ASCII on Windows 10/11, so we
    stage through a UTF-8 BOM'd temp file that PowerShell can read back
    losslessly with -Encoding utf8.
    """
    fd, path = tempfile.mkstemp(suffix=".clip.txt")
    try:
        import os
        with os.fdopen(fd, "wb") as f:
            f.write(b"\xef\xbb\xbf")
            f.write(text.encode("utf-8"))
        script = f"Get-Content -Raw -Encoding utf8 -LiteralPath '{path}' | Set-Clipboard"
        r = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", script],
            capture_output=True,
        )
        if r.returncode != 0:
            sys.stderr.write(r.stderr.decode("utf-8", errors="replace"))
            raise RuntimeError("Set-Clipboard failed")
    finally:
        Path(path).unlink(missing_ok=True)


def clip_paste() -> str:
    """Read the Windows clipboard as UTF-8 via PowerShell.

    We stage through a temp file again because powershell's stdout is
    code-page-encoded and will lossily transcode non-ASCII on older consoles.
    """
    fd, path = tempfile.mkstemp(suffix=".paste.txt")
    import os
    os.close(fd)
    try:
        script = (
            f"Get-Clipboard -Raw | Out-File -FilePath '{path}' "
            "-Encoding utf8 -NoNewline"
        )
        r = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", script],
            capture_output=True,
        )
        if r.returncode != 0:
            sys.stderr.write(r.stderr.decode("utf-8", errors="replace"))
            raise RuntimeError("Get-Clipboard failed")
        data = Path(path).read_bytes()
        if data.startswith(b"\xef\xbb\xbf"):
            data = data[3:]
        return data.decode("utf-8", errors="replace").rstrip("\r\n")
    finally:
        Path(path).unlink(missing_ok=True)


# --- Scans -------------------------------------------------------------
ARTICLE_H1_RE = re.compile(r'<h1 class="article-title">(.*?)</h1>', re.DOTALL)
SUBJECT_BYLINE_RE = re.compile(
    r'<span>Subject:\s*<strong>(.*?)</strong></span>', re.DOTALL)


def _strip_html(s: str) -> str:
    s = re.sub(r"<br\s*/?>", " ", s, flags=re.I)
    s = re.sub(r"<[^>]+>", "", s)
    s = (s.replace("&mdash;", "\u2014")
           .replace("&ndash;", "\u2013")
           .replace("&rsquo;", "\u2019")
           .replace("&lsquo;", "\u2018")
           .replace("&ldquo;", "\u201c")
           .replace("&rdquo;", "\u201d")
           .replace("&amp;", "&")
           .replace("&nbsp;", " ")
           .replace("&middot;", "\u00b7")
           .replace("&hellip;", "\u2026")
           .replace("&#8209;", "-"))
    return re.sub(r"\s+", " ", s).strip()


def load_covered() -> list[tuple[int, str, str, str]]:
    """Return [(num, slug_stub, display_title, subject_label)]."""
    if not ISSUES_DIR.exists():
        return []
    out = []
    for p in sorted(ISSUES_DIR.iterdir()):
        m = ISSUE_FILE_RE.match(p.name.lower())
        if not m:
            continue
        num = int(m.group(1))
        stub = m.group(2)
        title = stub.title()
        subject = stub.title()
        try:
            src = p.read_text(encoding="utf-8")
            tm = ARTICLE_H1_RE.search(src)
            if tm:
                title = _strip_html(tm.group(1)).rstrip(".")
            sm = SUBJECT_BYLINE_RE.search(src)
            if sm:
                subject = _strip_html(sm.group(1))
        except OSError:
            pass
        out.append((num, stub, title, subject))
    out.sort(key=lambda x: x[0])
    return out


def load_backlog() -> list[str]:
    if not BACKLOG_FILE.exists():
        return []
    return [ln.strip() for ln in BACKLOG_FILE.read_text(encoding="utf-8").splitlines()
            if ln.strip() and not ln.strip().startswith("#")]


def append_backlog(new_items: list[str]) -> list[str]:
    existing = {x.lower() for x in load_backlog()}
    added: list[str] = []
    current = ""
    if BACKLOG_FILE.exists():
        current = BACKLOG_FILE.read_text(encoding="utf-8")
        if current and not current.endswith("\n"):
            current += "\n"
    lines_out = [current]
    for item in new_items:
        if item.lower() in existing:
            continue
        lines_out.append(item + "\n")
        existing.add(item.lower())
        added.append(item)
    BACKLOG_FILE.write_text("".join(lines_out), encoding="utf-8")
    return added


# --- Template rendering ------------------------------------------------
def render_template(path: Path, replacements: dict[str, str]) -> str:
    text = path.read_text(encoding="utf-8")
    for k, v in replacements.items():
        text = text.replace("{{" + k + "}}", v)
    return text


# --- Pick response parsing --------------------------------------------
PICK_ROW_RE = re.compile(r"^\s*[-*]\s*\*\*([^*]+?)\*\*\s*(?:[\u2014\u2013\-:]|$)")


def parse_pick_response(text: str) -> list[str]:
    names: list[str] = []
    seen: set[str] = set()
    in_top3 = False
    for line in text.splitlines():
        if re.match(r"^\s*#+\s*(my\s*)?top\s*3", line, re.I):
            in_top3 = True
            continue
        if in_top3:
            continue
        m = PICK_ROW_RE.match(line)
        if not m:
            continue
        name = m.group(1).strip().rstrip(".")
        name = re.sub(r"\s*\([^)]*\)\s*$", "", name)
        if not name or name.lower() in seen:
            continue
        seen.add(name.lower())
        names.append(name)
    return names


# --- Subcommands -------------------------------------------------------
def prompt_user_to_copy(target: str) -> str:
    print()
    print(f"Target: {target}")
    print()
    print("STEPS:")
    print("  1. In the chat window, press Ctrl+V, then Enter.")
    print("  2. Wait for the response to finish.")
    print("  3. Select the whole response and press Ctrl+C.")
    print("  4. Come back here and press Enter.")
    print()
    input("Press Enter when the response is on your clipboard: ")
    response = clip_paste()
    if not response.strip():
        print("Clipboard is empty; aborting.")
        sys.exit(2)
    return response


def cmd_pick(args: argparse.Namespace) -> int:
    covered = load_covered()
    backlog = load_backlog()

    covered_block = "\n".join(
        f"- Issue \u2116{num:02d}: **{subject}** ({title})"
        for num, _stub, title, subject in covered
    ) or "_(none yet)_"
    backlog_block = "\n".join(f"- {x}" for x in backlog) or "_(empty)_"

    prompt = render_template(
        PROMPTS_DIR / "pick_products.md",
        {"COVERED": covered_block, "BACKLOG": backlog_block},
    )

    clip_copy(prompt)
    url = PROVIDERS[args.provider]
    print(f"[prompt copied to clipboard \u2014 {len(prompt)} chars]")
    print(f"[opening {url}]")
    webbrowser.open(url)

    response = prompt_user_to_copy(f"refill backlog via {args.provider}")

    NOTES_DIR.mkdir(exist_ok=True)
    raw_path = NOTES_DIR / f"pick-{dt.date.today().isoformat()}.md"
    raw_path.write_text(response, encoding="utf-8")
    print(f"[raw response saved: {raw_path.relative_to(ROOT)}]")

    items = parse_pick_response(response)
    if not items:
        print("[warning] could not parse any product names from the response.")
        print("          inspect the raw file and add entries to backlog.txt manually.")
        return 1

    added = append_backlog(items)
    print(f"[parsed {len(items)} candidates \u2014 added {len(added)} to backlog.txt]")
    for item in added:
        print(f"  + {item}")
    skipped = len(items) - len(added)
    if skipped:
        print(f"[skipped {skipped} duplicates already covered or queued]")
    return 0


def cmd_research(args: argparse.Namespace) -> int:
    product = args.product.strip()
    if not product:
        print("--product is required")
        return 2

    covered = load_covered()
    next_num = (max(n for n, *_ in covered) if covered else 0) + 1
    if args.issue_num:
        next_num = args.issue_num

    publish = dt.date.fromisoformat(args.date) if args.date else next_tuesday()
    publish_str = f"{publish.day} {MONTHS[publish.month]} {publish.year}"

    prompt = render_template(
        PROMPTS_DIR / "research.md",
        {
            "PRODUCT": product,
            "ISSUE_NUM": f"{next_num:02d}",
            "PUBLISH_DATE": publish_str,
        },
    )

    clip_copy(prompt)
    url = PROVIDERS[args.provider]
    print(f"[prompt copied to clipboard \u2014 {len(prompt)} chars]")
    print(f"[opening {url}]")
    webbrowser.open(url)

    response = prompt_user_to_copy(
        f"Issue \u2116{next_num:02d} \u00b7 {product} \u00b7 {publish_str}")

    slug = f"{next_num:03d}-{slugify(product)}"
    NOTES_DIR.mkdir(exist_ok=True)
    out_path = NOTES_DIR / f"{slug}.md"
    header = (
        f"# Research notes \u2014 Issue \u2116{next_num:02d}: {product}\n\n"
        f"- Target publish: {publish_str}\n"
        f"- Provider: {args.provider}\n"
        f"- Gathered: {dt.date.today().isoformat()}\n\n"
        f"---\n\n"
    )
    out_path.write_text(header + response, encoding="utf-8")
    print(f"[notes saved: {out_path.relative_to(ROOT)} ({len(response)} chars)]")
    print()
    print("Next step \u2014 generate the draft:")
    print(f"  python tools\\write_issue.py --product \"{product}\"")
    return 0


# --- Entry point -------------------------------------------------------
def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Monograph Level-1 chat helper")
    sub = ap.add_subparsers(dest="cmd", required=True)

    pick = sub.add_parser("pick",
        help="Fill the backlog with AI-suggested products.")
    pick.add_argument("--provider", choices=list(PROVIDERS), default="claude")
    pick.set_defaults(func=cmd_pick)

    res = sub.add_parser("research",
        help="Gather research notes for an upcoming issue.")
    res.add_argument("--product", required=True,
                     help="Product name, e.g. \"Superhuman\".")
    res.add_argument("--provider", choices=list(PROVIDERS), default="claude")
    res.add_argument("--date", help="YYYY-MM-DD (default: next Tuesday).")
    res.add_argument("--issue-num", type=int,
                     help="Override issue number.")
    res.set_defaults(func=cmd_research)

    args = ap.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
