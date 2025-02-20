import datetime
import inspect
from urllib.parse import urlparse

from django.contrib import messages
from django.contrib.messages import get_messages
from django.http import HttpResponseRedirect
from django.http import JsonResponse
from django.urls import reverse
from django.views.generic import TemplateView
from django_htmx.http import HttpResponseClientRedirect

from building_dialouge_webapp.heat.flows import ConsumptionInputFlow
from building_dialouge_webapp.heat.flows import RenovationRequestFlow

from . import flows
from . import forms
from . import tables
from .navigation import SidebarNavigationMixin

SCENARIO_MAX = 3
COONSUMPTION_MAX = 6
POWER_MAX = 3
HEATING_MAX = 3


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
    if flow_id.startswith("year"):
        prefix = flow_id[:5]
        flow = ConsumptionInputFlow(prefix=prefix)
        flow.reset(request)

        if len(url_path) == 1:
            return HttpResponseClientRedirect(reverse("heat:consumption_overview"))
        if not flow_id.startswith(url_instance):
            return HttpResponseClientRedirect(reverse("heat:consumption_input", kwargs={"year": url_instance}))
        overview_url = "heat:consumption_overview"
    if flow_id.startswith("scenario"):
        prefix = flow_id[:9]
        flow = RenovationRequestFlow(prefix=prefix)
        flow.reset(request)

        if len(url_path) == 1:
            return HttpResponseClientRedirect(reverse("heat:renovation_overview"))
        if not flow_id.startswith(url_instance):
            return HttpResponseClientRedirect(reverse("heat:renovation_request", kwargs={"scenario": url_instance}))
        overview_url = "heat:renovation_overview"
    return HttpResponseClientRedirect(reverse(overview_url))


def consumption_year(request, year=None):
    # year is none when consumption_input first called or when opened via navigation sidebar or back-button
    year_changed = False

    # Count existing heating and power instances
    year_data = get_all_year_data(request)
    heating_count = sum(1 for data in year_data if data["type_class"] == "heating")
    power_count = sum(1 for data in year_data if data["type_class"] == "power")

    if year is None or year == "new_year":
        year = get_new_year(request)
        year_changed = True

    if year_changed:
        return HttpResponseRedirect(reverse("heat:consumption_input", kwargs={"year": year}))
    # Check if adding another instance would exceed the maximum limits
    existing_messages = [m.message for m in get_messages(request)]
    if heating_count >= HEATING_MAX and power_count < POWER_MAX:
        message_text = (
            "Maximale Anzahl an Wärmeverbraucheingaben erreicht, "
            "Sie können nur noch Stromverbraucheingaben hinzufügen."
        )
        if message_text not in existing_messages:
            messages.add_message(request, messages.INFO, message_text)
    if heating_count < HEATING_MAX and power_count >= POWER_MAX:
        message_text = (
            "Maximale Anzahl an Stromverbraucheingaben erreicht, "
            "Sie können nur noch Wärmeverbraucheingaben hinzufügen."
        )
        if message_text not in existing_messages:
            messages.add_message(request, messages.INFO, message_text)
    flow = ConsumptionInputFlow(prefix=year)
    flow.extra_context.update({"year_boxes": year_data})
    return flow.dispatch(request)


def get_new_year(request):
    """Goes through years and checks if they have finished."""
    year_id = 1
    while year_id <= COONSUMPTION_MAX:
        flow = ConsumptionInputFlow(prefix=f"year{year_id}")
        if not flow.finished(request):
            break
        year_id += 1
    return f"year{year_id}"


def get_all_year_data(request):
    """Goes through years and gets their data if finished."""
    year_data_list = []
    year_id = 1
    heating_count = 0
    power_count = 0
    while year_id <= COONSUMPTION_MAX:
        flow = ConsumptionInputFlow(prefix=f"year{year_id}")
        if not flow.finished(request):
            year_id += 1
            continue

        class_type, title, text = get_user_friendly_data_consumption(flow.data(request))

        if class_type == "heating":
            if heating_count >= HEATING_MAX:
                year_id += 1
                continue  # Skip if max heating flows reached
            heating_count += 1
        elif class_type == "power":
            if power_count >= POWER_MAX:
                year_id += 1
                continue  # Skip if max power flows reached
            power_count += 1

        extra_context = {
            "type_class": class_type,
            "id": f"year{year_id}box",
            "href": reverse("heat:consumption_input", kwargs={"year": f"year{year_id}"}),
            "title": f"{year_id} {title}",
            "text": text,
        }
        year_data_list.append(extra_context)
        year_id += 1
    return year_data_list


