# Building Dialouge Webapp

Webapp für die Wärmewende

[![Built with Cookiecutter Django](https://img.shields.io/badge/built%20with-Cookiecutter%20Django-ff69b4.svg?logo=cookiecutter)](https://github.com/cookiecutter/cookiecutter-django/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

License: MIT

## Settings

Moved to [settings](http://cookiecutter-django.readthedocs.io/en/latest/settings.html).

## Basic Commands

### Setting Up Your Users

- To create a **normal user account**, just go to Sign Up and fill out the form. Once you submit it, you'll see a "Verify Your E-mail Address" page. Go to your console to see a simulated email verification message. Copy the link into your browser. Now the user's email should be verified and ready to go.

- To create a **superuser account**, use this command:

      $ python manage.py createsuperuser

For convenience, you can keep your normal user logged in on Chrome and your superuser logged in on Firefox (or similar), so that you can see how the site behaves for both kinds of users.

### Type checks

Running type checks with mypy:

    $ mypy building_dialouge_webapp

### Test coverage

To run the tests, check your test coverage, and generate an HTML coverage report:

    $ coverage run -m pytest
    $ coverage html
    $ open htmlcov/index.html

#### Running tests with pytest

    $ pytest

### Live reloading and Sass CSS compilation

Moved to [Live reloading and SASS compilation](https://cookiecutter-django.readthedocs.io/en/latest/developing-locally.html#sass-compilation-live-reloading).

### Celery

This app comes with Celery.

To run a celery worker:

```bash
cd building_dialouge_webapp
celery -A config.celery_app worker -l info
```

Please note: For Celery's import magic to work, it is important _where_ the celery commands are run. If you are in the same folder with _manage.py_, you should be right.

To run [periodic tasks](https://docs.celeryq.dev/en/stable/userguide/periodic-tasks.html), you'll need to start the celery beat scheduler service. You can start it as a standalone process:

```bash
cd building_dialouge_webapp
celery -A config.celery_app beat
```

or you can embed the beat service inside a worker with the `-B` option (not recommended for production use):

```bash
cd building_dialouge_webapp
celery -A config.celery_app worker -B -l info
```

### Sentry

Sentry is an error logging aggregator service. You can sign up for a free account at <https://sentry.io/signup/?code=cookiecutter> or download and host it yourself.
The system is set up with reasonable defaults, including 404 logging and integration with the WSGI application.

You must set the DSN url in production.

## Deployment

The following details how to deploy this application.

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

## Adding new Flows

### 1. Forms
add the forms needed for the flow.
For each moment in the flow where a decision in the form / from the user will cause a diffrent form being
rendered afterwards, that decision needs it's own form

### 2. Flow
start the Flow with a nice descriptive Name: for example "RoofFlow"
```
class RoofFlow(Flow):
template_name = "path_to_template/name_of_template.html"

    def __init__(self):
        super().__init__()
        self.start = State(
            ...
        ).transition(
            ...,
        )

        # add more States in here

        self.end = EndState(self, url="url_to_next_flow_or_view")
```

You can use these States:
- ```FormState(self, name="roof_type", form_class=forms.NameOfForm,)```
- ```EndState(self, url="url_to_next_flow_or_view")```
- if you want to add helptext to a Form, create a partial (a separate html file) and add it to the corresponding state with the ```template_name``` parameter

You can use these Transitions:
- ```Next("name_of_the_next_state")```
- ```Switch("name_of_the_field_that_will_cause_the_switch").case("returned value of the field", "name of next state").default("name_of_the_next_state")```
    you can add as many cases as you need

It is important, that the name_of_the_next_state in the transition is the same as a state that you are
declaring later ```(self.name_of_the_next_state = State(...) )```

### 3. Template
Create a template with a fitting name: for example roof.html
use this base structure:
```
    {% extends "base.html" %}

    {% block content %}
    <section class="position-relative h-100 flex-grow-1 pb-5">
        <div class="help-background"></div>
        <div class="step-title">
            <div class="step-container">
                <div class="main">
                    <h1>Title of Page</h1>
                </div>
            </div>
        <div class="help"></div>
        </div>
        <div id="name_attribute_of_state">{{ name_attribute_of_state.content | safe }}</div>
    </section>
    {% endblock content %}
```

For a helptext partial you can use this structure: for example roof_help.html
```
    <div class="step-question">
        <div class="step-container">
            <div class="main">{{ form }}</div>
        </div>
        <div class="help">
            <span>Flachdach:&nbsp;</span>Ein Flachdach ist ein Dach mit einer sehr geringen Neigung, das fast waagerecht verläuft.
        </div>
    </div>
```
### 4. URL
add the Flow to the url like this:
```
    path("roof/", flows.RoofFlow.as_view(), name="roof"),
```
