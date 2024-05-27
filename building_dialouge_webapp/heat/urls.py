from django.urls import path

from . import views

app_name = "heat"

urlpatterns = [
    path("forms/", views.load_all_forms, name="forms"),
]
