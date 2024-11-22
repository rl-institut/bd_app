from django.views.generic import TemplateView


class LandingPage(TemplateView):
    template_name = "pages/home.html"


class DeadEndTenant(TemplateView):
    template_name = "pages/dead_end_tenant.html"


class IntroConsumption(TemplateView):
    template_name = "pages/intro_consumption.html"
    extra_context = {
        "back_url": "heat:home",
    }


class DeadEndMonumentProtection(TemplateView):
    template_name = "pages/dead_end_monument_protection.html"


class DeadEndHeating(TemplateView):
    template_name = "pages/dead_end_heating.html"


class ConsumptionResult(TemplateView):
    template_name = "pages/consumption_result.html"


class IntroInventory(TemplateView):
    template_name = "pages/intro_inventory.html"


class IntroRenovation(TemplateView):
    template_name = "pages/intro_renovation.html"


class Results(TemplateView):
    template_name = "pages/results.html"


class NextSteps(TemplateView):
    template_name = "pages/next_steps.html"
