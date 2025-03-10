class SidebarNavigationMixin:
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        index = self.get_flows()
        active_step_found = False

        for category in index:
            if category["object"] == type(self):
                category["index_state"] = "active"
                active_step_found = True
            elif not active_step_found:
                category["index_state"] = "visited"
            else:
                category["index_state"] = ""

            for step in category["steps"]:
                if (
                    isinstance(step["object"], list)
                    and any(isinstance(self, obj) for obj in step["object"])
                    or step["object"] == type(self)
                ):
                    step["index_state"] = "active"
                    active_step_found = True
                elif not active_step_found:
                    step["index_state"] = "visited"
                else:
                    step["index_state"] = ""

        context["index"] = index
        return context

    def get_flows(self):
        from . import flows
        from . import views

        return [
            {
                "category": "1. Bestandsanalyse",
                "object": views.IntroInventory,
                "url": "heat:intro_inventory",
                "steps": [
                    {"name": "Gebäudeart", "object": flows.BuildingTypeFlow, "url": "heat:building_type"},
                    {"name": "Angaben zu Gebäude", "object": flows.BuildingDataFlow, "url": "heat:building_data"},
                    {"name": "Dämmungsmaßnahmen", "object": flows.InsulationFlow, "url": "heat:insulation"},
                    {
                        "name": "Heizung & Warmwasser",
                        "object": flows.HotwaterHeatingFlow,
                        "url": "heat:hotwater_heating",
                    },
                    {"name": "Dach", "object": flows.RoofFlow, "url": "heat:roof"},
                    {"name": "Heizung", "object": flows.HeatingFlow, "url": "heat:heating"},
                    {"name": "PV-Anlage", "object": flows.PVSystemFlow, "url": "heat:pv_system"},
                ],
            },
            {
                "category": "2. Sanierung",
                "object": views.IntroRenovation,
                "url": "heat:intro_renovation",
                "steps": [
                    {
                        "name": "Sanierungsübersicht",
                        "object": [views.RenovationOverview, flows.RenovationRequestFlow],
                        "url": "heat:renovation_overview",
                    },
                    {"name": "Förderung", "object": flows.FinancialSupportFlow, "url": "heat:financial_support"},
                    {
                        "name": "Optimierung starten",
                        "object": views.OptimizationStart,
                        "url": "heat:optimization_start",
                    },
                ],
            },
            {
                "category": "3. Ergebnisse",
                "object": views.Results,
                "url": "heat:results",
                "steps": [
                    {"name": "Nächste Schritte", "object": views.NextSteps, "url": "heat:next_steps"},
                ],
            },
        ]
