from django.http import HttpResponseRedirect
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.urls import reverse
from django.views.generic import TemplateView

from building_dialouge_webapp.heat.flows import RenovationRequestFlow

from .navigation import SidebarNavigationMixin


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


SCENARIO_MAX = 3


def renovation_scenario(request, scenario=None):
    if "scenarios" not in request.session:
        request.session["scenarios"] = []

    if request.method == "GET":
        scenarios = request.session["scenarios"]

        if scenario != "new_scenario":
            request.session["scenarios"].append(scenario)
            request.session.modified = True
            flow = RenovationRequestFlow(prefix=scenario)
            return flow.dispatch(request)

        if len(scenarios) < SCENARIO_MAX:
            new_scenario = f"scenario{len(scenarios) + 1}"
            request.session["scenarios"].append(new_scenario)
            request.session.modified = True
            return HttpResponseRedirect(reverse("heat:renovation_request", kwargs={"scenario": new_scenario}))

        return JsonResponse({"error": "Maximum number of scenarios reached."}, status=400)

    if request.method == "POST" and request.htmx:
        if "save_scenario" in request.POST:
            # FLow States should save their data automatically
            session_data = request.session.get("django_htmx_flow", {})
            scenario_data = session_data
            # Return partial to be rendered with htmx, including the scenarioX fields
            return JsonResponse(
                {
                    "html": render_to_string("partials/scenario_box.html", {"scenario": scenario_data}),
                },
            )

        # For other HTMX requests, continue the flow
        flow = RenovationRequestFlow(prefix=scenario)
        return flow.dispatch(request)

    return JsonResponse({"error": "Invalid request."}, status=400)


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
