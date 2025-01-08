import inspect
from urllib.parse import urlparse

from django.http import HttpResponseRedirect
from django.http import JsonResponse
from django.urls import reverse
from django.views.generic import TemplateView
from django_htmx.http import HttpResponseClientRedirect

from building_dialouge_webapp.heat.flows import ConsumptionInputFlow
from building_dialouge_webapp.heat.flows import RenovationRequestFlow

from . import forms
from .navigation import SidebarNavigationMixin

SCENARIO_MAX = 3
YEAR_MAX = 4


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


def consumption_year(request, year=None):
    # year is none when consumption_input first called or when opened via navigation sidebar or back-button
    year_changed = False
    if year is None or year == "new_year":
        year = get_new_year(request)
        year_changed = True
    # Check if year ID is lower than max years
    year_index = int(year[4:])
    if year_index > YEAR_MAX:
        return JsonResponse({"error": "Maximum number of years reached."}, status=400)

    if year_changed:
        # If we return flow.dispatch(prefix=year), URL is not changed!
        return HttpResponseRedirect(reverse("heat:consumption_input", kwargs={"year": year}))
    flow = ConsumptionInputFlow(prefix=year)
    flow.extra_context.update({"year_boxes": get_all_year_data(request)})
    return flow.dispatch(request)


def get_new_year(request):
    """Goes through years and checks if they have finished."""
    year_id = 1
    while year_id < YEAR_MAX:
        flow = ConsumptionInputFlow(prefix=f"year{year_id}")
        if not flow.finished(request):
            break
        year_id += 1
    return f"year{year_id}"


def delete_flow(request):
    """Delete the selected year or scenario."""
    # get only the "name" part of the url for reversing
    current_url = request.headers.get("hx-current-url")
    parsed_url = urlparse(current_url)
    url_path = parsed_url.path.strip("/").split("/")
    url_name = url_path[-2] if len(url_path) > 1 else url_path[0]

    flow_id = request.POST.get("delete_flow")

    if flow_id.startswith("year"):
        prefix = flow_id[:5]
        flow = ConsumptionInputFlow(prefix=prefix)
    elif flow_id.startswith("scenario"):
        prefix = flow_id[:9]
        flow = RenovationRequestFlow(prefix=prefix)

    flow.reset(request)
    return HttpResponseClientRedirect(reverse(f"heat:{url_name}"))


def get_all_year_data(request):
    """Goes through years and gets their data if finished."""
    year_data_list = []
    year_id = 1
    while year_id <= YEAR_MAX:
        flow = ConsumptionInputFlow(prefix=f"year{year_id}")
        if not flow.finished(request):
            year_id += 1
            continue

        extra_context = {
            "id": f"year{year_id}box",
            "href": reverse("heat:consumption_input", kwargs={"year": f"year{year_id}"}),
            "title": f"Zeitraum {year_id}",
            "text": "",
        }
        year_data_list.append(extra_context)
        year_id += 1
    return year_data_list


class ConsumptionOverview(SidebarNavigationMixin, TemplateView):
    template_name = "pages/consumption_overview.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["back_url"] = "heat:hotwater_heating"
        context["next_url"] = "heat:consumption_result"
        context["year_boxes"] = get_all_year_data(self.request)
        context["max_reached"] = int(get_new_year(self.request)[4:]) > YEAR_MAX
        return context


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
        consumption_max_a = 50
        consumption_max_b = 100
        consumption_max_c = 150

        consumption_result = 150  # needs to change to value of actual result
        if consumption_result < consumption_max_a:
            roof_color = "#00b300"
            house_position = "8%"
        elif consumption_result < consumption_max_b:
            roof_color = "#99cc00"
            house_position = "33%"
        elif consumption_result < consumption_max_c:
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
    }


def renovation_scenario(request, scenario=None):
    # Needed to adapt URL via redirect if necessary
    scenario_changed = False
    # scenario is none when renovation_request first called or when opened via back-button
    if scenario is None or scenario == "new_scenario":
        scenario = get_new_scenario(request)
        scenario_changed = True
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


def get_new_scenario(request):
    """Goes through scenarios and checks if they have finished."""
    scenario_id = 1
    while scenario_id < SCENARIO_MAX:
        flow = RenovationRequestFlow(prefix=f"scenario{scenario_id}")
        if not flow.finished(request):
            break
        scenario_id += 1
    return f"scenario{scenario_id}"


def get_all_scenario_data(request):
    """Goes through scenarios and gets their data if finished."""
    scenario_data_list = []
    scenario_id = 1
    while scenario_id <= SCENARIO_MAX:
        flow = RenovationRequestFlow(prefix=f"scenario{scenario_id}")
        if not flow.finished(request):
            scenario_id += 1
            continue
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
            if scenario_data.get(field_name):
                value = scenario_data[field_name]

                if isinstance(value, list):  # For multiple-choice fields
                    labels = [dict(field.choices).get(v) for v in value if v in dict(field.choices)]
                    user_friendly_data.extend(labels)
                elif isinstance(value, bool):
                    user_friendly_data.append(field.label)
                else:  # for select-fields / radiobuttons
                    label = dict(field.choices).get(value)
                    if label:
                        user_friendly_data.append(label)
    return list(set(user_friendly_data))


class RenovationOverview(SidebarNavigationMixin, TemplateView):
    template_name = "pages/renovation_overview.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["back_url"] = "heat:renovation_request"
        context["next_url"] = "heat:financial_support"
        context["scenario_boxes"] = get_all_scenario_data(self.request)
        context["max_reached"] = int(get_new_scenario(self.request)[8:]) > SCENARIO_MAX
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