def get_user_friendly_data_consumption(scenario_data):
    """What I need to output here:
    either: heating_consumption + heating_consumption_unit and duration
     or: power_consumption + kWh and duration"""
    user_friendly_data = []

    if scenario_data["consumption_type"] == "heating":
        class_type = "heating"
        title = "Wärmeverbrauch"
        consumption_value = scenario_data["heating_consumption"]
        consumption_unit = scenario_data["heating_consumption_unit"]
        start_date = format_date_output(scenario_data["heating_consumption_period_start"])
        end_date = format_date_output(scenario_data["heating_consumption_period_end"])
    else:
        class_type = "power"
        title = "Stromverbrauch"
        consumption_value = scenario_data["power_consumption"]
        consumption_unit = "kwH"
        start_date = format_date_output(scenario_data["power_consumption_period_start"])
        end_date = format_date_output(scenario_data["power_consumption_period_end"])
    user_friendly_data.append(f"{start_date} - {end_date}")
    user_friendly_data.append(f"{consumption_value} {consumption_unit}")

    return class_type, title, user_friendly_data


def format_date_output(date: str):
    """Adjust all date outputs in the same way."""
    date_object = datetime.date.fromisoformat(date)
    # strftime("%d.%m.%Y") makes 01.01.2010
    return date_object.strftime("%d.%m.%Y")


class ConsumptionOverview(SidebarNavigationMixin, TemplateView):
    template_name = "pages/consumption_overview.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["back_url"] = "heat:hotwater_heating"
        context["next_url"] = "heat:consumption_result"
        context["year_boxes"] = get_all_year_data(self.request)
        next_disabled, not_finished = check_if_new_year_possible(self.request, context["year_boxes"])
        context["next_disabled"] = next_disabled
        context["max_reached"] = int(get_new_year(self.request)[4:]) > COONSUMPTION_MAX
        context["not_finished_flows"] = not_finished
        return context


def check_if_new_year_possible(request, year_boxes):
    """
    Checks Flows that are necessary for Consumption Input Validation if they are finished.
    And checks if there are at least one of power and one of heating instances already.
    returns next_disabled = True, if one of these conditions fail.
    """
    needed_flow_classes = [
        ("HotwaterHeatingFlow", flows.HotwaterHeatingFlow),
        ("BuildingDataFlow", flows.BuildingDataFlow),
    ]
    needed_flows = [(name, form_class()) for name, form_class in needed_flow_classes]
    not_finished = [name for name, flow in needed_flows if not flow.finished(request)]
    if not_finished:
        next_disabled = True
        return next_disabled, not_finished
    has_power = any(box.get("type_class") == "power" for box in year_boxes)
    has_heating = any(box.get("type_class") == "heating" for box in year_boxes)
    next_disabled = True if not has_power or not has_heating else False  # noqa: SIM210
    return next_disabled, []


