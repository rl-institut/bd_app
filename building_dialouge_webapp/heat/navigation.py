class SidebarNavigationMixin:
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        index = self.get_flows()
        state_found = False

        for step in index:
            index_state = ""
            if step["object"] == type(self):
                index_state = "active"
                state_found = True
            elif not state_found:
                index_state = "visited"

            step["index_state"] = index_state
            step["is_category"] = step["name"][0].isdigit()

        context["index"] = index
        return context

    def get_flows(self):
        from . import flows
        from . import views

        return [
            {"name": "1. Verbrauchsanalyse", "object": views.IntroConsumption, "url": "heat:intro_consumption"},
            {"name": "Gebäudeart", "object": flows.BuildingTypeFlow, "url": "heat:building_type"},
            {"name": "Angaben zu Gebäude", "object": flows.BuildingDataFlow, "url": "heat:building_data"},
            {"name": "Keller", "object": flows.CellarFlow, "url": "heat:cellar"},
            {"name": "Heizung & Warmwasser", "object": flows.HotwaterHeatingFlow, "url": "heat:hotwater_heating"},
            {"name": "Verbrauchseingabe", "object": flows.ConsumptionInputFlow, "url": "heat:consumption_input"},
            {"name": "Verbrauchsergebnis", "object": views.ConsumptionResult, "url": "heat:consumption_result"},
            {"name": "2. Bestandsanalyse", "object": views.IntroInventory, "url": "heat:intro_inventory"},
            {"name": "Dach", "object": flows.RoofFlow, "url": "heat:roof"},
            {"name": "Fenster", "object": flows.WindowFlow, "url": "heat:window"},
            {"name": "Fassade", "object": flows.FacadeFlow, "url": "heat:facade"},
            {"name": "Heizung", "object": flows.HeatingFlow, "url": "heat:heating"},
            {"name": "PV-Anlage", "object": flows.PVSystemFlow, "url": "heat:pv_system"},
            {"name": "Lüftungsanlage", "object": flows.VentilationSystemFlow, "url": "heat:ventilation_system"},
            {"name": "3. Sanierung", "object": views.IntroRenovation, "url": "heat:intro_renovation"},
            {
                "name": "Sanierungswunsch",
                "object": flows.FinancialSupporFlow,
                "url": "heat:financial_support",
            },  # renovation
            {"name": "Förderung", "object": flows.FinancialSupporFlow, "url": "heat:financial_support"},
            {"name": "4. Ergebnisse", "object": views.Results, "url": "heat:results"},
            {"name": "Nächste Schritte", "object": views.NextSteps, "url": "heat:next_steps"},
        ]
