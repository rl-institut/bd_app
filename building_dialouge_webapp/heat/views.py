from django.views.generic import TemplateView


class LandingPage(TemplateView):
    template_name = "pages/home.html"


class DeadEndTenant(TemplateView):
    template_name = "pages/dead_end_tenant.html"
    extra_context = {
        "back_url": "heat:home",
    }


class IntroConsumption(TemplateView):
    template_name = "pages/intro_consumption.html"
    extra_context = {
        "back_url": "heat:home",
        "next_url": "heat:building_type",
    }


class DeadEndMonumentProtection(TemplateView):
    template_name = "pages/dead_end_monument_protection.html"
    extra_context = {
        "back_url": "heat:building_type",
    }


class DeadEndHeating(TemplateView):
    template_name = "pages/dead_end_heating.html"
    extra_context = {
        "back_url": "heat:hotwater_heating",
    }


class ConsumptionResult(TemplateView):
    template_name = "pages/consumption_result.html"
    extra_context = {
        "back_url": "heat:consumption_input",
        "next_url": "heat:intro_inventory",
    }


class IntroInventory(TemplateView):
    template_name = "pages/intro_inventory.html"
    extra_context = {
        "back_url": "heat:consumption_result",
        "next_url": "heat:roof",
    }


class IntroRenovation(TemplateView):
    template_name = "pages/intro_renovation.html"
    extra_context = {
        "back_url": "heat:ventilation_system",
    }


class Results(TemplateView):
    template_name = "pages/results.html"
    extra_context = {
        "back_url": "heat:financial_support",
        "next_url": "heat:next_steps",
    }


class NextSteps(TemplateView):
    template_name = "pages/next_steps.html"
    extra_context = {
        "back_url": "heat:results",
    }
