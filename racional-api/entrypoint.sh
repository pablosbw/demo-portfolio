#!/bin/sh
set -e

python manage.py makemigrations racional_api
python manage.py migrate

# Populate users
python manage.py seed_users
python manage.py runserver 0.0.0.0:8000

