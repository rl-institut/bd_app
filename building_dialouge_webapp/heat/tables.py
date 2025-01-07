import pandas as pd


class Table:
    translations = {
        "procedure": "Maßnahme",
        "scenario1": "Szenario 1",
        "scenario2": "Szenario 2",
        "scenario3": "Szenario 3",
        "change_heating": "Heiztechnologie wechseln",
        "renovate_facade": "Fassade sanieren",
        "renovate_roof": "Dach sanieren",
        "replace_windows": "Fenster austauschen",
        "insulate_basement_ceiling": "Kellerdecke dämmen",
    }

    procedures = [
        "change_heating",
        "renovate_facade",
        "renovate_roof",
        "replace_windows",
        "insulate_basement_ceiling",
    ]

    def __init__(self, data):
        self.data = data

    def translate_column(self, column_name):
        return self.translations.get(column_name, column_name)

    def generate_table_data(self):
        table_data = {
            "procedure": [self.translations[proc] for proc in self.procedures],
        }

        for scenario_key, scenario_data in self.data.items():
            table_data[self.translate_column(scenario_key)] = [
                scenario_data.get(proc, "nicht ausgewählt") for proc in self.procedures
            ]

        return pd.DataFrame(table_data)

    def to_html(self):
        dataframe = self.generate_table_data()

        html_table = dataframe.to_html(classes="table", escape=False, index=False)

        html_table = html_table.replace(
            '<table border="1" class="dataframe table">',
            '<table class="consumption_table">',
        )
        html_table = html_table.replace("<th>procedure</th>", '<th class="procedure">Maßnahme</th>')
        html_table = html_table.replace("<th>Szenario 1</th>", '<th class="scenario1">Szenario 1</th>')
        html_table = html_table.replace("<th>Szenario 2</th>", '<th class="scenario2">Szenario 2</th>')
        html_table = html_table.replace("<th>Szenario 3</th>", '<th class="scenario3">Szenario 3</th>')

        return html_table.replace("<td>nicht ausgewählt</td>", '<td class="no-entry">nicht ausgewählt</td>')
