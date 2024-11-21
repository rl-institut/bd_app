from django.views.generic import TemplateView


class LandingPage(TemplateView):
    template_name = "pages/home.html"


class IntroConsumption(TemplateView):
    template_name = "pages/intro_consumption.html"
    extra_context = {
        "back_url": "heat:home",
    }


class ConsumptionResult(TemplateView):
    template_name = "pages/consumption_result.html"


class IntroInventory(TemplateView):
    template_name = "pages/intro_inventory.html"


class IntroRenovation(TemplateView):
    template_name = "pages/intro_renovation.html"
