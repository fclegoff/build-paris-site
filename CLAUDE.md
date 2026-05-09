# build-paris.com — contexte projet

Site officiel de **BUILD construction** (atelier décor pub Pantin 93), réalisé par 1.618.

## Identité
- **Prod** : https://build-paris.com (alias : `build-paris.pages.dev`)
- **Repo** : https://github.com/fclegoff/build-paris-site
- **Cloudflare project** : `build-paris`, account `ed0807f1ed88eaa30527e465984dc91a`

## Stack
- **Hébergement** : Cloudflare Pages (auto-deploy sur push `main`)
- **Source contenu** : Instagram @build.paris (9 projets affichés, posts brand filtrés via `is_project_post()` dans `sync-instagram.py`)
- **Build** : statique. `index.template.html` + `data/posts.json` → `scripts/build-site.py` → `index.html`
- **Sync IG** : `scripts/sync-instagram.py` (web API publique non authentifiée)
- **Bilingue** : FR/EN via spans `lang="fr"` / `lang="en"`, switch JS persiste en localStorage + URL

## Brand (depuis logo)
- Violet primaire : `#7B40FF`
- Noir : `#0F0F12`
- Variables CSS : `--violet`, `--black` dans `index.template.html`
- Police : Helvetica Neue
- Drapeaux 🇫🇷/🇬🇧 22px pour le switch langue (active : couleur pleine + scale 1.05 ; inactive : grayscale 60% + opacity 55%)

## Workflow dev
```bash
# 1. Modifier index.template.html (NE PAS toucher index.html — généré)
# 2. Rebuild
python3 scripts/build-site.py
# 3. Tester en local
python3 -m http.server 8000
# 4. Push → Cloudflare deploy auto
git push origin main
```

## Sync Instagram — point critique

**Problème** : Instagram rate-limite (HTTP 429) toutes les IPs des cloud providers (GitHub Actions, GCP, AWS, Azure). La sync depuis GitHub Actions échoue en silence (`✋ Skipping sync — keeping existing data`).

**Solution actuelle** : `launchd` sur la machine de @fclegoff
- Plist : `~/Library/LaunchAgents/com.build-paris.sync.plist`
- Wrapper : `scripts/local-sync.sh`
- Schedule : 9h, 13h, 17h, 21h heure Paris + `RunAtLoad: true` (sync immédiate au login si Mac était off)
- Logs : `.sync.log` (gitignored)
- IP résidentielle → pas blacklistée

**Si Mac off plusieurs jours** : la sync rattrape automatiquement au prochain login grâce à `RunAtLoad`.

**Si besoin always-on 24/7** : passer à l'**Instagram Graph API** sur VM GCP free-tier.
- Convertir @build.paris en compte Business/Creator (gratuit, 1 clic)
- Lier page Facebook
- Créer app Meta Developer
- Long-lived access token 60j (refresh API auto)
- Réécrire `sync-instagram.py` côté API officielle (~2h dev)
- Coût : 0€, zéro maintenance

**À ne jamais faire** : essayer de remettre la sync sur GitHub Actions, AWS Lambda, GCP Cloud Functions. C'est bloqué.

## GitHub Actions
- `.github/workflows/instagram-sync.yml` — cron 6h, fallback (skip 429). Reste en place mais ne fait rien d'utile actuellement.
- `.github/workflows/deploy.yml` — push main → wrangler pages deploy
- **Secret requis** : `CLOUDFLARE_API_TOKEN` (permission `Cloudflare Pages: Edit`, sans expiry recommandé). Régénérer sur https://dash.cloudflare.com/profile/api-tokens
- **Secret** : `CLOUDFLARE_ACCOUNT_ID` = `ed0807f1ed88eaa30527e465984dc91a`

## Contacts BUILD
- **Carole** : carole@build-paris.com · +33 6 85 51 50 06 (devis + opérations)
- **Atelier** : 62 rue Denis Papin, 93500 Pantin

## Architecture des fichiers
```
index.template.html       # template avec marqueurs @PROJECT_ROWS@ / @INSTAGRAM_FEED@
scripts/
  build-site.py           # template → index.html
  sync-instagram.py       # IG → posts.json + img/ig-*.jpg
  local-sync.sh           # wrapper launchd (sync + build + push si changements)
data/posts.json           # généré, ne pas éditer à la main
img/ig-<shortcode>.jpg    # photos IG téléchargées
.github/workflows/        # CI deploy + sync (sync ne marche que pour fallback)
favicon.svg               # logo violet bg + BUILD noir
```

## Mappings manuels dans sync-instagram.py
- `CLIENT_MAP` : handles IG → noms de marque propres (ex: `chaumetofficial` → "Chaumet")
- `TITLE_OVERRIDES` : shortcode IG → titre projet propre (les titres auto-extraits du caption sont parfois moches)
- À mettre à jour quand BUILD poste un nouveau projet avec une marque pas encore mappée
