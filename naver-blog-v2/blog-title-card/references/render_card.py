"""Render a 1080x1080 blog title card with headless Chrome. No extra packages.

Usage:
  python render_card.py --bg card_bg.png --out card.png \
      --tag "Short label" --chip "Small line above the title" \
      --l1 "Title line 1" --l2 "Title line 2 with <u>underlined</u> word" \
      --sub "One sentence under the title" [--accent "#ffb347"] [--zoom 1.12]

Needs Google Chrome (or Edge/Chromium) installed. Pass --chrome PATH if it is not found.
Use only text you are allowed to publish. Keep lines short: ~12 Korean characters per line at this size.
"""
import argparse
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

CANDIDATES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/usr/bin/google-chrome",
    "/usr/bin/chromium",
    "/usr/bin/chromium-browser",
]


def find_chrome(explicit):
    if explicit:
        return explicit
    for c in CANDIDATES:
        if os.path.exists(c):
            return c
    for name in ("google-chrome", "chromium", "chrome", "msedge"):
        p = shutil.which(name)
        if p:
            return p
    sys.exit("Chrome not found. Pass --chrome PATH.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bg", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--tag", default="")
    ap.add_argument("--chip", default="")
    ap.add_argument("--l1", default="")
    ap.add_argument("--l2", default="")
    ap.add_argument("--sub", default="")
    ap.add_argument("--accent", default="#ffb347")
    ap.add_argument("--zoom", default="1.12")
    ap.add_argument("--chrome", default="")
    a = ap.parse_args()

    here = pathlib.Path(__file__).resolve().parent
    html = (here / "card_template.html").read_text(encoding="utf-8")
    bg = pathlib.Path(a.bg).resolve().as_uri()
    for k, v in {"BG": bg, "ACCENT": a.accent, "ZOOM": a.zoom, "TAG": a.tag, "CHIP": a.chip,
                 "L1": a.l1, "L2": a.l2, "SUB": a.sub}.items():
        html = html.replace("{{" + k + "}}", v)

    tmp = pathlib.Path(tempfile.mkdtemp()) / "card.html"
    tmp.write_text(html, encoding="utf-8")
    out = pathlib.Path(a.out).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    cmd = [find_chrome(a.chrome), "--headless=new", "--disable-gpu", "--hide-scrollbars",
           "--allow-file-access-from-files", "--window-size=1080,1080",
           f"--screenshot={out}", tmp.as_uri()]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=60)
    print("saved", out)


if __name__ == "__main__":
    main()
