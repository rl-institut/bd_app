import inspect
import pandas as pd
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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Daten für die Tabellen
        scenario1_investments = [20700, 2980, 260, 480, 9620, 36890]
        scenario1_subsidies = [23158.07]
        scenario2_investments = [28700, 1980, 260, 410, 9620, 38980, 36890]
        scenario2_subsidies = [23158.07, 1931.93]

        # Tabellenstruktur erstellen
        def create_table(title, dynamic_column, values):
            values = [f"{value:,.2f} €" if isinstance(value, (int, float)) else value for value in values]
            return pd.DataFrame({
                title: dynamic_column,
                "": values
            })

        # Dynamische Spalten
        scenario1_dynamic_column_investments = ["Luft-Wärmepumpe", "Wärmespeicher", "Wärmemengenzähler", "Pumpe des Heizsystems", "Lüftungsanlage", "Außenfassade dämmen"]
        scenario1_dynamic_column_subsidies = ["KfW - Bundesförderung für effiziente Gebäude - Heizungsförderung für Privatpersonen - Wohnungsgebäude (BEG EM) (Nr. 458) (Zuschuss inkl. Klima-Bonus)"]

        scenario2_dynamic_column_investments = ["Luft-Wärmepumpe", "Wärmespeicher", "Wärmemengenzähler", "Pumpe des Heizsystems", "Lüftungsanlage", "Dach dämmen", "Außenfassade dämmen"]
        scenario2_dynamic_column_subsidies = ["KfW - Bundesförderung für effiziente Gebäude - Heizungsförderung für Privatpersonen - Wohnungsgebäude (BEG EM) (Nr. 458) (Zuschuss inkl. Klima-Bonus)", "KfW - Bundesförderung für effiziente Gebäude - Heizungsförderung für Privatpersonen - Wohnungsgebäude (BEG EM) (Nr. 458) (Effizienz-Bonus)"]

        # Tabellen für Szenario 1
        df_scenario1_investments = create_table("Investitionskosten", scenario1_dynamic_column_investments, scenario1_investments)
        df_scenario1_subsidies = create_table("Zuschüsse", scenario1_dynamic_column_subsidies, scenario1_subsidies)
        df_scenario1_sum = pd.DataFrame({
            "Summe": [""],
            "": [f"{sum(scenario1_investments) - sum(scenario1_subsidies):,.2f} €"]
        })

        # Tabellen für Szenario 2
        df_scenario2_investments = create_table("Investitionskosten", scenario2_dynamic_column_investments, scenario2_investments)
        df_scenario2_subsidies = create_table("Zuschüsse", scenario2_dynamic_column_subsidies, scenario2_subsidies)
        df_scenario2_sum = pd.DataFrame({
            "Summe": [""],
            "": [f"{sum(scenario2_investments) - sum(scenario2_subsidies):,.2f} €"]
        })

        # HTML-Tabellen generieren
        def generate_html_table(investments, subsidies, sums, scenario_name):
            investments_html = investments.to_html(classes=f"table {scenario_name}", index=False, escape=False)
            subsidies_html = subsidies.to_html(classes=f"table {scenario_name}", index=False, escape=False)
            sums_html = sums.to_html(classes=f"table {scenario_name}", index=False, escape=False)

            return investments_html + subsidies_html + sums_html

        html_scenario1 = generate_html_table(df_scenario1_investments, df_scenario1_subsidies, df_scenario1_sum, "tab_scenario1")
        html_scenario2 = generate_html_table(df_scenario2_investments, df_scenario2_subsidies, df_scenario2_sum, "tab_scenario2")

        # Tab-Steuerelemente
        tabs_html = """<div class='tabs'>
            <button class='tab-button' style="background-color: #1b9e77;" onclick="showTab('tab_scenario1', '#1b9e77')">Szenario 1</button>
            <button class='tab-button' style="background-color: #7570b3;" onclick="showTab('tab_scenario2', '#7570b3')">Szenario 2</button>
        </div>"""

        # Zusammenfügen
        full_html = f"""<style>
            .tabs {{ margin-bottom: 0; position: relative; top: 0; left: 0; }}
            .tab-button {{ margin-right: 5px; padding: 10px; color: white; border: none; cursor: pointer; }}
            .tab-button:hover {{ opacity: 0.9; }}
            .table {{ display: none; width: 100%; margin: 0; border-collapse: collapse; }}
            .table th, .table td {{ border: 1px solid lightgrey; padding: 10px; text-align: left; }}
            .table th {{ width: 70%; border-right: none; border-left: none; background-color: #f9f9f9; }}
            .tab_scenario1 {{ display: table; border: 10px solid #1b9e77; border-radius: 10px; }}
            .tab_scenario2 {{ border: 10px solid #7570b3; border-radius: 10px; }}
        </style>
        <script>
            function showTab(tabName, borderColor) {{
                var tables = document.querySelectorAll('.table');
                tables.forEach(function(table) {{
                    table.style.display = 'none';
                    table.style.border = '10px solid ' + borderColor;
                    table.style.borderRadius = '10px';
                }});
                document.querySelectorAll('.' + tabName).forEach(function(table) {{
                    table.style.display = 'table';
                }});
            }}
        </script>
        {tabs_html}
        {html_scenario1}
        {html_scenario2}
        """

        tabledata = {
            'Maßnahme': ['Heiztechnologie wechseln', 'Fassade sanieren', 'Dach sanieren', 'Fenster austauschen',
                         'Kellerdecke dämmen'],
            'Szenario 1': [-50, -50, 'nicht ausgewählt', 'nicht ausgewählt', 'nicht ausgewählt'],
            'Szenario 2': [-88, -50, -45, 'nicht ausgewählt', 'nicht ausgewählt']
        }
        df = pd.DataFrame(tabledata)

        # Generierte zweite Tabelle
        #measures_table = style_table(df)

        # Kontext hinzufügen
        #context['measures_table'] = measures_table
        # Kontext hinzufügen
        context['html_content'] = full_html
        context['hectare_scenario1'] = 2.2
        context['hectare_scenario2'] = 1.3
        return context

