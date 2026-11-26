#!/bin/sh
# Démarrage d'un conteneur SmartWater : attend MySQL, applique les migrations (service web), puis lance la commande.
set -e

echo "Attente de la base de données ${DB_HOST:-db}:${DB_PORT:-3306}..."
python - <<'PY'
import os, sys, time
import MySQLdb
for essai in range(60):
    try:
        MySQLdb.connect(host=os.environ.get('DB_HOST', 'db'), port=int(os.environ.get('DB_PORT', '3306')),
                        user=os.environ.get('DB_USER'), password=os.environ.get('DB_PASSWORD', ''),
                        database=os.environ.get('DB_NAME')).close()
        print('Base de données prête.')
        sys.exit(0)
    except MySQLdb.OperationalError as e:
        print(f'  pas encore prête ({e.args[0]}), nouvel essai dans 2 s')
        time.sleep(2)
sys.exit('Base de données injoignable après 2 minutes : vérifiez le service db et le fichier .env')
PY

if [ "${MIGRER:-1}" = "1" ]; then
    python manage.py migrate --noinput
fi

exec "$@"
