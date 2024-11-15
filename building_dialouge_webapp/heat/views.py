from django.views.generic import TemplateView


class LandingPage(TemplateView):
    template_name = "pages/home.html"


class IntroConsumption(TemplateView):
    template_name = "pages/intro_consumption.html"


class IntroInventory(TemplateView):
    template_name = "pages/intro_inventory.html"


class IntroRenovation(TemplateView):
    template_name = "pages/intro_renovation.html"
