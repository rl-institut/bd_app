from math import isclose
from typing import Any

import pandas as pd


def format_currency(value: Any) -> str:
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

    def translate_column(self, column_name: str) -> str:
        return self.translations.get(column_name, column_name)

    def generate_table_data(self) -> pd.DataFrame:
        return pd.DataFrame(self.data)

    def to_html(self, title: str) -> str:
        dataframe = self.generate_table_data()
        html = dataframe.to_html(classes="table", escape=False, index=False)

        for header in dataframe.columns:
            translated = next((k for k, v in self.translations.items() if v == header), None)
            if translated is not None:
                html = html.replace(
                    f"<th>{header}</th>",
                    f'<th class="{translated}"><span>{header}</span></th>',
                )

        return html.replace('<table border="1" class="dataframe table">', f'<table class="{title} table">')


class ConsumptionTable(Table):
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

    def generate_table_data(self) -> pd.DataFrame:
        table_data = {
            self.translate_column("procedure"): [self.translations.get(proc, proc) for proc in self.procedures],
        }
        for scenario, scenario_data in self.data.items():
            table_data[self.translate_column(scenario)] = [
                scenario_data.get(proc, "nicht ausgewählt") for proc in self.procedures
            ]
        return pd.DataFrame(table_data)

    def to_html(self, title: str = "consumption_table") -> str:
        html_table = super().to_html(title)
        return html_table.replace(
            "<td>nicht ausgewählt</td>",
            '<td class="no-entry">nicht ausgewählt</td>',
        )


class SumTable(Table):
    @staticmethod
    def generate_sum_row(dataframe: pd.DataFrame) -> pd.DataFrame:
        if not dataframe.empty and dataframe.shape[1] > 1:
            sum_row = ["Summe"]
            for col in dataframe.columns[1:]:
                numeric_series = pd.to_numeric(dataframe[col], errors="coerce")
                col_sum = numeric_series.sum(skipna=True)
                sum_row.append(col_sum)

            dataframe.loc[len(dataframe)] = sum_row

            for col in dataframe.columns[1:]:
                dataframe[col] = dataframe[col].apply(format_currency)

        return dataframe

    def generate_table_data(self):
        dataframe = super().generate_table_data()
        return self.generate_sum_row(dataframe)

    def to_html(self, title: str = "sum_table"):
        return super().to_html(title)


class InvestmentSummaryTable(SumTable):
    translations = {
        **Table.translations,
        "investment_overview": "Finanzierungsübersicht",
    }

    def generate_table_data(self) -> pd.DataFrame:
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
        return self.generate_sum_row(pd.DataFrame(table_data))

    def to_html(self, title: str = "investment_table") -> str:
        return super().to_html(title)


class InvestmentTable(Table):
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

    def generate_table_data(self):
        investments = self.data.get("investments", {})

        return pd.DataFrame(
            {
                "Investitionskosten": [self.translations.get(k, k) for k in investments],
                "": [format_currency(v) for v in investments.values()],
            },
        )


class SubsidiesTable(Table):
    def generate_table_data(self):
        subsidies = self.data.get("subsidies", {})
        return pd.DataFrame(
            {
                "Zuschüsse": list(subsidies),
                "": [format_currency(v) for v in subsidies.values()],
            },
        )


class TotalCostTable(Table):
    def generate_table_data(self):
        investments = self.data.get("investments", {})
        subsidies = self.data.get("subsidies", {})
        total_cost = sum(investments.values()) - sum(subsidies.values())
        return pd.DataFrame(
            {
                "Summe": [""],
                "": [format_currency(total_cost)],
            },
        )
