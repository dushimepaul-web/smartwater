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

> 🚀 **Mise en ligne sur un serveur avec Docker et un nom de domaine** : voir la section [en bas de ce fichier](#-mise-en-ligne-sur-un-serveur-vps-avec-docker-et-un-nom-de-domaine).

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

### E-mails réels (Gmail) — dans l'application

Connecté en **administrateur**, ouvrez **Paramètres → E-mail (SMTP)** :

1. Activez la **validation en 2 étapes** du compte Google : https://myaccount.google.com/security
2. Créez un **mot de passe d'application** : https://myaccount.google.com/apppasswords
3. Saisissez l'adresse Gmail et les 16 lettres (les espaces sont retirés automatiquement). Gardez `smtp.gmail.com`, le port `587` et STARTTLS.
4. Cliquez sur **Enregistrer**, puis sur **Envoyer un e-mail de test**. En cas d'échec, la page affiche la cause.

Le mot de passe est **chiffré** dans la table `configuration_email`, avec une clé dérivée de `DJANGO_SECRET_KEY`. Il n'est jamais réaffiché.
⚠️ Si vous changez `DJANGO_SECRET_KEY`, ressaisissez le mot de passe.

En ligne de commande, le mot de passe est demandé au clavier et ne s'affiche pas :

```bat
python manage.py configurer_email --email votre.adresse@gmail.com --test votre.adresse@gmail.com
```

Autre possibilité : les variables `EMAIL_HOST`… du fichier `.env`. Elles ne servent que si rien n'est configuré dans l'application.
Sans configuration, les e-mails s'affichent dans la console du serveur.
Les e-mails d'alerte partent pour les niveaux **bas** et **haut**.

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

## Copie vers ThingSpeak (facultatif)

[ThingSpeak](https://thingspeak.mathworks.com) est un service IoT gratuit pour les petits projets non commerciaux. SmartWater peut y recopier chaque mesure : vous obtenez des graphiques en ligne et une copie de secours.

1. Créez un compte, puis un **canal** (Channels → New Channel) avec trois champs : `Field 1` = Niveau (%), `Field 2` = Distance (cm), `Field 3` = Volume (L).
2. Notez le **Channel ID** et, dans l'onglet *API Keys*, la **Write API Key**. Si le canal est privé, notez aussi la **Read API Key**.
3. Dans SmartWater, ouvrez **Paramètres → ThingSpeak** (pour le réservoir choisi), saisissez ces valeurs, puis cliquez sur **Enregistrer**, puis sur **Tester**.

Le comportement :
- chaque mesure reçue est recopiée, au plus une fois toutes les 20 s (15 s minimum : c'est la limite de l'offre gratuite, 3 millions de messages par an) ;
- les clés sont chiffrées dans la base (table `thingspeak`) ;
- une panne de ThingSpeak ne bloque jamais la réception des mesures.

**Secours si le serveur tombe :**
1. Dans le firmware ESP32, décommentez `#define THINGSPEAK_DIRECT` et renseignez `TS_WRITE_KEY` et `HAUTEUR_CM`. L'ESP32 enverra aussi ses mesures directement à ThingSpeak.
2. Une fois le serveur revenu, cliquez sur **Paramètres → ThingSpeak → Récupérer les mesures manquantes**, ou lancez :

```bat
python manage.py importer_thingspeak --heures 24
```

Les doublons sont ignorés.

## Tests

```bat
python manage.py test tests
```

## Capteur conseillé

Le **HC-SR04** du cahier des charges convient pour une maquette. Il n'est pas étanche et l'humidité d'un réservoir l'abîme vite.
Pour un vrai réservoir, prenez un **JSN-SR04T** (étanche). Il a le même câblage TRIG/ECHO, et le firmware fonctionne sans modification.
Il a une zone morte d'environ 20–25 cm : placez-le au moins 25 cm au-dessus du niveau maximum.

L'ECHO de ces deux capteurs sort en 5 V. Mettez un pont diviseur 1 kΩ / 2 kΩ avant l'entrée GPIO 18 de l'ESP32.

---

# 🚀 Mise en ligne sur un serveur (VPS) avec Docker et un nom de domaine

Ce guide va du serveur vide jusqu'au site en **HTTPS** sur votre domaine, par exemple `https://smartwater.mondomaine.com`.
Remplacez partout `smartwater.mondomaine.com` par **votre** domaine et `203.0.113.10` par **l'adresse IP de votre serveur**.

## Ce qui tourne sur le serveur

```
Internet ──► Caddy (ports 80/443, HTTPS automatique Let's Encrypt)
                 └──► web : Django + gunicorn ──► db : MySQL 8.4 (non exposé)
ESP32 ──HTTPS──► Caddy ──► web  /api/mesures/
ESP32 ──MQTT (1883, mot de passe)──► mqtt : Mosquitto ──► mqtt_listener (Django) ──► db
```

| Service | Rôle |
|---|---|
| `db` | MySQL 8.4. Les données sont gardées dans le volume `db_data`. |
| `web` | L'application Django (gunicorn). Les migrations s'appliquent toutes seules au démarrage. |
| `mqtt` | Le broker Mosquitto. Il exige un identifiant et un mot de passe. |
| `mqtt_listener` | Reçoit les mesures MQTT et les enregistre. |
| `caddy` | Le serveur web public : il obtient et renouvelle le certificat HTTPS tout seul. |

## Prérequis

- Un VPS **Ubuntu 22.04 ou 24.04** (1 Go de RAM minimum, 2 Go conseillés), avec l'accès `root` en SSH.
- Un **nom de domaine** chez un registraire (OVH, Namecheap, Cloudflare, Gandi, LWS…).

## Étape 1 – Faire pointer le domaine vers le serveur (DNS)

Dans l'espace client de votre registraire, menu **Zone DNS**, ajoutez deux enregistrements :

| Type | Nom (sous-domaine) | Valeur | TTL |
|---|---|---|---|
| `A` | `smartwater` (ou `@` pour le domaine nu) | `203.0.113.10` | 300 |
| `A` | `www.smartwater` (ou `www`) | `203.0.113.10` | 300 |

- **Cloudflare :** mettez le nuage en **gris** (« DNS only ») pendant l'installation. Sinon, Caddy ne pourra pas obtenir son certificat.
- **Vérification :** depuis votre PC, la commande `nslookup smartwater.mondomaine.com` doit répondre avec l'IP du serveur. Cela prend de quelques minutes à quelques heures.

## Étape 2 – Se connecter au serveur et le préparer

```bash
ssh root@203.0.113.10

apt update && apt upgrade -y
apt install -y git ufw

# Pare-feu : SSH, web, et MQTT pour les ESP32
ufw allow OpenSSH
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 443/udp
ufw allow 1883/tcp
ufw --force enable
```

## Étape 3 – Installer Docker

```bash
curl -fsSL https://get.docker.com | sh
docker --version
docker compose version
```

## Étape 4 – Récupérer le projet

```bash
mkdir -p /opt && cd /opt
git clone https://github.com/dushimepaul-web/smartwater.git
cd smartwater
```

Le dépôt est privé ? GitHub vous demandera alors un identifiant et un **jeton personnel** (Settings → Developer settings → Personal access tokens) à la place du mot de passe.
Vous pouvez aussi envoyer le zip depuis votre PC avec `scp smartwater.zip root@203.0.113.10:/opt/`, puis `unzip`.

## Étape 5 – Créer le fichier de configuration `.env`

```bash
cp .env.production.example .env

# Générez trois secrets et notez-les :
openssl rand -hex 32   # -> DJANGO_SECRET_KEY
openssl rand -hex 16   # -> DB_PASSWORD
openssl rand -hex 16   # -> MYSQL_ROOT_PASSWORD
openssl rand -hex 12   # -> MQTT_PASSWORD

nano .env
```

Dans `nano`, remplacez :
- `smartwater.mondomaine.com` par votre domaine, **partout** (DOMAINE, DJANGO_ALLOWED_HOSTS, DJANGO_CSRF_TRUSTED_ORIGINS, SITE_URL) ;
- `EMAIL_LETSENCRYPT` par votre adresse e-mail (Let's Encrypt vous prévient en cas de problème de certificat) ;
- toutes les valeurs `A_CHANGER…` par les secrets générés.

Enregistrez avec `Ctrl+O`, `Entrée`, puis quittez avec `Ctrl+X`. Protégez ensuite le fichier : `chmod 600 .env`.

⚠️ Ne changez plus `DJANGO_SECRET_KEY` ensuite : le mot de passe Gmail enregistré dans l'application est chiffré avec cette clé.

## Étape 6 – Construire et démarrer

```bash
docker compose up -d --build
docker compose ps                 # tous les services doivent être "running" / "healthy"
docker compose logs -f web        # Ctrl+C pour quitter les journaux
```

Le premier démarrage prend 2 à 5 minutes (construction de l'image, initialisation de MySQL). Dans les journaux de `web`, vous devez voir « Base de données prête » puis les migrations.
Le certificat HTTPS arrive tout seul, à condition que le DNS pointe déjà vers le serveur. Pour suivre son obtention : `docker compose logs caddy`.

## Étape 7 – Créer le compte administrateur

```bash
docker compose exec web python manage.py createsuperuser
```

La commande vous demande l'adresse e-mail, le nom et le mot de passe. Le compte reçoit automatiquement le rôle **Administrateur**.

Ensuite, ouvrez **https://smartwater.mondomaine.com** et connectez-vous.

## Étape 8 – Configurer dans l'application

1. **Paramètres → E-mail (SMTP)** : entrez votre Gmail et le mot de passe d'application, cliquez sur **Enregistrer**, puis sur **Envoyer un e-mail de test**.
2. **Réservoirs → Ajouter** : créez le réservoir, puis notez la **clé d'API** du capteur.
3. **Paramètres → Notifications** : activez le téléphone (ntfy) et cliquez sur **Envoyer un test**.

## Étape 9 – Brancher l'ESP32 sur le serveur en ligne

Dans `firmware/esp32_smartwater/esp32_smartwater.ino` :

- **En HTTPS (conseillé) :**
  - `API_URL = "https://smartwater.mondomaine.com/api/mesures/"`
  - `API_KEY = "<clé du capteur>"`
- **En MQTT :**
  - décommentez `#define MODE_MQTT` et commentez `#define MODE_HTTP` ;
  - `MQTT_HOST = "smartwater.mondomaine.com"` ;
  - `MQTT_USER` et `MQTT_PASS` : les valeurs du `.env` du serveur ;
  - `ID_CAPTEUR` et `API_KEY` : ceux du capteur.

Téléversez le programme, puis ouvrez le moniteur série à 115200 bauds. Il doit afficher `HTTP 201`. Le tableau de bord se met alors à jour en direct.

Test sans ESP32, depuis n'importe quel PC :
```bash
curl -X POST https://smartwater.mondomaine.com/api/mesures/ -H "X-API-Key: <clé>" -H "Content-Type: application/json" -d "{\"distance_cm\": 40}"
```

## Utilisation au quotidien

| Action | Commande (dans `/opt/smartwater`) |
|---|---|
| Voir l'état des services | `docker compose ps` |
| Journaux (tous / un service) | `docker compose logs -f` · `docker compose logs -f mqtt_listener` |
| Redémarrer | `docker compose restart` |
| Arrêter / démarrer | `docker compose down` · `docker compose up -d` |
| Mettre à jour après un `git push` | `git pull && docker compose up -d --build` |
| Console Django | `docker compose exec web python manage.py shell` |
| Console MySQL | `docker compose exec db sh -c 'mysql -u root -p"$MYSQL_ROOT_PASSWORD" smartwater'` |

`docker compose down` **ne supprime pas** les données : elles restent dans les volumes. Ne lancez **jamais** `docker compose down -v` : cette commande efface la base.

## Sauvegardes

```bash
chmod +x docker/sauvegarde.sh
./docker/sauvegarde.sh                       # crée sauvegardes/smartwater_AAAA-MM-JJ_HHMM.sql.gz

crontab -e                                   # sauvegarde automatique chaque nuit à 2 h :
0 2 * * * cd /opt/smartwater && ./docker/sauvegarde.sh >> sauvegardes/journal.log 2>&1
```

Si l'ESP32 envoie aussi directement à ThingSpeak, vous pouvez récupérer automatiquement chaque heure les mesures manquantes (`crontab -e`) :
```bash
0 * * * * cd /opt/smartwater && docker compose exec -T web python manage.py importer_thingspeak --heures 2
```

Pour restaurer une sauvegarde :
```bash
gunzip -c sauvegardes/smartwater_2026-11-26_0200.sql.gz | docker compose exec -T db sh -c 'mysql -u root -p"$MYSQL_ROOT_PASSWORD" smartwater'
```

Copiez régulièrement le dossier `sauvegardes/` hors du serveur, par exemple avec `scp` vers votre PC.

## Dépannage

| Problème | Solution |
|---|---|
| Le site ne s'ouvre pas | `nslookup votre-domaine` doit donner l'IP du serveur. Vérifiez aussi `ufw status` (ports 80 et 443) et `docker compose logs caddy`. |
| Erreur de certificat HTTPS | DNS pas encore propagé, ou Cloudflare en orange : attendez ou passez-le en gris, puis lancez `docker compose restart caddy`. |
| « Bad Request (400) » | Le domaine manque dans `DJANGO_ALLOWED_HOSTS`. Corrigez `.env`, puis lancez `docker compose up -d`. |
| « CSRF verification failed » à la connexion | `DJANGO_CSRF_TRUSTED_ORIGINS` doit contenir `https://votre-domaine`. |
| `web` redémarre en boucle | `docker compose logs web`. La cause est souvent `DJANGO_SECRET_KEY` absente ou un mot de passe MySQL différent entre `.env` et la base déjà créée. |
| L'ESP32 reçoit `401` | Mauvaise clé d'API : copiez-la depuis **Réservoirs → Modifier**. |
| MQTT « not authorised » | `MQTT_USER` et `MQTT_PASSWORD` de l'ESP32 doivent être identiques à ceux du `.env`. |
| Les e-mails ne partent pas | **Paramètres → E-mail (SMTP) → Envoyer un e-mail de test** affiche la raison. Certains hébergeurs bloquent le port 587 : demandez au support de l'ouvrir. |
