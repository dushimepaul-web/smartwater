mkdir mon_projet
cd mon_projet

python -m venv venv

venv\Scripts\activate

python -m pip install --upgrade pip

pip install django

django-admin startproject config .

python manage.py migrate

python manage.py runserver