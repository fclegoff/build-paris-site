#!/usr/bin/env python3
"""
Build index.html from index.template.html + data/posts.json.
Replaces markers:
  <!-- @PROJECT_GRID@ -->     → portfolio grid (top 7 posts)
  <!-- @INSTAGRAM_FEED@ -->   → Instagram-style square grid (top 12 posts)
  <!-- @CLIENT_TICKER@ -->    → marquee with client names
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "index.template.html"
OUTPUT = ROOT / "index.html"
DATA = ROOT / "data" / "posts.json"


def render_grid(posts):
    """7-post hero grid with editorial layout."""
    out = []
    for p in posts[:7]:
        out.append(f'''      <a href="{p["url"]}" target="_blank" class="grid-item">
        <img src="{p["image"]}" alt="{p["client"]} — {p["title"]}" loading="lazy">
        <div class="grid-caption">
          <div class="client">{p["client"]}</div>
          <h3>{p["title"]}</h3>
        </div>
      </a>''')
    return "\n".join(out)


def render_insta(posts):
    """12-thumb square Instagram grid."""
    out = []
    for p in posts[:12]:
        out.append(f'''      <a href="{p["url"]}" target="_blank" class="insta-thumb" title="{p["client"]}">
        <img src="{p["image"]}" alt="{p["client"]}" loading="lazy">
      </a>''')
    return "\n".join(out)


def render_ticker(posts):
    """Client names ticker — unique, repeated twice for seamless loop."""
    seen, clients = set(), []
    for p in posts:
        c = p["client"]
        if c and c not in seen:
            seen.add(c)
            clients.append(c)

    items = "".join(
        f'<span class="ticker-item">{c} <span class="dot">·</span></span>'
        for c in clients
    )
    return items + items  # double for loop


def main():
    if not TEMPLATE.exists():
        print(f"❌ Missing template: {TEMPLATE}")
        return 1
    if not DATA.exists():
        print(f"❌ Missing data: {DATA} — run sync-instagram.py first")
        return 1

    data = json.loads(DATA.read_text(encoding="utf-8"))
    posts = data.get("posts", [])
    print(f"→ Building from {len(posts)} posts")

    html = TEMPLATE.read_text(encoding="utf-8")
    html = html.replace("<!-- @PROJECT_GRID@ -->", render_grid(posts))
    html = html.replace("<!-- @INSTAGRAM_FEED@ -->", render_insta(posts))
    html = html.replace("<!-- @CLIENT_TICKER@ -->", render_ticker(posts))

    OUTPUT.write_text(html, encoding="utf-8")
    print(f"✅ Wrote {OUTPUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
