from django.urls import path

from . import flows
from . import views

app_name = "heat"

urlpatterns = [
    path("forms/", views.handle_forms, name="forms"),
    path("roof/", flows.RoofFlow.as_view(), name="roof"),
    path("cellar/", flows.CellarFlow.as_view(), name="cellar"),
    path("", views.LandingPage.as_view(), name="home"),
]
