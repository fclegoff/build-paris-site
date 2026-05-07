#!/usr/bin/env python3
"""
Build index.html from index.template.html + data/posts.json.
Replaces markers:
  <!-- @PROJECT_ROWS@ -->     → editorial list rows (with cursor preview data)
  <!-- @INSTAGRAM_FEED@ -->   → 12-thumb square grid
"""

import json
import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "index.template.html"
OUTPUT = ROOT / "index.html"
DATA = ROOT / "data" / "posts.json"


def get_year(post):
    ts = post.get("timestamp")
    if ts:
        try:
            return str(datetime.datetime.fromtimestamp(ts).year)
        except Exception:
            pass
    return "2026"


def render_rows(posts):
    """Editorial list — title, client, year. Hover loads preview image."""
    out = []
    for p in posts:
        title = p.get("title", "Set construction").replace('"', '&quot;')
        client = p.get("client", "BUILD")
        year = get_year(p)
        out.append(f'''      <li class="row" data-preview="{p["image"]}">
        <a href="{p["url"]}" target="_blank">
          <span class="row-title">{title}</span>
          <span class="row-meta">{client}</span>
          <span class="row-year">{year}</span>
        </a>
      </li>''')
    return "\n".join(out)


def render_insta(posts):
    """12-thumb square Instagram grid."""
    out = []
    for p in posts[:12]:
        out.append(f'''      <a href="{p["url"]}" target="_blank" class="insta-thumb" title="{p["client"]}">
        <img src="{p["image"]}" alt="{p["client"]}" loading="lazy">
      </a>''')
    return "\n".join(out)


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
    html = html.replace("<!-- @PROJECT_ROWS@ -->", render_rows(posts))
    html = html.replace("<!-- @INSTAGRAM_FEED@ -->", render_insta(posts))

    OUTPUT.write_text(html, encoding="utf-8")
    print(f"✅ Wrote {OUTPUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
