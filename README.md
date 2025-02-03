# Building Dialouge Webapp
## Stand 03.02.2025 Abgabe Bachelorarbeit Josefine Hoppe

Webapp für die Wärmewende

[![Built with Cookiecutter Django](https://img.shields.io/badge/built%20with-Cookiecutter%20Django-ff69b4.svg?logo=cookiecutter)](https://github.com/cookiecutter/cookiecutter-django/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

License: MIT


## Deployment

The following details on how to deploy this application.

### Docker

See detailed [cookiecutter-django Docker documentation](http://cookiecutter-django.readthedocs.io/en/latest/deployment-with-docker.html).

## Installation

### Docker

Build dev container with

`docker-compose -f local.yml up -d --build`

or for production (requires manual creation of `.envs/.production/.django`):

`docker-compose -f production.yml up -d --build`

### Local

1. Clone repo, setup virtual environment and install

```shell
git clone git@github.com:rl-institut/bd_app.git
cd bd_app
virtualenv venv
source venv/bin/activate
pip install -r ./requirements/local.txt
```

2. Setup local PostgreSQL server and configure using pgadmin4 (Linux)

- Install: `sudo apt install postgresql pgadmin4`
- Start pgadmin4
  - Create database "building_dialouge_webapp"
  - Create user "bd_user" with some password, e.g. "my_bd_user_pass"
- Grant write permissions to this DB for the user
- Activate postGIS via SQL query: `CREATE EXTENSION postgis;`

3. Create `.env` file with the following content
```
# General
# ------------------------------------------------------------------------------
USE_DOCKER=yes
IPYTHONDIR=/app/.ipython
# Redis
# ------------------------------------------------------------------------------
REDIS_URL=redis://redis:6379/0

# Celery
# ------------------------------------------------------------------------------

CELERY_BROKER_URL=redis://redis:6379/0

# Flower
CELERY_FLOWER_USER=dVSdYOthZmldNnHOnGLAgKhnETvRbOXs
CELERY_FLOWER_PASSWORD=YbGI8ju9tsiODB0ACmcEGC1yMoOe3BI51PwV8niA6AH6oXLPMQ6Fahc3NWFHaQlK

# PostgreSQL
# ------------------------------------------------------------------------------
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=building_dialouge_webapp
POSTGRES_USER=bd_user
POSTGRES_PASSWORD=my_bd_user_pass

DATABASE_URL=postgis://bd_user:GWzBcADhGhvhY0VRQvm9dD2LTMnEIplVmzNjAEkZNoF2T87leMSiRHiSReK2hlmC@localhost:5432/building_dialouge_webapp
```
(make sure you use the same password in `POSTGRES_PASSWORD` as in step 2)

4. Activate the `.env` file

Run `export DJANGO_READ_DOT_ENV=True;` - ff this fails, try `source .env`

5. Migrate and start app

```shell
python manage.py migrate
python manage.py runserver
```

## Add dependencies

This can be done in `requirements/` folder by adding dependency to related *.in file and compile/lock dependencies.
Via `uv` (you must install uv first - recommended!):
```shell
uv pip compile -o requirements/local.txt requirements/local.in
uv pip compile -o requirements/production.txt requirements/production.in
```
or via `pip-compile` (you must install pip-tools first):
```shell
pip-compile -o requirements/local.txt requirements/local.in
pip-compile -o requirements/production.txt requirements/production.in
```
