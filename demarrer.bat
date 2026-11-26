@echo off
start "" cmd /k "cd /d C:\wamp64\www\smartwater & call venv\Scripts\activate & python manage.py runserver 5000"
start "" cmd /k "cd /d C:\wamp64\www\smartwater & call venv\Scripts\activate & python manage.py simuler_capteur"

