#!/usr/bin/env python3
"""
Sync @build.paris Instagram posts to local data + images.
Outputs:
  - data/posts.json
  - img/ig-<shortcode>.jpg
"""

import json
import os
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
IMG_DIR = ROOT / "img"
DATA_DIR = ROOT / "data"
IMG_DIR.mkdir(exist_ok=True)
DATA_DIR.mkdir(exist_ok=True)

USERNAME = "build.paris"
APP_ID = "936619743392459"
USER_AGENT = "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15"

# Manual client → display name mapping (clean Instagram handles into proper brand names)
CLIENT_MAP = {
    "chaumetofficial":      "Chaumet",
    "solebox":              "Adidas Originals × Solebox",
    "adidasoriginals":      "Adidas Originals × Solebox",
    "palomawool":           "Paloma Wool",
    "ashistudio":           "Ashi Studio",
    "0800shygirl":          "Shygirl × Centre Pompidou",
    "becausemusic":         "Shygirl × Centre Pompidou",
    "centrepompidou":       "Shygirl × Centre Pompidou",
    "theodorabosslady":     "Miss Kitoko — SM4LL",
    "frederickasseo":       "Too Faced",
    "too_faced":            "Too Faced",
    "toofaced":             "Too Faced",
    "build.paris":          None,  # skip self-reference
    "kitty_events":         "Ashi Studio × Kitty",
}

# Title overrides per shortcode (cleaner than auto-extracted titles)
TITLE_OVERRIDES = {
    "DXOpqyLjH_p": "A Peachy Summer",
    "DXEYKTojJnQ": "Pop-up store · Rue de Turenne",
    "DWBbJf7jPge": "SM4LL — Music video set",
    "DVBIVrgEd2D": "SS26 Couture — Fashion show",
    "DUY1h9aDK_4": "The Beginnings — SS26 Couture",
    "DT269OCDNj6": "ALIAS — Sensory Exhibition",
    "DT26HPCDI8V": "ALIAS — Sensory Exhibition",
    "DT0V4oADD9B": "Solebox × Adidas Originals",
    "DT0UFJHjNTt": "Set design — Shooting Chaumet",
}


class RateLimited(Exception):
    pass


def fetch_profile():
    url = f"https://www.instagram.com/api/v1/users/web_profile_info/?username={USERNAME}"
    req = urllib.request.Request(url, headers={
        "User-Agent": USER_AGENT,
        "X-IG-App-ID": APP_ID,
        "Accept": "application/json",
    })
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        if e.code in (401, 403, 429):
            raise RateLimited(f"Instagram rate-limited or auth-required (HTTP {e.code})")
        raise


def detect_client(caption: str) -> str:
    """Find the best client display name from caption mentions."""
    if not caption:
        return None

    # 1. Try "Brand : @xxx" pattern first (most reliable)
    m = re.search(r"Brand\s*:\s*@(\w[\w.]+)", caption, re.IGNORECASE)
    handles = []
    if m:
        handles.append(m.group(1).lower())

    # 2. Collect all @mentions in order
    handles.extend(re.findall(r"@(\w[\w.]+)", caption.lower()))

    # 3. Match against CLIENT_MAP, return first non-null
    seen = set()
    for h in handles:
        if h in seen:
            continue
        seen.add(h)
        if h in CLIENT_MAP:
            mapped = CLIENT_MAP[h]
            if mapped:
                return mapped
        else:
            # Unknown handle → titlecase it as fallback
            pretty = h.replace("_", " ").replace(".", " ").title()
            if pretty.lower() != "build paris":
                return pretty
    return None


def is_project_post(caption: str, shortcode: str) -> bool:
    """Filter out branding/identity cards."""
    if shortcode in TITLE_OVERRIDES:
        return True  # explicit project
    cap = (caption or "").strip()
    if not cap:
        return False
    if cap.lower().startswith("@build.paris") and len(cap) < 80:
        return False
    return True


def download(url: str, target: Path) -> bool:
    if target.exists() and target.stat().st_size > 5_000:
        return False
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Referer": "https://www.instagram.com/",
        })
        with urllib.request.urlopen(req, timeout=20) as r:
            target.write_bytes(r.read())
        return True
    except Exception as e:
        print(f"  ❌ {target.name}: {e}", file=sys.stderr)
        return False


def main():
    print(f"→ Fetching @{USERNAME}…")
    try:
        raw = fetch_profile()
    except RateLimited as e:
        print(f"⚠ {e}")
        print("✋ Skipping sync — keeping existing data/posts.json + img/.")
        print("   (GitHub Actions IPs are often rate-limited by Instagram.")
        print("    Run `python3 scripts/sync-instagram.py` locally to refresh.)")
        return 0
    user = raw["data"]["user"]
    posts_raw = user.get("edge_owner_to_timeline_media", {}).get("edges", [])
    print(f"  found {len(posts_raw)} posts")

    posts = []
    new_downloads = 0
    skipped = 0

    for edge in posts_raw:
        node = edge["node"]
        shortcode = node.get("shortcode")
        if not shortcode:
            continue

        cap_edges = node.get("edge_media_to_caption", {}).get("edges", [])
        caption = cap_edges[0]["node"]["text"] if cap_edges else ""

        if not is_project_post(caption, shortcode):
            print(f"  ⏭  skip {shortcode}")
            skipped += 1
            continue

        target = IMG_DIR / f"ig-{shortcode}.jpg"
        if download(node["display_url"], target):
            new_downloads += 1
            print(f"  ⬇  {target.name}")

        client = detect_client(caption)
        title = TITLE_OVERRIDES.get(shortcode)
        if not title and caption:
            title = caption.strip().split("\n")[0][:80]

        posts.append({
            "shortcode": shortcode,
            "url": f"https://www.instagram.com/p/{shortcode}/",
            "image": f"/img/ig-{shortcode}.jpg",
            "client": client or "BUILD",
            "title": title or "Set construction",
            "caption": caption,
            "is_video": node.get("is_video", False),
            "likes": node.get("edge_liked_by", {}).get("count", 0),
            "timestamp": node.get("taken_at_timestamp"),
        })

    out = {
        "username": USERNAME,
        "name": user.get("full_name"),
        "bio": user.get("biography"),
        "followers": user.get("edge_followed_by", {}).get("count"),
        "post_count_total": user.get("edge_owner_to_timeline_media", {}).get("count"),
        "posts": posts,
    }
    DATA_DIR.joinpath("posts.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8",
    )

    print(f"\n✅ {len(posts)} projects · {new_downloads} new images · {skipped} skipped")
    return 0


if __name__ == "__main__":
    sys.exit(main())
