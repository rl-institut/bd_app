from django.urls import path

from . import views

app_name = "heat"

urlpatterns = [
    path("", views.LandingPage.as_view(), name="home"),
    path("contact/", views.ContactPage.as_view(), name="contact"),
    path("imprint/", views.ImprintPage.as_view(), name="imprint"),
    path("privacy/", views.PrivacyPage.as_view(), name="privacy"),
    path("docs/<str:page>/", views.DocumentationView.as_view(), name="docs"),
]
