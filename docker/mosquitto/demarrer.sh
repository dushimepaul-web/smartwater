#!/bin/sh
# Crée le fichier de mots de passe à partir de MQTT_USER / MQTT_PASSWORD (.env), puis lance Mosquitto.
set -e
if [ -z "$MQTT_USER" ] || [ -z "$MQTT_PASSWORD" ]; then
    echo "MQTT_USER et MQTT_PASSWORD doivent être définis dans .env" >&2
    exit 1
fi
rm -f /mosquitto/data/passwd
mosquitto_passwd -b -c /mosquitto/data/passwd "$MQTT_USER" "$MQTT_PASSWORD"
chown mosquitto:mosquitto /mosquitto/data/passwd
chmod 0700 /mosquitto/data/passwd
exec mosquitto -c /mosquitto/config/mosquitto.conf
