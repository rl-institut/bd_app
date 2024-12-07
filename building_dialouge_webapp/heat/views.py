import inspect

from django.http import HttpResponseRedirect
from django.http import JsonResponse
from django.urls import reverse
from django.views.generic import TemplateView

from building_dialouge_webapp.heat.flows import RenovationRequestFlow

from . import forms
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
            if not flow.finished(request):
                break
            scenario_id += 1
        return f"scenario{scenario_id}"

    # Needed to adapt URL via redirect if necessary
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
    flow.extra_context.update({"scenario_boxes": get_all_scenario_data(request)})
    return flow.dispatch(request)


def get_all_scenario_data(request):
    """Goes through scenarios and gets their data if finished."""
    scenario_data_list = []
    scenario_id = 1
    while scenario_id <= SCENARIO_MAX:
        flow = RenovationRequestFlow(prefix=f"scenario{scenario_id}")
        if not flow.finished(request):
            break
        scenario_data = flow.data(request)
        user_friendly_data = get_user_friendly_data(form_surname="Renovation", scenario_data=scenario_data)
        extra_context = {
            "id": f"scenario{scenario_id}box",
            "href": reverse("heat:renovation_request", kwargs={"scenario": f"scenario{scenario_id}"}),
            "title": f"Szenario {scenario_id}",
            "text": ", ".join(user_friendly_data),
        }
        scenario_data_list.append(extra_context)
        scenario_id += 1
    return scenario_data_list


def get_user_friendly_data(form_surname, scenario_data):
    user_friendly_data = []

    flow_forms = [
        form_class()
        for name, form_class in inspect.getmembers(forms, inspect.isclass)
        if name.startswith(form_surname)
    ]

    # add labels from forms for easier readability
    for form in flow_forms:
        for field_name, field in form.fields.items():
            if field_name in scenario_data:
                value = scenario_data[field_name]

                if value:
                    if isinstance(value, list):  # For multiple-choice fields
                        labels = [dict(field.choices).get(v, v) for v in value]
                        user_friendly_data.extend(labels)
                    elif isinstance(value, bool):
                        user_friendly_data.append(field.label)
                    else:
                        user_friendly_data.append(dict(field.choices).get(value, value))
    return user_friendly_data


class RenovationOverview(SidebarNavigationMixin, TemplateView):
    template_name = "pages/renovation_overview.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["back_url"] = "heat:renovation_request"
        context["next_url"] = "heat:financial_support"
        context["scenario_boxes"] = get_all_scenario_data(self.request)
        return context


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
