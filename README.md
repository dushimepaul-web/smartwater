# SmartWater IoT – Surveillance du niveau d'eau

Application Django qui reçoit les mesures d'un **ESP32 + capteur ultrason**, calcule le niveau
d'eau, déclenche des alertes et affiche un tableau de bord en temps réel. Elle suit le
cahier des charges `SmartWater_IoT_Projet.pdf`, avec en plus une table **roles**.

```
ESP32 + JSN-SR04T/HC-SR04 ──HTTP POST /api/mesures/──┐
                          └─MQTT smartwater/capteurs/<id>/mesure─► mqtt_listener ─┤
                                                                                  ▼
                               Django (calcul du niveau, alertes, API REST) ── MySQL
                                                                                  ▲
                         Navigateur (pages Django, rafraîchies toutes les 5 s via l'API)
```

## Installation (Windows)

```bat
cd smartwater
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

1. Démarrez WAMP/XAMPP et créez une base vide **`smartwater`** (phpMyAdmin → Nouvelle base, interclassement `utf8mb4_unicode_ci`).
2. Créez les tables et les données de démonstration :

```bat
python manage.py migrate
python manage.py init_donnees
python manage.py runserver 0.0.0.0:8000
```

3. Ouvrez http://127.0.0.1:8000 et connectez-vous avec **admin@smartwater.local** / **SmartWater2026!**
   (changez ce mot de passe ensuite).

> Autre méthode : importer `db/smartwater.sql` dans phpMyAdmin. C'est le même schéma.
> `python manage.py migrate` ne fera alors plus rien.
>
> Essai sans MySQL : mettez `DB_ENGINE=sqlite` dans `.env`.

## Faire arriver des mesures

| Méthode | Commande |
|---|---|
| **Simulateur** (sans matériel) | `python manage.py simuler_capteur` (options : `--scenario vidange`, `--intervalle 5`) |
| Simulateur qui passe par l'API, comme un vrai ESP32 | `python manage.py simuler_capteur --http http://127.0.0.1:8000/api/mesures/` |
| **ESP32 en HTTP** | `firmware/esp32_smartwater/esp32_smartwater.ino` avec `MODE_HTTP` |
| **ESP32 en MQTT** | Broker Mosquitto + `python manage.py mqtt_listener`, firmware avec `MODE_MQTT` |

La clé d'API de chaque capteur se trouve dans **Réservoirs → Modifier**.

## Base de données

| Table | Champs principaux |
|---|---|
| `roles` | id_role, nom (admin, utilisateur, technicien…), libelle, description, est_administrateur |
| `utilisateurs` | id_utilisateur, nom, email, mot_de_passe (**haché**), id_role, actif, notif_email/push/son |
| `reservoirs` | id_reservoir, id_utilisateur, nom, emplacement, capacite_litres, seuil_bas, seuil_haut |
| `capteurs` | id_capteur, id_reservoir, modele, hauteur_cm, statut, cle_api, frequence_envoi_s, derniere_communication |
| `mesures` | id_mesure, id_capteur, distance_cm, niveau_pct, date_mesure |
| `alertes` | id_alerte, id_reservoir, type (niveau_bas, niveau_haut, info), message, lue, date_alerte |

Niveau (%) = (hauteur_cm − distance_cm) / hauteur_cm × 100, borné entre 0 et 100.

Une alerte est créée au **franchissement** d'un seuil, pas à chaque mesure :
- `niveau_bas` s'affiche « Critique » ;
- `niveau_haut` s'affiche « Avertissement » ;
- `info` sert au retour à la normale et au capteur revenu en ligne.

Les alertes critiques sont aussi envoyées par e-mail. En développement, l'e-mail s'affiche dans la console.

## Rôles

- Un rôle **administrateur** voit et gère tous les réservoirs. Il a aussi accès à la page **Rôles & utilisateurs** et à `/admin/`.
- Les autres rôles ne voient que **leurs** réservoirs.
- Les rôles `admin` et `utilisateur` sont protégés (on ne peut pas les supprimer).
- Il reste toujours au moins un administrateur actif.

## API REST (`/api/`)

