import inspect
from urllib.parse import urlparse

from django.http import HttpResponseRedirect
from django.http import JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.views.generic import TemplateView
from django_htmx.http import HttpResponseClientRedirect

from . import flows
from . import forms
from . import settings as heat_settings
from . import tables
from .charts import cost_emission_chart
from .charts import heating_and_co2_chart
from .charts import investment_costs_chart
from .forms import RoofOrientationForm
from .navigation import SidebarNavigationMixin


class LandingPage(TemplateView):
    template_name = "pages/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        flow_data_present = False
        if self.request.session.get("django_htmx_flow"):
            flow_data_present = True
        context["session"] = {"flow_data_present": flow_data_present, "flow_url": reverse("heat:intro_inventory")}
        return context


class DeadEndTenant(TemplateView):
    template_name = "pages/dead_end_tenant.html"
    extra_context = {
        "back_url": "heat:home",
        "next_disabled": True,
    }


class IntroInventory(SidebarNavigationMixin, TemplateView):
    template_name = "pages/intro_inventory.html"
    extra_context = {
        "back_url": "heat:home",
        "next_url": "heat:building_type",
    }


class DeadEndMonumentProtection(TemplateView):
    template_name = "pages/dead_end_monument_protection.html"
    extra_context = {
        "back_url": "heat:building_type",
        "next_disabled": True,
    }


def reset_session(request):
    """Resets session to clean user inputs."""
    request.session.clear()
    return JsonResponse({"success": True})


def delete_flow(request):
    """
    Delete the selected year or scenario.
    Handles 2 different use cases:
    1 - if url_instance is not part of flow id we are deleting a different object and want to stay on page
    2 - we are deleting the object we are currently editing, we want to go to overview
    """
    current_url = request.headers.get("hx-current-url")
    parsed_url = urlparse(current_url)
    url_path = parsed_url.path.strip("/").split("/")  # len(url_path > 1 if coming from flow, otherwise 1)
    # url_instance comes from the request, it is the page from wich we are calling delete
    url_instance = url_path[-1] if len(url_path) > 1 else url_path[0]

    # flow_id comes from the object that we are deleting
    flow_id = request.POST.get("delete_flow")
    if flow_id.startswith("scenario"):
        prefix = flow_id[:9]
        flow = flows.RenovationRequestFlow(prefix=prefix)
        flow.reset(request)

        if len(url_path) == 1:
            return HttpResponseClientRedirect(reverse("heat:renovation_overview"))
        if not flow_id.startswith(url_instance):
            return HttpResponseClientRedirect(reverse("heat:renovation_request", kwargs={"scenario": url_instance}))
        overview_url = "heat:renovation_overview"
    return HttpResponseClientRedirect(reverse(overview_url))


def roof_orientation(request):
    form = RoofOrientationForm()
    return render(request, "partials/roof_orientation.html", {"form": form})


