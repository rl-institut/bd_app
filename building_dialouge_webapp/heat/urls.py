from django.urls import path

from . import views

app_name = "heat"

urlpatterns = [
    path("forms/", views.handle_forms, name="forms"),
    # BPMN Views
    path("roof_type/", views.RoofTypeView.as_view(), name="roof_type_form"),
    path(
        "roof_insulation/<int:pk>/",
        views.RoofInsulationView.as_view(),
        name="roof_insulation",
    ),
    path(
        "roof_details/<int:pk>/",
        views.RoofDetailsView.as_view(),
        name="roof_details",
    ),
    path("roof_usage/<int:pk>/", views.RoofUsageView.as_view(), name="roof_usage"),
]
