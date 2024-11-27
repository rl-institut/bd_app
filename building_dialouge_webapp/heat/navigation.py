class SidebarNavigationMixin:
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        index = self.get_flows()
        current_url = self.request.path

        for category in index:
            for step in category["steps"]:
                flow_object = step["object"]

                if step["url"] == current_url:
                    step["index_state"] = "active"
                elif flow_object.finished(self):
                    step["index_state"] = "visited"
                else:
                    step["index_state"] = ""

            # Set category state based on step states
            if any(step["index_state"] == "active" for step in category["steps"]):
                category["index_state"] = "active"
            elif all(step["index_state"] == "visited" for step in category["steps"]):
                category["index_state"] = "visited"
            else:
                category["index_state"] = ""

        context["index"] = index
        return context

    def get_flows(self):
        from . import flows
        from . import views

        return [
            {
                "category": "1. Verbrauchsanalyse",
                "object": views.IntroConsumption,
                "url": "heat:intro_consumption",
                "steps": [
                    {"name": "Gebäudeart", "object": flows.BuildingTypeFlow, "url": "heat:building_type"},
                    {"name": "Angaben zu Gebäude", "object": flows.BuildingDataFlow, "url": "heat:building_data"},
                    {"name": "Keller", "object": flows.CellarFlow, "url": "heat:cellar"},
                    {
                        "name": "Heizung & Warmwasser",
                        "object": flows.HotwaterHeatingFlow,
                        "url": "heat:hotwater_heating",
                    },
                    {
                        "name": "Verbrauchseingabe",
                        "object": flows.ConsumptionInputFlow,
                        "url": "heat:consumption_input",
                    },
                    {
                        "name": "Verbrauchsergebnis",
                        "object": views.ConsumptionResult,
                        "url": "heat:consumption_result",
                    },
                ],
            },
            {
                "category": "2. Bestandsanalyse",
                "object": views.IntroInventory,
                "url": "heat:intro_inventory",
                "steps": [
                    {"name": "Dach", "object": flows.RoofFlow, "url": "heat:roof"},
                    {"name": "Fenster", "object": flows.WindowFlow, "url": "heat:window"},
                    {"name": "Fassade", "object": flows.FacadeFlow, "url": "heat:facade"},
                    {"name": "Heizung", "object": flows.HeatingFlow, "url": "heat:heating"},
                    {"name": "PV-Anlage", "object": flows.PVSystemFlow, "url": "heat:pv_system"},
                    {
                        "name": "Lüftungsanlage",
                        "object": flows.VentilationSystemFlow,
                        "url": "heat:ventilation_system",
                    },
                ],
            },
            {
                "category": "3. Sanierung",
                "object": views.IntroRenovation,
                "url": "heat:intro_renovation",
                "steps": [
                    {
                        "name": "Sanierungswunsch",
                        "object": flows.FinancialSupporFlow,
                        "url": "heat:financial_support",
                    },  # renovation
                    {"name": "Förderung", "object": flows.FinancialSupporFlow, "url": "heat:financial_support"},
                ],
            },
            {
                "category": "4. Ergebnisse",
                "object": views.Results,
                "url": "heat:results",
                "steps": [
                    {"name": "Nächste Schritte", "object": views.NextSteps, "url": "heat:next_steps"},
                ],
            },
        ]
