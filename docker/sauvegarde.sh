#!/bin/sh
# Sauvegarde de la base MySQL dans ./sauvegardes (garde les 14 dernières).
#   ./docker/sauvegarde.sh
# Tous les jours à 2 h (crontab -e) :
#   0 2 * * * cd /opt/smartwater && ./docker/sauvegarde.sh >> sauvegardes/journal.log 2>&1
set -e
cd "$(dirname "$0")/.."
mkdir -p sauvegardes
FICHIER="sauvegardes/smartwater_$(date +%Y-%m-%d_%H%M).sql.gz"
docker compose exec -T db sh -c 'mysqldump -u root -p"$MYSQL_ROOT_PASSWORD" --single-transaction --routines "$MYSQL_DATABASE"' | gzip > "$FICHIER"
echo "Sauvegarde créée : $FICHIER"
ls -1t sauvegardes/smartwater_*.sql.gz | tail -n +15 | xargs -r rm --
