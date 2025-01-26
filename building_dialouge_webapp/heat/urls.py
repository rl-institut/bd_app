from django.urls import path

from . import flows
from . import views

app_name = "heat"

urlpatterns = [
    # sorted by appearance in view flow
    path("", views.LandingPage.as_view(), name="home"),
    path("dead_end_tenant/", views.DeadEndTenant.as_view(), name="dead_end_tenant"),
    # step 1 consumption analysis
    path("intro_consumption/", views.IntroConsumption.as_view(), name="intro_consumption"),
    path("building_type/", flows.BuildingTypeFlow.as_view(), name="building_type"),
    path("dead_end_monument/", views.DeadEndMonumentProtection.as_view(), name="dead_end_monument_protection"),
    path("building_data", flows.BuildingDataFlow.as_view(), name="building_data"),
    path("cellar/", flows.CellarFlow.as_view(), name="cellar"),
    path("hotwater_heating/", flows.HotwaterHeatingFlow.as_view(), name="hotwater_heating"),
    path("dead_end_heating/", views.DeadEndHeating.as_view(), name="dead_end_heating"),
    path("consumption_input/", views.consumption_year, name="consumption_input"),
    path("consumption_input/<str:year>", views.consumption_year, name="consumption_input"),
    path("consumption_overview/", views.ConsumptionOverview.as_view(), name="consumption_overview"),
    path("consumption_result/", views.ConsumptionResult.as_view(), name="consumption_result"),
    # step 2 inventory analysis
    path("intro_inventory/", views.IntroInventory.as_view(), name="intro_inventory"),
    path("roof/", flows.RoofFlow.as_view(), name="roof"),
    path("window/", flows.WindowFlow.as_view(), name="window"),
    path("facade/", flows.FacadeFlow.as_view(), name="facade"),
    path("heating/", flows.HeatingFlow.as_view(), name="heating"),
    path("pv_system/", flows.PVSystemFlow.as_view(), name="pv_system"),
    path("ventilation_system/", flows.VentilationSystemFlow.as_view(), name="ventilation_system"),
    # step 3 renovation request
    path("intro_renovation/", views.IntroRenovation.as_view(), name="intro_renovation"),
    path("renovation_request/", views.renovation_scenario, name="renovation_request"),
    path("renovation_request/<str:scenario>", views.renovation_scenario, name="renovation_request"),
    path("renovation_overview/", views.RenovationOverview.as_view(), name="renovation_overview"),
    path("financial_support/", flows.FinancialSupporFlow.as_view(), name="financial_support"),
    path("optimization_start/", views.OptimizationStart.as_view(), name="optimization_start"),
    path("results/", views.Results.as_view(), name="results"),
    path("next_steps/", views.NextSteps.as_view(), name="next_steps"),
    # htmx redirected views
    path("delete_flow/", views.delete_flow, name="delete_flow"),
]
