import inspect
from urllib.parse import urlparse

from django.http import HttpRequest
from django.http import HttpResponseRedirect
from django.http import JsonResponse
from django.urls import reverse
from django.views.generic import TemplateView
from django_htmx.http import HttpResponseClientRedirect

from . import flows
from . import forms
from . import settings as heat_settings
from . import tables
from .charts import energycost_chart
from .charts import heating_and_co2_chart
from .charts import heating_chart_vertical
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
    top_categories = ["Biomasseheizung", "Wärmepumpe", "Dach:", "Fassade:"]
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
        if name.endswith("Flow") and name not in {"Flow", "RenovationRequestFlow"}
    ]

    # Check if at least one instance of RenovationRequestFlow is finished
    finished_scenarios = get_finished_scenarios(request)

    not_finished = [name for name, flow in all_flows if not flow.finished(request)]
    if not finished_scenarios:
        not_finished.append("RenovationRequestFlow")
    return (True, []) if not not_finished else (False, not_finished)


def get_finished_scenarios(request: HttpRequest) -> list[str]:
    """Return finished scenarios."""
    finished_scenarios = []
    scenario_max = heat_settings.SCENARIO_MAX
    scenario_id = 1
    while scenario_id <= scenario_max:
        flow = flows.RenovationRequestFlow(prefix=f"scenario{scenario_id}")
        if flow.finished(request):
            finished_scenarios.append(f"scenario{scenario_id}")
        scenario_id += 1
    return finished_scenarios


