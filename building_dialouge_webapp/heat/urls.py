from django.urls import path

from . import views

app_name = "heat"

urlpatterns = [
    path("forms/", views.handle_forms, name="forms"),
]
