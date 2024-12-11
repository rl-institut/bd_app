from django.http import HttpResponseRedirect
from django.http import JsonResponse
from django.urls import reverse
from django.views.generic import TemplateView
from django.shortcuts import render

from building_dialouge_webapp.heat.flows import RenovationRequestFlow

from .navigation import SidebarNavigationMixin

SCENARIO_MAX = 3


class LandingPage(TemplateView):
    template_name = "pages/home.html"


class DeadEndTenant(TemplateView):
    template_name = "pages/dead_end_tenant.html"
    extra_context = {
        "back_url": "heat:home",
    }


class IntroConsumption(SidebarNavigationMixin, TemplateView):
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


class ConsumptionResult(SidebarNavigationMixin, TemplateView):
    template_name = "pages/consumption_result.html"
    extra_context = {
        "back_url": "heat:consumption_input",
        "next_url": "heat:intro_inventory",
    }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        """
        consumption_result = self.request.GET.get("consumption_result")
        if consumption_result is None:
            consumption_result = self.request.session.get("consumption_result")
        if consumption_result is None:
            consumption_result = 40
        else:
            consumption_result = float(consumption_result)
        """

        consumption_result = 150 # needs to change to value of actual result
        if consumption_result < 50:
            roof_color = "#00b300"
            house_position = "8%"
        elif consumption_result < 100:
            roof_color = "#99cc00"
            house_position = "33%"
        elif consumption_result < 150:
            roof_color = "#ffcc00"
            house_position = "58%"
        else:
            roof_color = "#ff3300"
            house_position = "83%"
        context["roof_color"] = roof_color
        context["house_position"] = house_position
        return context


class IntroInventory(SidebarNavigationMixin, TemplateView):
    template_name = "pages/intro_inventory.html"
    extra_context = {
        "back_url": "heat:consumption_result",
        "next_url": "heat:roof",
    }


class IntroRenovation(SidebarNavigationMixin, TemplateView):
    template_name = "pages/intro_renovation.html"
    extra_context = {
        "back_url": "heat:ventilation_system",
        "next_url": "heat:renovation_request",
        "next_kwargs": "scenario1",
    }


def renovation_scenario(request, scenario=None):
    def get_new_scenario():
        """Goes through scenarios and checks if they have finished."""
        scenario_id = 1
        while scenario_id <= SCENARIO_MAX:
            flow = RenovationRequestFlow(prefix=f"scenario{scenario_id}")
            if not flow.finished():
                break
            scenario_id += 1
        return f"scenario{scenario_id}"

    # Needed to adapt URL vie redirect if necessary
    scenario_changed = scenario is None or scenario == "new_scenario"
    scenario = "scenario1" if scenario is None else scenario
    scenario = get_new_scenario() if scenario == "new_scenario" else scenario

    # Check if scenario ID is lower than max scenarios
    scenario_index = int(scenario[8:])
    if scenario_index > SCENARIO_MAX:
        return JsonResponse({"error": "Maximum number of scenarios reached."}, status=400)

    if scenario_changed:
        # If we return flow.dispatch(prefix=scenario), URL is not changed!
        return HttpResponseRedirect(reverse("heat:renovation_request", kwargs={"scenario": scenario}))
    flow = RenovationRequestFlow(prefix=scenario)
    return flow.dispatch(request)


class Results(SidebarNavigationMixin, TemplateView):
    template_name = "pages/results.html"
    extra_context = {
        "back_url": "heat:financial_support",
        "next_url": "heat:next_steps",
    }


class NextSteps(SidebarNavigationMixin, TemplateView):
    template_name = "pages/next_steps.html"
    extra_context = {
        "back_url": "heat:results",
    }
