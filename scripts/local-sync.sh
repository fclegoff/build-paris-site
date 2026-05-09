#!/bin/bash
# Local Instagram sync wrapper for launchd cron.
# Syncs IG, rebuilds, pushes if changes.
# Logs to .sync.log in repo root.

set -u
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO"

LOG=".sync.log"
ts() { date '+%Y-%m-%d %H:%M:%S'; }

# Cap log size to last 500 lines
if [ -f "$LOG" ] && [ "$(wc -l < "$LOG")" -gt 500 ]; then
  tail -500 "$LOG" > "$LOG.tmp" && mv "$LOG.tmp" "$LOG"
fi

echo "[$(ts)] === sync run ===" >> "$LOG"

# Network reachability (10s timeout)
if ! /usr/bin/curl -sfI -m 10 https://www.instagram.com/ -o /dev/null; then
  echo "[$(ts)] no network or IG unreachable, skip" >> "$LOG"
  exit 0
fi

# Resolve git/python from PATH (launchd has minimal env)
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin"

# Pull rebase to avoid conflict with manual pushes
if ! git pull --rebase --autostash origin main >> "$LOG" 2>&1; then
  echo "[$(ts)] git pull failed, abort" >> "$LOG"
  exit 1
fi

# Sync + build
python3 scripts/sync-instagram.py >> "$LOG" 2>&1 || { echo "[$(ts)] sync failed" >> "$LOG"; exit 1; }
python3 scripts/build-site.py >> "$LOG" 2>&1 || { echo "[$(ts)] build failed" >> "$LOG"; exit 1; }

# Stage relevant paths only
git add data/posts.json img/ index.html

if git diff --staged --quiet; then
  echo "[$(ts)] no changes" >> "$LOG"
  exit 0
fi

git commit -m "Auto-sync Instagram posts $(date '+%Y-%m-%d %H:%M')" >> "$LOG" 2>&1
if git push origin main >> "$LOG" 2>&1; then
  echo "[$(ts)] pushed updates" >> "$LOG"
else
  echo "[$(ts)] push failed" >> "$LOG"
  exit 1
fi