class ConsumptionResult(SidebarNavigationMixin, TemplateView):
    template_name = "pages/consumption_result.html"
    extra_context = {
        "back_url": "heat:intro_inventory",
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


class IntroRenovation(SidebarNavigationMixin, TemplateView):
    template_name = "pages/intro_renovation.html"
    extra_context = {
        "back_url": "heat:pv_system",
        "next_url": "heat:renovation_overview",
    }


def renovation_scenario(request, scenario=None):
    scenario_max = heat_settings.SCENARIO_MAX
    # Needed to adapt URL via redirect if necessary
    scenario_changed = False
    # scenario is none when renovation_request first called or when opened via back-button
    if scenario is None or scenario == "new_scenario":
        scenario = get_new_scenario(request)
        scenario_changed = True
    # Check if scenario ID is lower than max scenarios
    scenario_index = int(scenario[8:])
    if scenario_index > scenario_max:
        return JsonResponse(
            {"error": "Maximum number of scenarios reached."},
            status=400,
        )
    if scenario_changed:
        # If we return flow.dispatch(prefix=scenario), URL is not changed!
        return HttpResponseRedirect(
            reverse("heat:renovation_request", kwargs={"scenario": scenario}),
        )
    flow = flows.RenovationRequestFlow(prefix=scenario)
    flow.extra_context.update({"scenario_boxes": get_all_scenario_data(request)})
    return flow.dispatch(request)


def get_new_scenario(request):
    """Goes through scenarios and checks if they have finished."""
    scenario_max = heat_settings.SCENARIO_MAX
    scenario_id = 1
    while scenario_id <= scenario_max:
        flow = flows.RenovationRequestFlow(prefix=f"scenario{scenario_id}")
        if not flow.finished(request):
            break
        scenario_id += 1
    return f"scenario{scenario_id}"


def get_all_scenario_data(request):
    """Goes through scenarios and gets their data if finished."""
    scenario_max = heat_settings.SCENARIO_MAX
    scenario_data_list = []
    scenario_id = 1
    while scenario_id <= scenario_max:
        flow = flows.RenovationRequestFlow(prefix=f"scenario{scenario_id}")
        if not flow.finished(request):
            scenario_id += 1
            continue
        scenario_data = flow.data(request)

        extra_context = {
            "id": f"scenario{scenario_id}box",
            "href": reverse(
                "heat:renovation_request",
                kwargs={"scenario": f"scenario{scenario_id}"},
            ),
            "title": f"Szenario {scenario_id}",
            "heating_choices": get_heating_choices(scenario_data),
            "renovation_choices": get_renovation_choices(scenario_data),
        }
        scenario_data_list.append(extra_context)
        scenario_id += 1
    return scenario_data_list


def get_heating_choices(scenario_data) -> list:
    """
    Define wich form classes should be used for heating in scenario box.
    """
    form_classes = [
        forms.RenovationTechnologyForm,
        forms.RenovationHeatPumpForm,
        forms.RenovationBioMassForm,
        forms.RenovationPVSolarForm,
        forms.RenovationSolarForm,
    ]
    return get_user_friendly_data(scenario_data, form_classes)


def get_renovation_choices(scenario_data) -> list:
    """
    Define wich form classes should be used for renovation in scenario box.
    """
    form_classes = [
        forms.RenovationRequestForm,
    ]
    return get_user_friendly_data(scenario_data, form_classes)


def get_user_friendly_data(scenario_data, form_classes: list) -> list:
    """
    Instantiate the Forms for flows.RenovationRequestFlow and get all checked / chosen
    labels for easier readability.
    """
    choices = []

    renovation_forms = [form_class() for form_class in form_classes]

    for form in renovation_forms:
        for field_name, field in form.fields.items():
            if field_name.endswith("hidden"):
                continue

            if scenario_data.get(field_name):
                value = scenario_data[field_name]
                if isinstance(value, list):  # Multiple-choice fields
                    labels = [dict(field.choices).get(v) for v in value if v in dict(field.choices)]
                elif isinstance(value, bool):
                    labels = [field.label]
                else:  # Select-fields / Radiobuttons
                    labels = [dict(field.choices).get(value)] if value in dict(field.choices) else []

                choices.extend(labels)
    # remove duplicates
    choices = list(dict.fromkeys(choices))
    # remove categories that have further specification
    top_categories = ["Biomasseheizung", "Wärmepumpe", "Dach"]
    for category in top_categories:
        if category in choices:
            choices.remove(category)
    return choices


class RenovationOverview(SidebarNavigationMixin, TemplateView):
    template_name = "pages/renovation_overview.html"

    def get_context_data(self, **kwargs):
        scenario_max = heat_settings.SCENARIO_MAX
        context = super().get_context_data(**kwargs)
        context["back_url"] = "heat:intro_renovation"
        context["next_url"] = "heat:financial_support"
        context["scenario_boxes"] = get_all_scenario_data(self.request)
        context["next_disabled"] = check_for_min(self.request)
        context["max_reached"] = int(get_new_scenario(self.request)[8:]) > scenario_max
        return context


def check_for_min(request):
    """
    Checks if there is at least one renovation scenario saved already. Returns True if thats not the case, since
    then the next-button is diabled.

    """
    scenario_max = heat_settings.SCENARIO_MAX
    scenario_id = 1
    next_disabled = True  # disables next button if minimun not reached
    while scenario_id <= scenario_max:
        flow = flows.RenovationRequestFlow(prefix=f"scenario{scenario_id}")
        if flow.finished(request):
            next_disabled = False
            break
        scenario_id += 1

    return next_disabled


def all_flows_finished(request):
    """
    Checks all Flows if they are finished. Either returns a all_flows_finished = True flag or Flase
    and a list with the Flows that need more input.
    """
    all_flows = [
        (name, flow())
        for name, flow in inspect.getmembers(flows, inspect.isclass)
        if name.endswith("Flow") and name not in {"Flow", "flows.RenovationRequestFlow"}
    ]

    # Check if at least one instance of RenovationRequestFlow is finished
    scenario_max = heat_settings.SCENARIO_MAX
    scenario_id = 1
    has_finished_renovation = False
    while scenario_id <= scenario_max:
        flow = flows.RenovationRequestFlow(prefix=f"scenario{scenario_id}")
        if flow.finished(request):
            has_finished_renovation = True
            break
        scenario_id += 1

    not_finished = [name for name, flow in all_flows if not flow.finished(request)]
    if not has_finished_renovation:
        not_finished.append("RenovationRequestFlow")
    return (True, []) if not not_finished else (False, not_finished)


class OptimizationStart(SidebarNavigationMixin, TemplateView):
    template_name = "pages/optimization_start.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["back_url"] = "heat:financial_support"
        context["next_url"] = "heat:results"
        all_finished, not_finished = all_flows_finished(self.request)
        context["all_flows_finished"] = all_finished
        context["not_finished_flows"] = [
            step["name"]
            for category in context["index"]
            for step in category["steps"]
            if (isinstance(step["object"], list) and any(obj.__name__ in not_finished for obj in step["object"]))
            or (not isinstance(step["object"], list) and step["object"].__name__ in not_finished)
        ]
        return context


def simulate(request):
    """
    Takes all data from Session and calculates the results.
    """
    # TODO: implement functionality
    # try "next_disabled": True, for the next button to only work after sim finished
    # maybe some UI stuff for showing that sth is happening in the back


class Results(SidebarNavigationMixin, TemplateView):
    template_name = "pages/results.html"
    extra_context = {
        "back_url": "heat:optimization_start",
        "next_url": "heat:next_steps",
    }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        consumption_data = {
            "scenario1": {
                "change_heating": -50,
                "renovate_facade": -50,
            },
            "scenario2": {
                "change_heating": -88,
                "renovate_facade": -50,
                "renovate_roof": -45,
            },
        }

        investment_data = {
            "scenario1": {
                "investment": 95800,
                "contribution": -13800,
            },
            "scenario2": {
                "investment": 167280,
                "contribution": -25090,
            },
        }

        summary_data = {
            "scenario1": {
                "investments": {
                    "air_heat_pump": 20700,
                    "thermal_storage": 2980,
                    "heat_meter": 260,
                    "heating_system_pump": 480,
                    "ventilation_system": 9620,
                    "insulate_outer_facade": 36890,
                },
                "subsidies": {
                    "KfW - Bundesförderung für effiziente Gebäude - Heizungsförderung für Privatpersonen - "
                    "Wohnungsgebäude (BEG EM) (Nr. 458) (Zuschuss inkl. Klima-Bonus)": 23158.07,
                },
            },
            "scenario2": {
                "investments": {
                    "air_heat_pump": 28700,
                    "thermal_storage": 1980,
                    "heat_meter": 260,
                    "heating_system_pump": 480,
                    "ventilation_system": 9620,
                    "insulate_roof": 38980,
                    "insulate_outer_facade": 36890,
                },
                "subsidies": {
                    "KfW - Bundesförderung für effiziente Gebäude - Heizungsförderung für Privatpersonen - "
                    "Wohnungsgebäude (BEG EM) (Nr. 458) (Zuschuss inkl. Klima-Bonus)": 23158.07,
                    "KfW - Bundesförderung für effiziente Gebäude - Heizungsförderung für Privatpersonen - "
                    "Wohnungsgebäude (BEG EM) (Nr. 458) (Effizienz-Bonus)": 1931.93,
                },
            },
        }

        scenario_list = []
        for i, (scenario_name, scenario_data) in enumerate(summary_data.items(), start=1):
            scenario_id = f"tab_scenario{i}"
            investment_table = tables.InvestmentTable(scenario_data).to_html(f"{scenario_name} summary_table")
            subsidies_table = tables.SubsidiesTable(scenario_data).to_html(f"{scenario_name} summary_table")
            total_cost_table = tables.TotalCostTable(scenario_data).to_html(f"{scenario_name} summary_table")

            scenario_list.append(
                {
                    "index": i,
                    "id": scenario_id,
                    "label": f"Szenario {i}",
                    "investment_table": investment_table,
                    "subsidies_table": subsidies_table,
                    "total_cost_table": total_cost_table,
                },
            )

        consumption_table = tables.ConsumptionTable(consumption_data)
        consumption_table_html = consumption_table.to_html(title="consumption_table")
        investment_summary_table = tables.InvestmentSummaryTable(investment_data)
        investment_summary_table_html = investment_summary_table.to_html(title="investment_table")
        # Kontext hinzufügen
        context["html_content"] = "<Hallo>"
        context["hectare_scenario1"] = 2.2
        context["hectare_scenario2"] = 1.3
        context["consumption_table_html"] = consumption_table_html
        context["investment_summary_table_html"] = investment_summary_table_html
        context["scenarios"] = scenario_list
        context["cost_chart_data"] = cost_emission_chart.create_echarts_cost_emission(
            title="Kosten",
            unit="€",
            data=cost_emission_chart.EXAMPLE_COST_DATA,
        )
        context["emission_chart_data"] = cost_emission_chart.create_echarts_cost_emission(
            title="Emissionen",
            unit="t/a",
            data=cost_emission_chart.EXAMPLE_EMISSION_DATA,
        )
        context["heating_chart_data"] = heating_and_co2_chart.generate_echarts_option(
            scenarios=[
                {"name": "Heute", "value": 230},
                {"name": "Szenario 1", "value": 130},
                {"name": "Szenario 2", "value": 47},
            ],
            title="Heizenergieverbrauch in kWh/(m²*a) (Endenergie)",
        )
        context["co2_chart_data"] = heating_and_co2_chart.generate_echarts_option(
            scenarios=[
                {"name": "Heute", "value": 2600},
                {"name": "Szenario 1", "value": 1200},
                {"name": "Szenario 2", "value": 700},
            ],
            title="CO2-Kosten in € pro Jahr",
        )
        context["investment_chart_data"] = investment_costs_chart.generate_investment_chart_options(
            scenarios=[
                {"name": "Szenario 1", "renovation": 55000, "maintenance": 45000},
                {"name": "Szenario 2", "renovation": 100000, "maintenance": 67250},
            ],
        )
        return context


class NextSteps(SidebarNavigationMixin, TemplateView):
    template_name = "pages/next_steps.html"
    extra_context = {
        "back_url": "heat:results",
    }
