#!/usr/bin/env python3
"""Validate the generated profile before it goes out.

    python3 scripts/check_folio.py

Checks, in order of how badly each one bites:

  assets      every image the README references exists on disk
  xml         every generated SVG parses
  contrast    every text colour clears WCAG AA against what sits behind it
  alt text    every image carries a non-empty alt attribute
  links       every URL in data/ is well formed and uses https
  freshness   the committed output matches what the data would build now

Exit code is non-zero if anything fails, so this works as a CI gate.
Standard library only, and it never touches the network.
"""

import json
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from folio_theme import THEMES, contrast_ratio          # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
FOLIO = ROOT / "folio"
DATA = ROOT / "data"

AA_NORMAL = 4.5
AA_LARGE = 3.0


class Report:
    def __init__(self):
        self.failures = []
        self.checks = 0

    def ok(self, label):
        self.checks += 1
        print(f"  pass  {label}")

    def fail(self, label, detail):
        self.checks += 1
        self.failures.append((label, detail))
        print(f"  FAIL  {label}: {detail}")


def check_assets(r):
    print("assets")
    if not README.exists():
        r.fail("README.md", "missing, run build_folio.py")
        return
    text = README.read_text(encoding="utf-8")
    refs = set(re.findall(r'(?:srcset|src)="(folio/[^"]+)"', text))
    if not refs:
        r.fail("references", "README references no generated assets")
        return
    missing = [ref for ref in sorted(refs) if not (ROOT / ref).exists()]
    if missing:
        r.fail("referenced files", f"{len(missing)} missing, first is {missing[0]}")
    else:
        r.ok(f"{len(refs)} referenced assets present")

    on_disk = {f"folio/{p.name}" for p in FOLIO.glob("*.svg")}
    orphans = sorted(on_disk - refs)
    if orphans:
        r.fail("orphans", f"{len(orphans)} built but unreferenced, first is {orphans[0]}")
    else:
        r.ok("no orphaned assets")


def check_xml(r):
    print("xml")
    bad = []
    for path in sorted(FOLIO.glob("*.svg")):
        try:
            ET.parse(path)
        except ET.ParseError as exc:
            bad.append(f"{path.name}: {exc}")
    if bad:
        r.fail("svg parse", bad[0])
    else:
        r.ok(f"{len(list(FOLIO.glob('*.svg')))} SVGs parse")


def check_contrast(r):
    print("contrast")
    # (foreground token, background token, size class) pairs actually used
    pairs = [
        ("ink", "bg", "large"),      # handle, figures
        ("ink", "panel", "normal"),  # card titles
        ("chrome", "bg", "normal"),
        ("chrome", "panel", "normal"),
        ("dim", "bg", "normal"),
        ("dim", "panel", "normal"),
        ("accent", "bg", "normal"),
    ]
    worst = None
    for theme, pal in THEMES.items():
        for fg, bg, size in pairs:
            ratio = contrast_ratio(pal[fg], pal[bg])
            floor = AA_LARGE if size == "large" else AA_NORMAL
            label = f"{theme}: {fg} on {bg}"
            if ratio < floor:
                r.fail(label, f"{ratio:.2f}:1, needs {floor}:1")
            elif worst is None or ratio < worst[1]:
                worst = (label, ratio)
    if worst:
        r.ok(f"all pairs clear AA, tightest is {worst[0]} at {worst[1]:.2f}:1")


def check_alt(r):
    print("alt text")
    if not README.exists():
        return
    imgs = re.findall(r"<img ([^>]+)>", README.read_text(encoding="utf-8"))
    empty = [a for a in imgs if not re.search(r'alt="[^"]+"', a)]
    if empty:
        r.fail("alt", f"{len(empty)} of {len(imgs)} images have no alt text")
    else:
        r.ok(f"{len(imgs)} images carry alt text")


def check_links(r):
    print("links")
    urls = []
    profile = json.loads((DATA / "profile.json").read_text(encoding="utf-8"))
    urls += [l["url"] for l in profile.get("links", [])]
    repos = json.loads((DATA / "repos.json").read_text(encoding="utf-8"))
    for section in repos["sections"]:
        urls += [x["url"] for x in section["repos"]]

    bad = [u for u in urls if not re.match(r"^https://[\w.-]+\.[a-z]{2,}(/|$)", u)]
    if bad:
        r.fail("url shape", f"{bad[0]} is not a well formed https URL")
    else:
        r.ok(f"{len(urls)} URLs well formed")

    dupes = {u for u in urls if urls.count(u) > 1}
    if dupes:
        r.fail("duplicates", f"{sorted(dupes)[0]} appears more than once")
    else:
        r.ok("no duplicate URLs")


def check_freshness(r):
    print("freshness")
    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "build_folio.py"), "--check"],
        capture_output=True, text=True,
    )
    if proc.returncode == 0:
        r.ok("committed output matches the data")
    else:
        first = next((l.strip() for l in proc.stdout.splitlines()[1:] if l.strip()), "unknown")
        r.fail("stale output", f"re-run build_folio.py, starting with {first}")


def main():
    r = Report()
    check_assets(r)
    check_xml(r)
    check_contrast(r)
    check_alt(r)
    check_links(r)
    check_freshness(r)

    print()
    if r.failures:
        print(f"{len(r.failures)} of {r.checks} checks failed")
        return 1
    print(f"all {r.checks} checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