class NextSteps(SidebarNavigationMixin, TemplateView):
    template_name = "pages/next_steps.html"
    extra_context = {
        "back_url": "heat:results",
    }


def style_table(df):
    styles = [
        '<style> .table { border: 1px solid grey; border-radius: 12px; border-collapse: collapse; width: 100%; } </style>',
        '<style> th { background-color: #DCDCDC; padding: 10px; text-align: center; } </style>',
        '<style> th.procedure { font-weight: bold; } </style>',
        '<style> th.scenario1 { background-color: #DCDCDC; color: white; padding: 10px; } </style>',
        '<style> th.scenario2 { background-color: #DCDCDC; color: white; padding: 10px; } </style>',
        '<style> th.scenario1 span { background-color: #1b9e77; padding: 5px 15px; border-radius: 5px; } </style>',
        '<style> th.scenario2 span { background-color: #7570b3; padding: 5px 15px; border-radius: 5px; } </style>',
        '<style> td.no-entry { color: #A9A9A9; } </style>',
        '<style> th, td { border: 1px solid grey; padding: 10px; text-align: center; } </style>',
    ]

    html_table = df.to_html(classes='table', escape=False, index=False)
    html_table = ''.join(styles) + html_table
    html_table = html_table.replace('<th>', '<th class="procedure">', 1)
    html_table = html_table.replace('<th>Szenario 1</th>', '<th class="scenario1"><span>Szenario 1</span></th>')
    html_table = html_table.replace('<th>Szenario 2</th>', '<th class="scenario2"><span>Szenario 2</span></th>')
    html_table = html_table.replace('<td>nicht ausgewählt</td>', '<td class="no-entry">nicht ausgewählt</td>')
    html_table = html_table.replace('<table ', '<table style="border-radius: 12px;" ')
    return html_table