| Méthode | URL | Rôle |
|---|---|---|
| POST | `/api/mesures/` | **ESP32** : en-tête `X-API-Key`, corps `{"distance_cm": 45.5}` |
| GET | `/api/reservoirs/<id>/niveau/` | **niveau en temps réel**, volume, statut, état |
| GET | `/api/dashboard/?reservoir=<id>&periode=24h` | tout le tableau de bord |
| GET | `/api/reservoirs/<id>/serie/?periode=1h\|24h\|7j\|30j` | points du graphique |
| GET/POST/PUT/DELETE | `/api/reservoirs/` | gestion des réservoirs |
| GET | `/api/mesures-liste/?reservoir=<id>&limite=100` | dernières mesures |
| GET | `/api/alertes/?non_lues=1` et POST `/api/alertes/<id>/lue/` | alertes |
| GET | `/api/moi/` | utilisateur connecté |

Authentification : session du navigateur, ou HTTP Basic (e-mail et mot de passe). Exemple :

```bash
curl -u admin@smartwater.local:SmartWater2026! http://127.0.0.1:8000/api/reservoirs/1/niveau/
curl -X POST http://127.0.0.1:8000/api/mesures/ -H "X-API-Key: <cle>" -H "Content-Type: application/json" -d "{\"distance_cm\": 45.5}"
```

L'API est prête pour une interface React (prévue dans le PDF). Les pages Django actuelles l'utilisent déjà pour le temps réel.

## Gestion des utilisateurs

Un administrateur gère tout depuis **Utilisateurs & rôles** :
- il crée un compte (nom, e-mail, rôle, mot de passe) ;
- il le modifie : rôle, activation ou désactivation, nouveau mot de passe ;
- il le supprime. Ses réservoirs peuvent alors être transférés sur le compte de l'administrateur.

Protections : on ne peut pas supprimer son propre compte, et il reste toujours un administrateur actif.

## Notifications des alertes

Chaque utilisateur choisit ses canaux dans **Paramètres → Notifications**. Le bouton **Envoyer un test** vérifie la configuration.

### E-mails réels (Gmail)

1. Activez la **validation en 2 étapes** du compte Google : https://myaccount.google.com/security
2. Créez un **mot de passe d'application** : https://myaccount.google.com/apppasswords
3. Dans `.env`, remplissez ces lignes, puis relancez `runserver` :

```ini
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_USER=votre.adresse@gmail.com
EMAIL_PASSWORD=abcdefghijklmnop
```

Sans `EMAIL_HOST`, les e-mails s'affichent dans la console du serveur. Les e-mails d'alerte partent pour les niveaux **bas** et **haut**.

### Notifications sur le téléphone (ntfy)

1. Installez l'application gratuite **ntfy** (Play Store ou App Store). Aucun compte n'est nécessaire.
2. Dans SmartWater, ouvrez **Paramètres → Notifications** et activez « téléphone ». Un nom de sujet secret est proposé, par exemple `smartwater-1d57a53ed670`. Enregistrez.
3. Dans l'application ntfy, touchez **+** et abonnez-vous à ce même sujet.
4. Cliquez sur **Envoyer un test**.

Le téléphone reçoit alors toutes les alertes :
- bas : priorité maximale ;
- haut : priorité haute ;
- info : priorité normale.

⚠️ Sur ntfy.sh, toute personne qui connaît le nom du sujet peut lire les messages : gardez-le secret.
Pour plus de confidentialité, vous pouvez installer votre propre serveur ntfy et renseigner `NTFY_SERVEUR` et `NTFY_TOKEN`.

## Tests

```bat
python manage.py test tests
```

## Capteur conseillé

Le **HC-SR04** du cahier des charges convient pour une maquette. Il n'est pas étanche et l'humidité d'un réservoir l'abîme vite.
Pour un vrai réservoir, prenez un **JSN-SR04T** (étanche). Il a le même câblage TRIG/ECHO, et le firmware fonctionne sans modification.
Il a une zone morte d'environ 20–25 cm : placez-le au moins 25 cm au-dessus du niveau maximum.

L'ECHO de ces deux capteurs sort en 5 V. Mettez un pont diviseur 1 kΩ / 2 kΩ avant l'entrée GPIO 18 de l'ESP32.
