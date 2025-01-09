from math import isclose

import pandas as pd


def format_currency(value):
    """Format a number as currency (Euro)."""
    if value is None:
        return ""
    if isinstance(value, (int, float)):
        if isclose(value, round(value)):
            return f"{int(value):,}".replace(",", ".") + " €"
        return f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + " €"
    return str(value)


class Table:
    """Base class for generating and formatting tables."""

    translations = {
        "scenario1": "Szenario 1",
        "scenario2": "Szenario 2",
        "scenario3": "Szenario 3",
    }

    def __init__(self, data):
        self.data = data

    def translate_column(self, column_name):
        return self.translations.get(column_name, column_name)

    def to_html(self, dataframe, title):
        html_table = dataframe.to_html(classes="table", escape=False, index=False)
        html_table = html_table.replace('<table border="1" class="dataframe table">', f'<table class="{title}">')

        for header, translated in self.translations.items():
            html_table = html_table.replace(
                f"<th>{translated}</th>",
                f'<th class="{header}"><span>{translated}</span></th>',
            )
        return html_table


class ConsumptionTable(Table):
    """Specialized table for displaying consumption-related data."""

    translations = {
        **Table.translations,
        "change_heating": "Heiztechnologie wechseln",
        "renovate_facade": "Fassade sanieren",
        "renovate_roof": "Dach sanieren",
        "replace_windows": "Fenster austauschen",
        "insulate_basement_ceiling": "Kellerdecke dämmen",
        "procedure": "Maßnahme",
    }

    procedures = [
        "change_heating",
        "renovate_facade",
        "renovate_roof",
        "replace_windows",
        "insulate_basement_ceiling",
    ]

    def generate_table_data(self):
        table_data = {
            self.translate_column("procedure"): [self.translations.get(proc, proc) for proc in self.procedures],
        }
        for scenario, scenario_data in self.data.items():
            table_data[self.translate_column(scenario)] = [
                scenario_data.get(proc, "nicht ausgewählt") for proc in self.procedures
            ]
        return pd.DataFrame(table_data)

    def to_html(self, title="consumption_table"):
        dataframe = self.generate_table_data()
        html_table = super().to_html(dataframe, title)
        return html_table.replace(
            "<td>nicht ausgewählt</td>",
            '<td class="no-entry">nicht ausgewählt</td>',
        )


class InvestmentTable(Table):
    translations = {
        **Table.translations,
        "investment_overview": "Finanzierungsübersicht",
    }

    def generate_table_data(self):
        table_data = {
            self.translate_column("investment_overview"): [
                "Investitionskosten",
                "Summe Zuschüsse <br> (ohne Rückzahlung)",
            ],
        }
        for scenario, scenario_data in self.data.items():
            table_data[self.translate_column(scenario)] = [
                scenario_data.get("investment", 0),
                scenario_data.get("contribution", 0),
            ]

        dataframe = pd.DataFrame(table_data)
        sum_row = [self.translate_column("Summe"), *dataframe.iloc[:, 1:].sum().tolist()]
        dataframe.loc[len(dataframe)] = sum_row
        for col in dataframe.columns[1:]:
            dataframe[col] = dataframe[col].apply(format_currency)
        return dataframe

    def to_html(self, title="investment_table"):
        dataframe = self.generate_table_data()
        return super().to_html(dataframe, title)


class TabularTable(Table):
    translations = {
        **Table.translations,
        "air_heat_pump": "Luft-Wärmepumpe",
        "thermal_storage": "Wärmespeicher",
        "heat_meter": "Wärmemengenzähler",
        "heating_system_pump": "Pumpe des Heizsystems",
        "ventilation_system": "Lüftungsanlage",
        "insulate_outer_facade": "Außenfassade dämmen",
        "insulate_roof": "Dach dämmen",
    }

    def generate_table_data(self, scenario_data):
        investments = scenario_data.get("investments", {})
        subsidies = scenario_data.get("subsidies", {})

        dataframe_investments = pd.DataFrame(
            {
                "Investitionskosten": [self.translations.get(k, k) for k in investments],
                "": [format_currency(v) for v in investments.values()],
            },
        )

        dataframe_subsidies = pd.DataFrame(
            {
                "Zuschüsse": list(subsidies),
                "": [format_currency(v) for v in subsidies.values()],
            },
        )

        total_cost = sum(investments.values()) - sum(subsidies.values())
        dataframe_sum = pd.DataFrame(
            {
                "Summe": [""],
                "": [format_currency(total_cost)],
            },
        )

        return dataframe_investments, dataframe_subsidies, dataframe_sum

    def generate_html_table(self, scenario_data, scenario_class, title="summary_table"):
        dataframe_investments, dataframe_subsidies, dataframe_sum = self.generate_table_data(scenario_data)

        def format_html(dataframe, css_class):
            html = dataframe.to_html(classes=f"table {css_class}", index=False, escape=False)
            return html.replace(
                '<table border="1" class="dataframe table">',
                f'<table class="table {css_class} {title}">',
            )

        return (
            format_html(dataframe_investments, scenario_class)
            + format_html(dataframe_subsidies, scenario_class)
            + format_html(dataframe_sum, scenario_class)
        )
