# Setup sync IG sur un Mac (transfert Carole)

Ce guide transfère le système de sync Instagram + auto-deploy depuis un Mac
vers un autre. Une fois en place, le site se met à jour 4×/jour sans
intervention humaine, tant que le Mac est allumé (ou se rallume au moins
une fois par semaine).

## Prérequis sur le nouveau Mac

```bash
# Vérifier Python 3 (macOS l'a généralement)
python3 --version   # doit dire 3.x

# Vérifier git
git --version

# Installer GitHub CLI si absent
brew install gh
```

Si `brew` n'est pas installé : https://brew.sh

## 1. Donner accès au repo GitHub

Sur le compte GitHub propriétaire du repo (`fclegoff`) :

1. Aller sur https://github.com/fclegoff/build-paris-site/settings/access
2. **Add people** → entrer le compte GitHub de la personne
3. Choisir rôle **Write** (ou **Admin** si elle gère aussi les secrets)

La personne reçoit une invitation par email. Elle doit accepter avant de
pouvoir push.

## 2. Cloner le repo et s'authentifier

Sur le Mac de la personne :

```bash
cd ~
gh auth login
# → Choisir GitHub.com → HTTPS → authentifier via navigateur

git clone https://github.com/fclegoff/build-paris-site.git build-site
cd build-site
```

Tester que le push fonctionne :

```bash
git commit --allow-empty -m "test access"
git push origin main
git reset --hard HEAD~1
git push --force-with-lease origin main   # rollback du test
```

## 3. Tester la sync manuellement

```bash
cd ~/build-site
python3 scripts/sync-instagram.py
# → doit afficher "✅ X projects · Y new images · Z skipped"
# → si "rate-limited 429", c'est cassé (ne devrait PAS arriver depuis IP résidentielle)
```

## 4. Installer le launchd cron

Créer le fichier plist (remplacer `USERNAME` par le nom du user macOS) :

```bash
# Trouver l'username
whoami
# → ex: carole

# Créer le plist (ajuster les chemins)
cat > ~/Library/LaunchAgents/com.build-paris.sync.plist <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.build-paris.sync</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>/Users/USERNAME/build-site/scripts/local-sync.sh</string>
    </array>
    <key>StartCalendarInterval</key>
    <array>
        <dict><key>Hour</key><integer>9</integer><key>Minute</key><integer>0</integer></dict>
        <dict><key>Hour</key><integer>13</integer><key>Minute</key><integer>0</integer></dict>
        <dict><key>Hour</key><integer>17</integer><key>Minute</key><integer>0</integer></dict>
        <dict><key>Hour</key><integer>21</integer><key>Minute</key><integer>0</integer></dict>
    </array>
    <key>StandardOutPath</key>
    <string>/Users/USERNAME/build-site/.sync.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/USERNAME/build-site/.sync.log</string>
    <key>WorkingDirectory</key>
    <string>/Users/USERNAME/build-site</string>
    <key>RunAtLoad</key>
    <true/>
</dict>
</plist>
PLIST

# IMPORTANT : remplacer USERNAME dans le fichier généré
sed -i '' "s/USERNAME/$(whoami)/g" ~/Library/LaunchAgents/com.build-paris.sync.plist
```

Charger :

```bash
launchctl load ~/Library/LaunchAgents/com.build-paris.sync.plist
launchctl list | grep build-paris
# → doit afficher : <PID>  0  com.build-paris.sync (ou "-" puis exit code 0)
```

`RunAtLoad: true` lance immédiatement une sync — vérifier dans les 10 secondes :

```bash
tail -20 ~/build-site/.sync.log
# → doit se terminer par "no changes" ou "pushed updates"
```

## 5. Désactiver l'ancien Mac (chez fclg)

Une fois que ça tourne sur le nouveau Mac :

```bash
# Sur l'ancien Mac
launchctl unload ~/Library/LaunchAgents/com.build-paris.sync.plist
rm ~/Library/LaunchAgents/com.build-paris.sync.plist
```

Comme ça pas deux Macs qui pushent en même temps (risque de conflit git).

## Commandes utiles

```bash
# Forcer une sync immédiate
launchctl start com.build-paris.sync

# Voir les logs
tail -50 ~/build-site/.sync.log

# Vérifier le statut
launchctl list | grep build-paris

# Désactiver temporairement
launchctl unload ~/Library/LaunchAgents/com.build-paris.sync.plist

# Réactiver
launchctl load ~/Library/LaunchAgents/com.build-paris.sync.plist
```

## En cas de problème

- **Sync skip 429** : l'IP n'est PAS résidentielle (VPN allumé ? proxy d'entreprise ?). Désactiver VPN et retester.
- **Push refusé** : vérifier `gh auth status`, refaire `gh auth login` si besoin.
- **Le job ne se lance pas à l'heure prévue** : Mac en veille profonde — `RunAtLoad: true` rattrapera au prochain réveil.
- **Job marqué comme "0 -" mais pas de log** : vérifier le chemin du `local-sync.sh` dans le plist (typo USERNAME ?).
