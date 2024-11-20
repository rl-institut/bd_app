from django.urls import path

from . import flows
from . import views

app_name = "heat"

urlpatterns = [
    # sorted by appearance in view flow
    path("", views.LandingPage.as_view(), name="home"),
    # step 1 consumption analysis
    path("intro_consumption/", views.IntroConsumption.as_view(), name="intro_consumption"),
    path("building_type/", flows.BuildingTypeFlow.as_view(), name="building_type"),
    path("building_data", flows.BuildingDataFlow.as_view(), name="building_data"),
    path("cellar/", flows.CellarFlow.as_view(), name="cellar"),
    path("hotwater_heating/", flows.HotwaterHeatingFlow.as_view(), name="hotwater_heating"),
    # step 2 inventory analysis
    path("intro_inventory/", views.IntroInventory.as_view(), name="intro_inventory"),
    path("roof/", flows.RoofFlow.as_view(), name="roof"),
    # step 3 renovation request
    path("intro_renovation/", views.IntroRenovation.as_view(), name="intro_renovation"),
]
