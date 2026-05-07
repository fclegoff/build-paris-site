# build-paris.com

Site officiel de **BUILD** — Production design & set building workshop, Pantin (93).

## Stack

- **Hébergement** — Cloudflare Pages (build automatique sur push GitHub)
- **CDN** — Cloudflare global
- **Source de contenu** — [@build.paris](https://www.instagram.com/build.paris/) sur Instagram

## Architecture

```
GitHub repo
   ├── index.template.html   → template avec marqueurs
   ├── scripts/
   │   ├── sync-instagram.py → fetch IG → posts.json + /img
   │   └── build-site.py     → template + posts.json → index.html
   ├── data/posts.json       → métadonnées posts (auto-généré)
   ├── img/ig-*.jpg          → photos Instagram (auto-téléchargées)
   └── index.html            → site final (auto-généré)
```

## Auto-sync Instagram

GitHub Action `Sync Instagram` :

- ⏰ S'exécute **toutes les 6 heures** (cron)
- 🔄 Récupère les nouveaux posts @build.paris
- 📥 Télécharge les nouvelles images dans `/img/ig-<shortcode>.jpg`
- 🏗️ Reconstruit `index.html` à partir du template
- 📤 Commit + push automatique → **Cloudflare Pages redéploie**

→ Quand BUILD poste sur Instagram, le site est à jour dans les 6h sans intervention.

## Run manuel local

```bash
python3 scripts/sync-instagram.py   # fetch IG
python3 scripts/build-site.py        # rebuild HTML
```

## Run manuel sur GitHub

GitHub → Actions → "Sync Instagram" → **Run workflow**

## Déploiement initial

```bash
# Lier le repo à Cloudflare Pages
wrangler pages project create build-paris-site --production-branch main
wrangler pages deploy . --project-name build-paris-site
```

DNS — pointer build-paris.com sur Cloudflare en changeant les nameservers chez OVH.

---

Site par [1.618](https://1618-films.tv) · Powered by Claude Code
