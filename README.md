# Building Dialouge Webapp

Webapp für die Wärmewende

<img alt="Building Dialouge Illustration" height="30%" src="building_dialouge_webapp/static/images/illustrations/bd_lp_header2.svg" width="30%"/>

[![Built with Cookiecutter Django](https://img.shields.io/badge/built%20with-Cookiecutter%20Django-ff69b4.svg?logo=cookiecutter)](https://github.com/cookiecutter/cookiecutter-django/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

License: MIT

## Settings

Moved to [settings](http://cookiecutter-django.readthedocs.io/en/latest/settings.html).

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

1. Clone repo, setup virtual environment and install dependencies

    ```shell
    git clone git@github.com:rl-institut/bd_app.git
    cd bd_app
    virtualenv venv
    source venv/bin/activate
    pip install uv
    uv pip install -r ./requirements/local.txt
    pip install git+https://github.com/oemof/oemof-tabular.git
    pip install --upgrade django-compressor
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

    DATABASE_URL=postgres://bd_user:my_bd_user_pass@localhost:5432/building_dialouge_webapp
    ```
    (make sure you use the same password in `POSTGRES_PASSWORD` as in step 2)

4. Activate the `.env` file

    Run `export DJANGO_READ_DOT_ENV=True;` - ff this fails, try `source .env`

    Activate pre-commit:
    ```shell
    pre-commit install
    ```

5. Prepare needed data:

   - Clone oeprom oemof datapackage into `building_dialouge_webapp/media/oemof`

    ```shell
    cd building_dialouge_webapp/media/oemof
    git clone https://github.com/elmo-z/buildingDialogue.git
    ```

   - Copy hourly simulation profiles (from folder `data_raw`) into folder `building_dialouge_webapp/data/profiles`
   - Copy renovation responses into folder `building_dialouge_webapp/data/renovations`

6. Migrate and start app

    ```shell
    python manage.py migrate
    python manage.py runserver
    ```

7. In order to use django-oemof, you must start celery and redis parallel to runserver. You can use `make` command to do so

    ```shell
    make celery
    ```

    This will run celery app in background and wait for oemof simulations to run.
    You can trigger oemof simulation without the need to run a Django webserver by using script `scripts/django_oemof_standalone`

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

        self.stop = StopState(
            self,
            lookup="roof_done",
            next_botton_text="Speichern",
        ).transition(Next("end"))
        self.end = EndState(self, url="url_to_next_flow_or_view")
```

You can use these States:
- ```FormState(self, name="roof_type", form_class=forms.NameOfForm, template_name="optional_template.html",)```
  one FormState represents one Form, the name specifies the target in the template, the form_class the corresponding Form (defined in forms.py) and template_name is optional if you want to add helptext/explanation therefore you need to create a partial (a separate html file) and add its name to the corresponding state to the ```template_name``` parameter
- ```StopState(self, lookup="roof_done", next_botton_text="Speichern",)```
  every Flow needs at least one StopState, lookup can have a fitting and individual name (its used for remembering if a Flow is finished), and next_botton_text can change the Text of the next button
- ```EndState(self, url="url_to_next_flow_or_view")```
  every Flow needs at least one EndState, the url defines the url of the next Flow or View

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
        <div class="step-title">
            <div class="step-container">
                <div class="main">
                    <h1>Title of Page</h1>
                </div>
            </div>
        <div class="help"></div>
        </div>
        <div id="name_of_state" hx-post="" hx-trigger="change" hx-swap="show:bottom" hx-include="this">{{ name_of_state.content | safe }}</div>
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
