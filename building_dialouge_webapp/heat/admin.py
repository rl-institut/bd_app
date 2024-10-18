"""Add models to admin interface."""

from django.contrib import admin

from building_dialouge_webapp.heat.models import Roof

admin.site.register(
    [
        Roof,
    ],
)
