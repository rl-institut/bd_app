from django.urls import path

from . import flows
from . import views

app_name = "heat"

urlpatterns = [
    path("forms/", views.handle_forms, name="forms"),
    path("roof/", flows.RoofFlow.as_view(), name="roof"),
    path("cellar/", flows.CellarFlow.as_view(), name="cellar"),
    path("", views.LandingPage.as_view(), name="home"),
    path("intro_usage/", views.IntroUsage.as_view(), name="intro_usage"),
    path("intro_inventory/", views.IntroInventory.as_view(), name="intro_inventory"),
    path("intro_renovation/", views.IntroRenovation.as_view(), name="intro_renovation"),
]