class ConsumptionResult(SidebarNavigationMixin, TemplateView):
    template_name = "pages/consumption_result.html"
    extra_context = {
        "back_url": "heat:consumption_overview",
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
        "next_url": "heat:renovation_overview",
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
        return JsonResponse(
            {"error": "Maximum number of scenarios reached."},
            status=400,
        )
    if scenario_changed:
        # If we return flow.dispatch(prefix=scenario), URL is not changed!
        return HttpResponseRedirect(
            reverse("heat:renovation_request", kwargs={"scenario": scenario}),
        )
    flow = RenovationRequestFlow(prefix=scenario)
    flow.extra_context.update({"scenario_boxes": get_all_scenario_data(request)})
    return flow.dispatch(request)


def get_new_scenario(request):
    """Goes through scenarios and checks if they have finished."""
    scenario_id = 1
    while scenario_id <= SCENARIO_MAX:
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
        heating_choices, renovation_choices = get_user_friendly_data(scenario_data=scenario_data)
        extra_context = {
            "id": f"scenario{scenario_id}box",
            "href": reverse(
                "heat:renovation_request",
                kwargs={"scenario": f"scenario{scenario_id}"},
            ),
            "title": f"Szenario {scenario_id}",
            "heating_choices": heating_choices,
            "renovation_choices": renovation_choices,
        }
        scenario_data_list.append(extra_context)
        scenario_id += 1
    return scenario_data_list


def get_user_friendly_data(scenario_data):
    """
    Instantiate the Forms for RenovationRequestFlow and get all checked / chosen
    labels for easier readability.
    Seperate choices for heating and renovation so that they can be displayed in
    their own lists. Only choices from heating_fields are heating choices, the rest of the
    fields contain renovation choices.
    """
    heating_fields = {"primary_heating", "secondary_heating", "biomass_source", "heat_pump_type"}

    heating_choices = []
    renovation_choices = []

    renovation_form_classes = [
        forms.RenovationRequestForm,
        forms.RenovationHeatPumpForm,
        forms.RenovationBioMassForm,
        forms.RenovationPVSolarForm,
        forms.RenovationSolarForm,
        forms.RenovationTechnologyForm,
    ]
    renovation_forms = [form_class() for form_class in renovation_form_classes]

    for form in renovation_forms:
        category = "renovation"
        for field_name, field in form.fields.items():
            if field_name.endswith("hidden"):
                continue
            if field_name in heating_fields:
                category = "heating"

            if scenario_data.get(field_name):
                value = scenario_data[field_name]
                if isinstance(value, list):  # Multiple-choice fields
                    labels = [dict(field.choices).get(v) for v in value if v in dict(field.choices)]
                elif isinstance(value, bool):
                    labels = [field.label]
                else:  # Select-fields / Radiobuttons
                    labels = [dict(field.choices).get(value)] if value in dict(field.choices) else []

                if category == "heating":
                    heating_choices.extend(labels)
                else:
                    renovation_choices.extend(labels)
    # remove duplicates
    heating_choices = list(dict.fromkeys(heating_choices))
    renovation_choices = list(dict.fromkeys(renovation_choices))
    return heating_choices, renovation_choices


class RenovationOverview(SidebarNavigationMixin, TemplateView):
    template_name = "pages/renovation_overview.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["back_url"] = "heat:renovation_request"
        context["next_url"] = "heat:financial_support"
        context["scenario_boxes"] = get_all_scenario_data(self.request)
        context["max_reached"] = int(get_new_scenario(self.request)[8:]) > SCENARIO_MAX
        return context


def all_flows_finished(request):
    """
    Checks all Flows if they are finished. Either returns a all_flows_finished = True flag or Flase
    and a list with the Flows that need more input.
    """
    all_flows = [
        (name, flow())
        for name, flow in inspect.getmembers(flows, inspect.isclass)
        if name.endswith("Flow") and name not in {"Flow", "ConsumptionInputFlow", "RenovationRequestFlow"}
    ]

    # since there is no minimum for how many renovation scenarios are needed I omited testing that
    not_finished = [name for name, flow in all_flows if not flow.finished(request)]
    next_disabled, needed_for_consumption = check_if_new_year_possible(request, get_all_year_data(request))
    if next_disabled:
        not_finished.append("ConsumptionInputFlow")
    return (True, []) if not not_finished else (False, not_finished)


class OptimizationStart(SidebarNavigationMixin, TemplateView):
    template_name = "pages/optimization_start.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["back_url"] = "heat:financial_support"
        context["next_url"] = "heat:results"
        all_finished, not_finished = all_flows_finished(self.request)
        context["all_flows_finished"] = all_finished
        context["not_finished_flows"] = not_finished
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
        "back_url": "heat:financial_support",
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
        return context


class NextSteps(SidebarNavigationMixin, TemplateView):
    extra_context = {
        "back_url": "heat:results",
    }
