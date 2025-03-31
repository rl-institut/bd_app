from django.urls import path

from . import flows
from . import views

app_name = "heat"

urlpatterns = [
    # sorted by appearance in view flow
    path("", views.LandingPage.as_view(), name="home"),
    path("dead_end_tenant/", views.DeadEndTenant.as_view(), name="dead_end_tenant"),
    # step 1 inventory analysis
    path("intro_inventory/", views.IntroInventory.as_view(), name="intro_inventory"),
    path("building_type/", flows.BuildingTypeFlow.as_view(), name="building_type"),
    path("dead_end_monument/", views.DeadEndMonumentProtection.as_view(), name="dead_end_monument_protection"),
    path("insulation", flows.InsulationFlow.as_view(), name="insulation"),
    path("hotwater_heating/", flows.HotwaterHeatingFlow.as_view(), name="hotwater_heating"),
    path("roof/", flows.RoofFlow.as_view(), name="roof"),
    path("roof_orientation/", views.roof_orientation, name="roof_orientation"),
    path("heating/", flows.HeatingFlow.as_view(), name="heating"),
    path("pv_system/", flows.PVSystemFlow.as_view(), name="pv_system"),
    # step 2 renovation request
    path("intro_renovation/", views.IntroRenovation.as_view(), name="intro_renovation"),
    path("renovation_request/", views.renovation_scenario, name="renovation_request"),
    path("renovation_request/<str:scenario>", views.renovation_scenario, name="renovation_request"),
    path("renovation_overview/", views.RenovationOverview.as_view(), name="renovation_overview"),
    path("financial_support/", flows.FinancialSupportFlow.as_view(), name="financial_support"),
    path("optimization_start/", views.OptimizationStart.as_view(), name="optimization_start"),
    path("simulate/", views.simulate, name="simulate"),
    # step 3 results
    path("results/", views.Results.as_view(), name="results"),
    path("next_steps/", views.NextSteps.as_view(), name="next_steps"),
    # htmx redirected views
    path("delete_flow/", views.delete_flow, name="delete_flow"),
]