class OptimizationStart(SidebarNavigationMixin, TemplateView):
    template_name = "pages/optimization_start.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["back_url"] = "heat:financial_support"
        context["next_disabled"] = True
        all_finished, not_finished = all_flows_finished(self.request)
        context["all_flows_finished"] = all_finished
        context["not_finished_flows"] = [
            step["name"]
            for category in context["index"]
            for step in category["steps"]
            if (isinstance(step["object"], list) and any(obj.__name__ in not_finished for obj in step["object"]))
            or (not isinstance(step["object"], list) and step["object"].__name__ in not_finished)
        ]
        context["scenarios"] = get_finished_scenarios(self.request)
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
                "change_heating": -29,
                "hydraulic_balancing": -7,
                "change_circuit_pump": -3,
                "insulate_heat_distribution": -7,
                "insulate_water_distribution": -3,
                "pv_battery": "nicht ausgewählt",
                "renovate_roof": -35,
                "replace_windows": -16,
                "insulate_basement_ceiling": "nicht ausgewählt",
            },
            "scenario2": {
                "change_heating": -52,
                "hydraulic_balancing": -3,
                "change_circuit_pump": -2,
                "insulate_heat_distribution": -3,
                "insulate_water_distribution": -2,
                "pv_battery": -6,
                "renovate_outer_facade": -11,
                "renovate_roof": -18,
                "replace_windows": "nicht ausgewählt",
                "insulate_basement_ceiling": -3,
            },
        }

        summary_data = {
            "scenario1": {
                "investments": {
                    "wood_chip_heating": 18000,
                    "hydraulic_balancing": 1000,
                    "change_circuit_pump": 1000,
                    "insulate_heat_distribution": 3000,
                    "insulate_water_distribution": 500,
                    "renovate_roof": 64500,
                    "replace_windows": 21500,
                },
                "subsidies": {
                    "heating_basic_subsidy": 7500,
                    "heating_income_bonus": 7500,
                    "heating_emission_reduction_bonus": 2500,
                    "bafa_building_envelope_subsidy": 12000,
                },
                "savings": {
                    "wood_chip_heating": 28800,
                    "hydraulic_comparison": 2600,
                    "change_circuit_pump": 770,
                    "insulate_heat_distribution": 3000,
                    "insulate_water_distribution": 770,
                    "renovate_roof": 15400,
                    "replace_windows": 6900,
                },
            },
            "scenario2": {
                "investments": {
                    "air_heat_pump": 21500,
                    "hydraulic_balancing": 1000,
                    "change_circuit_pump": 1000,
                    "insulate_heat_distribution": 3000,
                    "insulate_water_distribution": 500,
                    "pv_battery": 27500,
                    "renovate_outer_facade": 11000,
                    "renovate_roof": 64500,
                    "insulate_basement_ceiling": 8000,
                },
                "subsidies": {
                    "tax_advantage_subsidy": 825,
                    "heating_basic_subsidy": 5500,
                    "heating_income_bonus": 8500,
                    "heating_emission_reduction_bonus": 5500,
                    "bafa_building_envelope_subsidy": 12000,
                },
                "savings": {
                    "air_heat_pump": 17000,
                    "hydraulic_comparison": 3600,
                    "change_circuit_pump": 900,
                    "insulate_heat_distribution": 4400,
                    "insulate_water_distribution": 900,
                    "pv_battery": 22200,
                    "renovate_outer_facade": 12400,
                    "renovate_roof": 21300,
                    "insulate_basement_ceiling": 3600,
                },
            },
            "scenario3": {
                "investments": {
                    "air_heat_pump": 21500,
                    "hydraulic_balancing": 1000,
                    "change_circuit_pump": 1000,
                    "insulate_heat_distribution": 3000,
                    "insulate_water_distribution": 500,
                    "pv_battery": 27500,
                    "renovate_outer_facade": 11000,
                    "renovate_roof": 64500,
                    "insulate_basement_ceiling": 8000,
                },
                "subsidies": {
                    "tax_advantage_subsidy": 825,
                    "heating_basic_subsidy": 5500,
                    "heating_income_bonus": 8500,
                    "heating_emission_reduction_bonus": 5500,
                    "bafa_building_envelope_subsidy": 12000,
                },
                "savings": {
                    "air_heat_pump": 17000,
                    "hydraulic_comparison": 3600,
                    "change_circuit_pump": 900,
                    "insulate_heat_distribution": 4400,
                    "insulate_water_distribution": 900,
                    "pv_battery": 22200,
                    "renovate_outer_facade": 12400,
                    "renovate_roof": 21300,
                    "insulate_basement_ceiling": 3600,
                },
            },
        }
        energy_consumption = [160.0, 20.0, 50.0]
        energy_consumption_transform = []
        for consumption_value in energy_consumption:
            transform = 0.729722 * consumption_value - 32.1912  # approximating to scale on graphic
            transform = f"{round(transform, 2):.2f}".replace(",", ".")  # putting "." and then going for string
            energy_consumption_transform.append(transform)

        scenario_list = []
        for i, (scenario_name, scenario_data) in enumerate(summary_data.items(), start=1):
            scenario_id = f"tab_scenario{i}"
            investment_table = tables.InvestmentTable(scenario_data).to_html(f"{scenario_name} summary_table")
            subsidies_table = tables.SubsidiesTable(scenario_data).to_html(f"{scenario_name} summary_table")
            savings_table = tables.EnergySavingsTable(scenario_data).to_html(f"{scenario_name} summary_table")
            total_cost_table = tables.TotalCostTable(scenario_data).to_html(
                f"{scenario_name} summary_table summary_table_highlight_last_row",
            )
            total_cost_15_years_table = tables.TotalCost15YearsTable(scenario_data).to_html(
                f"{scenario_name} summary_table summary_table_highlight_last_row",
            )

            scenario_list.append(
                {
                    "index": i,
                    "id": scenario_id,
                    "label": f"Szenario {i}",
                    "energy_consumption": energy_consumption[i - 1],
                    "transform_horizontal": energy_consumption_transform[i - 1],
                    "investment_table": investment_table,
                    "subsidies_table": subsidies_table,
                    "savings_table": savings_table,
                    "total_cost_table": total_cost_table,
                    "total_cost_15_years_table": total_cost_15_years_table,
                },
            )

        consumption_table = tables.ConsumptionTable(consumption_data)
        consumption_table_html = consumption_table.to_html(title="consumption_table")
        # Kontext hinzufügen
        context["html_content"] = "<Hallo>"
        context["hectare_scenario1"] = 1.4
        context["hectare_scenario2"] = 1.25
        context["consumption_table_html"] = consumption_table_html
        context["scenarios"] = scenario_list
        context["heating_chart_data"] = heating_chart_vertical.generate_vertical_echarts_option(
            months=["Jan", "Feb", "Mär", "Apr", "Mai", "Jun", "Jul", "Aug", "Sep", "Okt", "Nov", "Dez"],
            scenarios=[
                {
                    "name": "Szenario 1",
                    "values": [
                        3468.164547397838,
                        3033.178038349136,
                        2776.8431747565123,
                        1807.908995161528,
                        1038.37207426303,
                        590.005415215605,
                        443.0399715349141,
                        424.40763799495966,
                        687.827991548195,
                        1432.850252308145,
                        2453.095525606935,
                        3345.5603939823663,
                    ],
                    "color": "#1b9e77",
                },
                {
                    "name": "Szenario 2",
                    "values": [
                        457.21460496882776,
                        401.7522643955988,
                        375.9754775656805,
                        257.22107134751735,
                        159.39529865567033,
                        97.67117642479182,
                        76.16884597672653,
                        73.2881691214471,
                        111.5659844745372,
                        211.33609069766447,
                        335.7687021132994,
                        442.7838328978601,
                    ],
                    "color": "#7570b3",
                },
            ],
            y_axis_label="kWh",
        )
        context["financial_expense_chart_data_future"] = heating_and_co2_chart.generate_echarts_option(
            scenarios=[
                {"name": "Szenario 1", "value": 50260},
                {"name": "Szenario 2", "value": 8875},
            ],
            title="",
        )
        context["financial_expense_chart_data_now"] = heating_and_co2_chart.generate_echarts_option(
            scenarios=[
                {"name": "Szenario 1", "value": 108500},
                {"name": "Szenario 2", "value": 95175},
            ],
            title="",
        )
        context["energycost_chart_data"] = energycost_chart.generate_grouped_echarts_option(
            scenarios=[
                {"name": "Ausgangszustand", "value": [1550, 5260]},
                {"name": "Szenario 1", "value": [1420, 1490]},
                {"name": "Szenario 2", "value": [70, 990]},
            ],
            title="",
        )
        context["co2_chart_data"] = heating_and_co2_chart.generate_echarts_option(
            scenarios=[
                {"name": "Heute", "value": 825},
                {"name": "Szenario 1", "value": 55},
                {"name": "Szenario 2", "value": 137},
            ],
            title="",
        )
        context["scenario_boxes"] = get_all_scenario_data(self.request)
        return context


class NextSteps(SidebarNavigationMixin, TemplateView):
    template_name = "pages/next_steps.html"
    extra_context = {
        "back_url": "heat:results",
    }


def show_session(request: HttpRequest) -> JsonResponse:
    """Show session. May be used by developers only."""
    return JsonResponse(dict(request.session))
