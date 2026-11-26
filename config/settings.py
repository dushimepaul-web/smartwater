"""
Réglages Django du projet SmartWater IoT.

Les valeurs sensibles (clé secrète, mot de passe MySQL, broker MQTT) se lisent
dans des variables d'environnement. Les valeurs par défaut conviennent au
développement local (WAMP/XAMPP : MySQL en root sans mot de passe).
Voir .env.example et README.md.
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def env(nom, defaut=None):
    return os.environ.get(nom, defaut)


def env_bool(nom, defaut=False):
    return env(nom, str(defaut)).strip().lower() in ('1', 'true', 'yes', 'oui', 'on')


# Charge un fichier .env s'il existe (format CLE=valeur), sans dépendance externe.
_fichier_env = BASE_DIR / '.env'
if _fichier_env.exists():
    for _ligne in _fichier_env.read_text(encoding='utf-8').splitlines():
        _ligne = _ligne.strip()
        if _ligne and not _ligne.startswith('#') and '=' in _ligne:
            _cle, _val = _ligne.split('=', 1)
            os.environ.setdefault(_cle.strip(), _val.strip())


# --- Sécurité --------------------------------------------------------------
CLE_DEV = 'dev-uniquement-changez-moi-en-production'
SECRET_KEY = env('DJANGO_SECRET_KEY', CLE_DEV)
DEBUG = env_bool('DJANGO_DEBUG', True)
if not DEBUG and SECRET_KEY == CLE_DEV:
    from django.core.exceptions import ImproperlyConfigured
    raise ImproperlyConfigured('Production : définissez DJANGO_SECRET_KEY dans .env (openssl rand -hex 32)')
ALLOWED_HOSTS = [h.strip() for h in env('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1,0.0.0.0').split(',') if h.strip()]
# Permet à l'ESP32 du réseau local de joindre le serveur (ex. 192.168.1.20)
if env_bool('DJANGO_ALLOW_LAN', True) and DEBUG:
    ALLOWED_HOSTS.append('*')


# --- Applications ----------------------------------------------------------
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'roles',
    'accounts',
    'reservoirs',
    'alertes',
    'dashboard',
    'historique',
    'parametres',
    'api',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'alertes.context_processors.alertes_non_lues',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# --- Base de données (MySQL, comme dans le cahier des charges) -------------
if env('DB_ENGINE', 'mysql') == 'sqlite':
    # Pratique pour un essai rapide sans MySQL : DB_ENGINE=sqlite
    DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': BASE_DIR / 'db.sqlite3'}}
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': env('DB_NAME', 'smartwater'),
            'USER': env('DB_USER', 'root'),
            'PASSWORD': env('DB_PASSWORD', ''),
            'HOST': env('DB_HOST', 'localhost'),
            'PORT': env('DB_PORT', '3306'),
            'OPTIONS': {'charset': 'utf8mb4'},
            'TEST': {'CHARSET': 'utf8mb4', 'COLLATION': 'utf8mb4_unicode_ci'},
        }
    }


# --- Authentification ------------------------------------------------------
# Les comptes sont stockés dans la table `utilisateurs` (voir accounts/models.py)
AUTH_USER_MODEL = 'accounts.Utilisateur'
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'dashboard'
LOGOUT_REDIRECT_URL = 'login'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 8}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# --- Langue et fuseau horaire ----------------------------------------------
LANGUAGE_CODE = 'fr-fr'
TIME_ZONE = env('DJANGO_TIME_ZONE', 'Africa/Bujumbura')
USE_I18N = True
USE_TZ = True


# --- Fichiers statiques ----------------------------------------------------
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
# Fichiers statiques servis par WhiteNoise (compressés, mis en cache) en production
STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage' if not DEBUG
                    else 'django.contrib.staticfiles.storage.StaticFilesStorage'},
}

DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'


# --- E-mail (mot de passe oublié, alertes) ---------------------------------
# La configuration se fait de préférence dans l'application :
#   Paramètres > E-mail (SMTP)  (administrateur ; mot de passe chiffré dans la base).
# Sinon, variables EMAIL_HOST... du fichier .env ; sinon affichage dans la console.
EMAIL_ENV = {
    'host': env('EMAIL_HOST', ''),
    'port': int(env('EMAIL_PORT', '587')),
    'username': env('EMAIL_USER', ''),
    'password': env('EMAIL_PASSWORD', '').replace(' ', ''),
    'use_tls': env_bool('EMAIL_USE_TLS', True),
    'timeout': 15,
}
MAILERS = {'default': {'BACKEND': 'parametres.email_backend.EmailBackend'}}
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', f"SmartWater IoT <{env('EMAIL_USER') or 'no-reply@smartwater.local'}>")

# Adresse publique du site (lien dans les e-mails et notifications)
SITE_URL = env('SITE_URL', 'http://127.0.0.1:8000').rstrip('/')

# --- Notifications sur téléphone (ntfy) ------------------------------------
# Application gratuite ntfy (Android / iPhone) : https://ntfy.sh
NTFY_SERVEUR = env('NTFY_SERVEUR', 'https://ntfy.sh').rstrip('/')
NTFY_TOKEN = env('NTFY_TOKEN', '')   # seulement pour un serveur ntfy protégé


# --- API REST --------------------------------------------------------------
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': ['rest_framework.permissions.IsAuthenticated'],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ],
}


# --- IoT -------------------------------------------------------------------
# Un capteur est considéré « hors ligne » s'il n'a rien envoyé depuis
# CAPTEUR_DELAI_HORS_LIGNE secondes.
CAPTEUR_DELAI_HORS_LIGNE = int(env('CAPTEUR_DELAI_HORS_LIGNE', '60'))

# Broker MQTT (commande : python manage.py mqtt_listener)
MQTT_HOST = env('MQTT_HOST', 'localhost')
MQTT_PORT = int(env('MQTT_PORT', '1883'))
MQTT_USER = env('MQTT_USER', '')
MQTT_PASSWORD = env('MQTT_PASSWORD', '')
MQTT_TLS = env_bool('MQTT_TLS', False)
# L'ESP32 publie sur smartwater/capteurs/<id_capteur>/mesure
MQTT_TOPIC_PREFIXE = env('MQTT_TOPIC_PREFIXE', 'smartwater/capteurs')


# --- Production derrière Caddy (HTTPS) -------------------------------------
CSRF_TRUSTED_ORIGINS = [o.strip() for o in env('DJANGO_CSRF_TRUSTED_ORIGINS', '').split(',') if o.strip()]
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_REFERRER_POLICY = 'same-origin'
    X_FRAME_OPTIONS = 'DENY'
    # La redirection HTTP -> HTTPS et HSTS sont faites par Caddy

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {'console': {'class': 'logging.StreamHandler'}},
    'root': {'handlers': ['console'], 'level': env('DJANGO_LOG_LEVEL', 'INFO')},
    'loggers': {'django.server': {'level': 'WARNING'}},
}
THINGSPEAK_API = env("THINGSPEAK_API", "https://api.thingspeak.com")
