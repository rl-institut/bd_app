import heat.settings as heat_settings


class SidebarNavigationMixin:
    def get_context_data(self, **kwargs):
        from . import flows

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
                if step["name"] == "Sanierungsübersicht":
                    if step["object"][0] == type(self) or step["object"][1] == type(self):
                        step["index_state"] = "active"
                        active_step_found = True
                    else:
                        step["index_state"] = self.get_renovation_index_state()
                elif step["object"] == type(self):
                    step["index_state"] = "active"
                    active_step_found = True
                elif issubclass(step["object"], flows.Flow):
                    step["index_state"] = self.get_flow_index_state(step)
                elif not active_step_found:
                    step["index_state"] = "visited"

        context["index"] = index
        return context

    def get_renovation_index_state(self):
        """Checks if at least one scenario of RenovationRequestFlow is complete."""
        from . import flows

        scenario_max = heat_settings.SCENARIO_MAX
        scenario_id = 1
        while scenario_id <= scenario_max:
            flow = flows.RenovationRequestFlow(prefix=f"scenario{scenario_id}")
            if flow.finished(self.request):
                return "complete"
            scenario_id += 1
        return "incomplete"

    def get_flow_index_state(self, step):
        """Checks for the calling flow if it is complete or not."""
        flow = step["object"]()
        if flow.finished(self.request):
            return "complete"
        return "incomplete"

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
                    {"name": "Dämmmaßnahmen", "object": flows.InsulationFlow, "url": "heat:insulation"},
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
                ],
            },
            {
                "category": "3. Optimierung starten",
                "object": views.OptimizationStart,
                "url": "heat:optimization_start",
                "steps": [],
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
