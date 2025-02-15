import json
import re
from datetime import datetime
from datetime import timedelta
from datetime import timezone

from django import forms
from django.core.validators import MaxValueValidator
from django.core.validators import MinValueValidator
from django.forms import ValidationError


class ValidationForm(forms.Form):
    def __init__(self, *args, request=None, **kwargs):
        self.request = request
        super().__init__(*args, **kwargs)

        with open("building_dialouge_webapp/static/json/validation.json") as file:  # noqa: PTH123
            dynamic_rules = json.load(file)
            form_rules = dynamic_rules.get(self.__class__.__name__, {})
        if form_rules:
            for field_name, rules in form_rules.items():
                if field_name in self.fields:
                    field = self.fields[field_name]
                    for rule, value in rules.items():
                        setattr(field, rule, value)
                        if rule == "min_value":
                            field.widget.attrs["min"] = value
                            field.validators.append(MinValueValidator(value))
                        elif rule == "max_value":
                            field.widget.attrs["max"] = value
                            field.validators.append(MaxValueValidator(value))
        if self.request:
            self.validate_with_session()

    def validate_with_session(self):
        """
        Override this method in subclasses to add custom validations
        using data that was saved to the session (using request).
        this is how its saved:
            value = self.flow.request.POST[self.name]
            session_data = self.flow.request.session.get("django_htmx_flow", {})
        """


class BuildingTypeForm(ValidationForm):
    building_type = forms.ChoiceField(
        label="building_type",
        choices=[
            ("single_family", "Einfamlienhaus"),
            ("apartment_building", "Mehrfamilienhaus"),
        ],
        widget=forms.RadioSelect,
    )


class BuildingTypeProtectionForm(ValidationForm):
    monument_protection = forms.ChoiceField(
        label="monument_protection",
        choices=[("no", "Nein"), ("yes", "Ja")],
        widget=forms.RadioSelect,
    )


class BuildingDataForm(ValidationForm):
    construction_year = forms.IntegerField(
        label="construction_year",
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )
    number_persons = forms.IntegerField(
        label="number_persons",
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )
    number_flats = forms.IntegerField(
        label="number_flats",
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )
    living_space = forms.IntegerField(
        label="living_space",
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )
    number_floors = forms.IntegerField(
        label="number_floors",
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )
    adjoining_building = forms.ChoiceField(
        label="adjoining_building",
        choices=[
            ("no", "Nein / Freistehend"),
            ("1_side", "Eine Seite / Reihenendhaus"),
            ("2_side", "Zwei Seiten / Reihenmittelhaus"),
        ],
        widget=forms.RadioSelect,
    )
    floor_plan = forms.ChoiceField(
        label="floor_plan",
        choices=[
            ("compact", "Kompakt"),
            ("complex", "Langgestreckt, gewinkelt, komplex, angrenzend"),
        ],
        widget=forms.RadioSelect,
    )

    def validate_with_session(self):
        data = self.request.session.get("django_htmx_flow", {})

        min_max_defaults = {
            "single_family": {
                "number_persons": {"min": 1, "max": 10},
                "number_flats": {"min": 1, "max": 2},
                "living_space": {"min": 200, "max": 400},
                "number_floors": {"min": 1, "max": 3},
            },
            "apartment_building": {
                "number_persons": {"min": 2, "max": 100},
                "number_flats": {"min": 2, "max": 20},
                "living_space": {"min": 400, "max": 1000},
                "number_floors": {"min": 1, "max": 10},
            },
        }

        field_rules = min_max_defaults.get(data["building_type"])
        for field_name, rules in field_rules.items():
            if field_name in self.fields:
                self.fields[field_name].widget.attrs.update(
                    {"min": rules["min"], "max": rules["max"]},
                )
                self.fields[field_name].validators.append(MinValueValidator(rules["min"]))
                self.fields[field_name].validators.append(MaxValueValidator(rules["max"]))


class CellarHeatingForm(ValidationForm):
    cellar_heating = forms.ChoiceField(
        label="cellar_heating",
        choices=[
            ("no_cellar", "Kein Keller"),
            ("without_heating", "Keller unbeheizt"),
            ("with_heating", "Keller beheizt"),
        ],
        widget=forms.RadioSelect,
    )


class CellarDetailsForm(ValidationForm):
    cellar_ceiling = forms.ChoiceField(
        label="cellar_ceiling",
        choices=[
            ("solid", "Massiv"),
            ("other", "Andere (Holz)"),
        ],
        widget=forms.RadioSelect,
    )
    cellar_vault = forms.ChoiceField(
        label="cellar_vault",
        choices=[(True, "Ja"), (False, "Nein")],
        widget=forms.RadioSelect,
    )
    cellar_height = forms.FloatField(
        label="cellar_height",
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )


class CellarInsulationForm(ValidationForm):
    cellar_ceiling_insulation_exists = forms.ChoiceField(
        label="cellar_ceiling_insulation_exists",
        choices=[(True, "Ja"), ("doesnt_exist", "Nein")],
        widget=forms.RadioSelect,
    )


class CellarInsulationYearForm(ValidationForm):
    cellar_insulation_year = forms.IntegerField(
        label="cellar_insulation_year",
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )


class HeatingSystemForm(ValidationForm):
    heating_system = forms.ChoiceField(
        label="Heizungsart",
        choices=[
            ("central_heating", "Zentralheizung"),
            ("level_heating", "Etagenheizung"),
            ("night_storage", "Nachtspeicherheizung"),
        ],
        widget=forms.RadioSelect,
    )


class HeatingSourceForm(ValidationForm):
    energy_source = forms.ChoiceField(
        label="Technologie / Energieträger",
        choices=[
            ("gas", "Erdgas"),
            ("oil", "Heizöl"),
            ("district_heating", "Fernwärme"),
            ("liquid_gas", "Flüssiggas"),
            ("wood_pellets", "Holzpellets"),
            ("geothermal_pump", "Erdwärmepumpe"),
            ("air_heat_pump", "Luftwärmepumpe"),
            ("groundwater", "Grundwasser-/Solewärmepumpe"),
            ("heating_rod", "Heizstab"),
        ],
        widget=forms.RadioSelect,
    )


class HotwaterHeatingSystemForm(ValidationForm):
    hotwater_heating_system = forms.ChoiceField(
        label="Warmwasserbereitung erfolgt in ",
        choices=[
            ("heater", "Heizanlage"),
            ("boiler", "Boiler / Durchlauferhitzer"),
        ],
        widget=forms.RadioSelect,
    )


class HotwaterHeatingMeasuredForm(ValidationForm):
    hotwater_measured = forms.ChoiceField(
        label="Wird der WW Verbrauch separat gemessen?",
        choices=[(True, "Ja"), (False, "Nein")],
        widget=forms.RadioSelect,
    )


class HotwaterHeatingSolarExistsForm(ValidationForm):
    solar_thermal_exists = forms.ChoiceField(
        label="Solarthermieanlage vorhanden?",
        choices=[
            ("only_hotwater", "Ja, für Warmwasser"),
            ("both", "Ja, für WW und Heizung"),
            ("doesnt_exist", "Nein"),
        ],
        widget=forms.RadioSelect,
    )


class HotwaterHeatingSolarKnownForm(ValidationForm):
    solar_thermal_energy_known = forms.ChoiceField(
        label="Heizenergie bekannt?",
        choices=[("known", "Ja"), ("unknown", "Unbekannt")],
        widget=forms.RadioSelect,
    )


class HotwaterHeatingSolarEnergyForm(ValidationForm):
    solar_thermal_energy = forms.IntegerField(
        label="Heizenergie",
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )


class HotwaterHeatingSolarDetailsForm(ValidationForm):
    solar_thermal_area = forms.FloatField(
        label="Kollektorfläche in m²",
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )
    roof_inclination = forms.IntegerField(
        label="Dachneigung",
        widget=forms.NumberInput(attrs={"class": "form-control"}),
        min_value=0,
        max_value=360,
    )
    roof_orientation = forms.ChoiceField(
        label="Ausrichtung",
        choices=[
            ("n", "N"),
            ("ne", "NO"),
            ("e", "O"),
            ("se", "SO"),
            ("s", "S"),
            ("sw", "SW"),
            ("w", "W"),
            ("nw", "NW"),
        ],
        widget=forms.RadioSelect,
    )


class ConsumptionTypeForm(ValidationForm):
    consumption_type = forms.ChoiceField(
        label="Welche Art von Verbrauchseingabe?",
        choices=[
            ("heating", "Wärmeverbrauch"),
            ("power", "Stromverbrauch"),
        ],
        widget=forms.RadioSelect,
    )

    def validate_with_session(self):
        data = self.request.session.get("django_htmx_flow", {})
        # Count occurrences of "heating" and "power" as consumption_type in session
        pattern = re.compile(r"^year[1-6]-consumption_type$")
        relevant_data = {k: v for k, v in data.items() if pattern.match(k)}

        heating_count = sum(1 for v in relevant_data.values() if v == "heating")
        power_count = sum(1 for v in relevant_data.values() if v == "power")
        count_max = 3
        # Determine initial value and whether to disable the field
        if heating_count >= count_max:
            self.fields["consumption_type"].initial = "power"
            self.fields["consumption_type"].widget.attrs["disabled"] = True
        elif power_count >= count_max:
            self.fields["consumption_type"].initial = "heating"
            self.fields["consumption_type"].widget.attrs["disabled"] = True


class ConsumptionHeatingForm(ValidationForm):
    heating_consumption_period_start = forms.DateField(
        label="Zeitraum von:",
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    heating_consumption_period_end = forms.DateField(
        label="bis:",
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    heating_consumption = forms.IntegerField(
        label="Heizenergieverbrauch",
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )
    heating_consumption_unit = forms.ChoiceField(
        label="Einheit",
        choices=[
            ("kwh", "Kilowattstunden / kWh"),
            ("l", "Liter / l"),
            ("cbm", "Kubikmeter / m³"),
            ("t", "Tonnen / t"),
        ],
        widget=forms.RadioSelect,
    )
    heating_energy_source_cost = forms.FloatField(
        label="Brennstoffkosten in €",
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )

    def clean_heating_consumption_period_start(self):
        date_value = self.cleaned_data["heating_consumption_period_start"]
        return date_value.isoformat()

    def clean_heating_consumption_period_end(self):
        date_value = self.cleaned_data["heating_consumption_period_end"]
        return date_value.isoformat()

    def clean(self):
        cleaned_data = super().clean()
        # check if end date is after start date
        start_str = cleaned_data.get("heating_consumption_period_start")
        end_str = cleaned_data.get("heating_consumption_period_end")
        if start_str and end_str:
            start = datetime.fromisoformat(start_str).date()
            end = datetime.fromisoformat(end_str).date()
            max_date = datetime(2023, 12, 31, tzinfo=timezone(timedelta(hours=1))).date()
            if start > max_date or end > max_date:
                raise ValidationError("Dates have to be on or before 31.12.2023.")  # noqa: TRY003, EM101
            if end <= start:
                raise ValidationError("End date must be after start date.")  # noqa: TRY003, EM101
            if (end - start) < timedelta(days=90):
                raise ValidationError("End date needs to be at least 90 days after start date.")  # noqa: TRY003, EM101

        # Validation for heating_consumption
        heating_consumption = cleaned_data.get("heating_consumption")
        heating_consumption_unit = cleaned_data.get("heating_consumption_unit")
        if heating_consumption and heating_consumption_unit:
            data = self.request.session.get("django_htmx_flow", {})
            energy_source = 0.9  # TODO: get numeral value from data["energy_source"]
            heating_consumption_unit = 1  # TODO: get numeral value from heating_consumption_unit
            living_space = data["living_space"]
            heating_consumption_kwh = heating_consumption * energy_source * heating_consumption_unit
            # TODO: might need "Extrapolation mit Gradtagszahlen"
            # TODO: "Witterungsbereinigung mit Gradtagszahlen"
            heating_consumption_spec = heating_consumption_kwh / living_space
            comparison_value = 500
            if heating_consumption_spec > comparison_value:
                raise ValidationError("Heating Consumption seems too high.")  # noqa: TRY003, EM101

    def validate_with_session(self):
        data = self.request.session.get("django_htmx_flow", {})

        # energy source unit depends on energy_source from HotwaterHeating
        energy_source_unit = {
            "gas": "cbm",
            "oil": "l",
            "district_heating": "kwh",
            "liquid_gas": "cbm",
            "wood_pellets": "t",
            "geothermal_pump": "kwh",
            "air_heat_pump": "kwh",
            "groundwater": "kwh",
            "heating_rod": "kwh",
        }

        unit = energy_source_unit.get(data["energy_source"])
        self.fields["heating_consumption_unit"].initial = unit


class ConsumptionHotwaterForm(ValidationForm):
    hotwater_consumption = forms.FloatField(
        label="Warmwasserverbrauch",
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )
    hotwater_consumption_unit = forms.ChoiceField(
        label="Einheit",
        choices=[
            ("kwh", "Kilowattstunden / kWh"),
            ("l", "Liter / l"),
            ("cbm", "Kubikmeter / m³"),
        ],
        widget=forms.RadioSelect,
    )

    def clean(self):
        cleaned_data = super().clean()
        consumption = cleaned_data.get("hotwater_consumption")
        unit = cleaned_data.get("hotwater_consumption_unit")
        if unit and consumption:
            if unit != "kwh":
                consumption = consumption  # noqa: PLW0127 TODO: hotwater_consumption needs to be converted to kwh

            data = self.request.session.get("django_htmx_flow", {})
            living_space = data["living_space"]
            heating_consumption_spec = 40  # TODO: needs to be added to session, data["heating_consumption_spec"]

            hotwater_consumption_spec = consumption / living_space
            if hotwater_consumption_spec > heating_consumption_spec * 0.3:
                raise ValidationError("Hotwater Consumption seems too high.")  # noqa: TRY003, EM101
            if hotwater_consumption_spec < heating_consumption_spec * 0.1:
                raise ValidationError("Hotwater Consumption seems too low.")  # noqa: TRY003, EM101
        return cleaned_data


class ConsumptionWatertemperaturForm(ValidationForm):
    hotwater_temperature = forms.IntegerField(
        label="Warmwassertemperatur in °C",
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )


class ConsumptionPowerForm(forms.Form):
    power_consumption_period_start = forms.DateField(
        label="Zeitraum von:",
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    power_consumption_period_end = forms.DateField(
        label="bis:",
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    power_consumption = forms.IntegerField(
        label="Stromverbrauch",
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )
    power_cost = forms.FloatField(
        label="Stromkosten in €",
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )

    def clean_power_consumption_period_start(self):
        date_value = self.cleaned_data["power_consumption_period_start"]
        return date_value.isoformat()

    def clean_power_consumption_period_end(self):
        date_value = self.cleaned_data["power_consumption_period_end"]
        return date_value.isoformat()

    def clean(self):
        cleaned_data = super().clean()
        start_str = cleaned_data.get("power_consumption_period_start")
        end_str = cleaned_data.get("power_consumption_period_end")
        if start_str and end_str:
            start = datetime.fromisoformat(start_str).date()
            end = datetime.fromisoformat(end_str).date()
            max_date = datetime(2023, 12, 31, tzinfo=timezone(timedelta(hours=1))).date()
            if start > max_date or end > max_date:
                raise ValidationError("Dates have to be on or before 31.12.2023.")  # noqa: TRY003, EM101
            if end <= start:
                raise ValidationError("End date must be after start date.")  # noqa: TRY003, EM101
            if (end - start) < timedelta(days=90):
                raise ValidationError("End date needs to be at least 90 days after start date.")  # noqa: TRY003, EM101

    def validate_with_session(self):
        # TODO: there might be subtractions from power_consumption depending
        # on the energy source and hotwater_heating_system
        data = self.request.session.get("django_htmx_flow", {})
        energy_source = data["energy_source"]  # noqa: F841
        hotwater_heating_system = data["hotwater_heating_system"]  # noqa: F841


class RoofTypeForm(forms.Form):
    roof_type = forms.ChoiceField(
        label="roof_type",
        choices=[
            ("flachdach", "Flachdach"),
            ("satteldach", "Satteldach"),
            ("walmdach", "Walmdach"),
            ("other", "Andere Dachform"),
        ],
        widget=forms.RadioSelect,
    )


class RoofAreaForm(ValidationForm):
    roof_area = forms.IntegerField(
        label="Dachfläche in m² (gesamt)",
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )


class RoofOrientationForm(ValidationForm):
    roof_orientation = forms.ChoiceField(
        label="In welcher Richtung ist ihr Dach ausgerichtet?",
        choices=[
            ("n", "N"),
            ("ne", "NO"),
            ("e", "O"),
            ("se", "SO"),
            ("s", "S"),
            ("sw", "SW"),
            ("w", "W"),
            ("nw", "NW"),
        ],
        widget=forms.RadioSelect,
    )


class RoofWindowsForm(ValidationForm):
    number_roof_windows = forms.IntegerField(
        label="Anzahl der Dachfenster oder Dachgauben",
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )


class RoofUsageNowForm(ValidationForm):
    roof_usage_now = forms.ChoiceField(
        label="roof_usage_now",
        choices=[
            ("all_used", "Vollständig genutzt/beheizt"),
            ("part_used", "Teilweise genutzt/beheizt"),
            ("not_used", "Nicht genutzt/beheizt"),
        ],
        widget=forms.RadioSelect,
    )


class RoofUsageFutureForm(ValidationForm):
    roof_usage_planned = forms.ChoiceField(
        label="roof_usage_planned",
        choices=[
            ("all_used", "Keine Nutzung/Beheizung"),
            ("part_used", "Ausbauen und Nutzen"),
        ],
        widget=forms.RadioSelect,
    )
    roof_usage_share = forms.IntegerField(
        label="roof_usage_share in %",
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )


class RoofInsulationForm(ValidationForm):
    roof_insulation_exists = forms.ChoiceField(
        label="roof_insulation_exists",
        choices=[("yes", "Ja"), ("no", "Nein"), ("unknown", "Unbekannt")],
        widget=forms.RadioSelect,
    )


class RoofInsulationYearForm(forms.Form):
    roof_insulation_year = forms.IntegerField(
        label="Jahr",
        widget=forms.NumberInput(attrs={"class": "form-control"}),
        required=False,
    )


class WindowAreaForm(ValidationForm):
    window_area = forms.ChoiceField(
        label="Umfang Fensterflächen",
        choices=[
            ("small", "Niedrig (wenige Fensterflächen)"),
            ("medium", "Mittel (durchschnittlich viele Fensterflächen)"),
            ("large", "Hoch (viele Fensterfächen)"),
        ],
        widget=forms.RadioSelect,
    )


class WindowDetailsForm(ValidationForm):
    window_type = forms.ChoiceField(
        label="Fenstertyp",
        choices=[
            ("single_glazed", "Einfachverglast"),
            ("double_glazed", "Zweifachverglast (Verbund- und Kastenfenster, luftisoliert)"),
            ("double_heat_glazed", "Zweifach-Wärmeschutzverglasung"),
            ("triple_glazed", "Dreifach-Wärmeschutzverglasung"),
        ],
        widget=forms.RadioSelect,
    )
    window_construction_year = forms.ChoiceField(
        label="Jahr des Einbaus",
        choices=[
            ("unkown", "Unbekannt"),
            ("like_building", "wie Gebäude"),
            ("year", "Jahr: "),
        ],
        widget=forms.RadioSelect,
    )
    seperate_year = forms.IntegerField(
        label="",
        widget=forms.NumberInput(attrs={"class": "form-control"}),
        required=False,
    )
    window_share = forms.IntegerField(
        label="prozentualer Anteil (bei mehreren Typen)",
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )

    def clean(self):
        cleaned_data = super().clean()
        choice = cleaned_data.get("window_construction_year")
        year = cleaned_data.get("seperate_year")

        if choice == "year" and not year:
            self.add_error("seperate_year", "Bitte ein Jahr angeben.")

        return cleaned_data


class FacadeForm(ValidationForm):
    facade_type = forms.ChoiceField(
        label="Bauweise",
        choices=[
            ("wood", "Holz"),
            ("solid", "Massiv"),
        ],
        widget=forms.RadioSelect,
    )
    facade_condition = forms.ChoiceField(
        label="Zustand",
        choices=[
            ("no_damage", "Keine Schäden"),
            ("needs_paintjob", "Neuer Anstrich erforderlich"),
            ("small_cracks", "Kleine Risse / bröckelnder Putz: "),
        ],
        widget=forms.RadioSelect,
    )


class FacadeInsulationForm(ValidationForm):
    facade_insulation_exists = forms.ChoiceField(
        label="Dämmung vorhanden?",
        choices=[("exists", "Ja"), ("doesnt_exist", "Nein"), ("unkown", "Unbekannt")],
        widget=forms.RadioSelect,
    )


class FacadeInsulationYearForm(ValidationForm):
    facade_construction_year = forms.IntegerField(
        label="Jahr",
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )


class HeatingForm(ValidationForm):
    heating_system_construction_year = forms.IntegerField(
        label="Baujahr Heizung",
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )
    condensing_boiler_exists = forms.ChoiceField(
        label="Brennwerttechnik vorhanden?",
        choices=[(True, "Ja"), (False, "Nein"), ("unkown", "Unbekannt")],
        widget=forms.RadioSelect,
    )


class HeatingHydraulicForm(ValidationForm):
    hydraulic_balancing_done = forms.ChoiceField(
        label="Hydraulischer Abgleich durchgeführt?",
        choices=[(True, "Ja"), (False, "Nein"), ("unkown", "Unbekannt")],
        widget=forms.RadioSelect,
    )


class HeatingDetailsForm(ValidationForm):
    pipe_insulation_exists = forms.ChoiceField(
        label="Rohre gedämmt?",
        choices=[(True, "Ja"), (False, "Nein")],
        widget=forms.RadioSelect,
    )
    floor_heating_exists = forms.ChoiceField(
        label="Fußbodenheizung",
        choices=[(True, "Ja"), (False, "Nein")],
        widget=forms.RadioSelect,
    )
    heating_storage_exists = forms.ChoiceField(
        label="Wärmespeicher",
        choices=[(True, "Ja"), (False, "Nein")],
        widget=forms.RadioSelect,
    )


class HeatingStorageForm(ValidationForm):
    heating_storage_capacity = forms.IntegerField(
        label="Wärmespeicher Fassungsvermögen in l",
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )


class PVSystemForm(ValidationForm):
    pv_exists = forms.ChoiceField(
        label="PV-Anlage vorhanden?",
        choices=[(True, "Ja"), ("doesnt_exist", "Nein")],
        widget=forms.RadioSelect,
    )


class PVSystemPlannedForm(ValidationForm):
    pv_planned = forms.ChoiceField(
        label="Beabsichtigen Sie, eine zu installieren?",
        choices=[(True, "Ja"), (False, "Nein")],
        widget=forms.RadioSelect,
    )


class PVSystemDetailsForm(ValidationForm):
    pv_construction_year = forms.IntegerField(
        label="Baujahr",
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )
    pv_capacity = forms.IntegerField(
        label="Leistung in kWp",
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )


class PVSystemBatteryForm(ValidationForm):
    battery_exists = forms.ChoiceField(
        label="Batterie vorhanden?",
        choices=[(True, "Ja"), (False, "Nein")],
        widget=forms.RadioSelect,
    )
    battery_capacity = forms.IntegerField(
        label="Leistung in kWh",
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )
    battery_planned = forms.ChoiceField(
        label="Beabsichtigen Sie, diese zu erweitern?",
        choices=[(True, "Ja"), (False, "Nein")],
        widget=forms.RadioSelect,
    )

    def __init__(self, *args, **kwargs):
        """
        Adjusts the required attribute of battery_capacity based on
        the initial or submitted value of `battery_exists`.
        """
        super().__init__(*args, **kwargs)
        battery_exists_value = self.data.get("battery_exists") or self.initial.get("battery_exists")

        if battery_exists_value in [False, "False", "0", None, ""]:
            self.fields["battery_capacity"].required = False


class VentilationSystemForm(ValidationForm):
    ventilation_system_exists = forms.ChoiceField(
        label="Lüftungsanlage mit Wärmerückgewinnung vorhanden?",
        choices=[(True, "Ja"), ("doesnt_exist", "Nein")],
        widget=forms.RadioSelect,
    )


class VentilationSystemYearForm(ValidationForm):
    ventilation_system_construction_year = forms.IntegerField(
        label="Baujahr",
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )


class RenovationTechnologyForm(ValidationForm):
    primary_heating = forms.ChoiceField(
        label="Heizungstechnologie",
        choices=[
            ("district_heating", "Fernwärme"),
            ("bio_mass", "Biomasseheizung"),
            ("heat_pump", "Wärmepumpe"),
            ("oil_heating", "Effiziente Öl- und Gasheizung"),
            ("heating_rod", "Heizstab"),
            ("bhkw", "BHKW"),
        ],
        widget=forms.RadioSelect,
    )


class RenovationSolarForm(ValidationForm):
    secondary_heating = forms.MultipleChoiceField(
        label="Zusätzliche Erzeuger",
        choices=[
            ("solar", "Solarthermie"),
        ],
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )
    secondary_heating_hidden = forms.CharField(widget=forms.HiddenInput(), required=False, initial="none")


class RenovationPVSolarForm(ValidationForm):
    secondary_heating = forms.MultipleChoiceField(
        label="Zusätzliche Erzeuger",
        choices=[
            ("pv", "PV-Anlage"),
            ("solar", "Solarthermie"),
        ],
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )
    secondary_heating_hidden = forms.CharField(widget=forms.HiddenInput(), required=False, initial="none")


class RenovationBioMassForm(ValidationForm):
    bio_mass_source = forms.ChoiceField(
        label="Energieträger",
        choices=[
            ("wood_pellets", "Holzpellets"),
            ("wood_chips", "Hackschnitzel"),
            ("firewood", "Scheitholz"),
        ],
        widget=forms.RadioSelect,
    )
    secondary_heating = forms.MultipleChoiceField(
        label="Zusätzliche Erzeuger",
        choices=[
            ("solar", "Solarthermie"),
        ],
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )
    secondary_heating_hidden = forms.CharField(widget=forms.HiddenInput(), required=False, initial="none")


class RenovationHeatPumpForm(ValidationForm):
    heat_pump_type = forms.ChoiceField(
        label="Wärmepumpentyp",
        choices=[
            ("geothermal_pump", "Erdwärmepumpe"),
            ("air_heat_pump", "Luftwärmepumpe"),
            ("groundwater", "Grundwasser-/Solewärmepumpe"),
        ],
        widget=forms.RadioSelect,
    )
    secondary_heating = forms.MultipleChoiceField(
        label="Zusätzliche Erzeuger",
        choices=[
            ("oil_heating", "Effiziente Öl- und Gasheizung"),
            ("heating_rod", "Heizstab"),
            ("pv", "PV-Anlage"),
            ("solar", "Solarthermie"),
        ],
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )
    secondary_heating_hidden = forms.CharField(widget=forms.HiddenInput(), required=False, initial="none")


class RenovationRequestForm(ValidationForm):
    facade_renovation = forms.BooleanField(
        label="Fassade sanieren",
        required=False,
    )
    facade_renovation_details = forms.ChoiceField(
        label="",
        choices=[
            ("paint", "streichen"),
            ("plaster", "verputzen"),
            ("insulate", "dämmen"),
        ],
        widget=forms.RadioSelect,
        required=False,
    )
    roof_renovation = forms.BooleanField(
        label="Dach sanieren",
        required=False,
    )
    roof_renovation_details = forms.MultipleChoiceField(
        label="",
        choices=[
            ("cover", "decken"),
            ("expand", "ausbauen"),
        ],
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )
    roof_renovation_details_hidden = forms.CharField(widget=forms.HiddenInput(), required=False, initial="none")
    window_renovation = forms.BooleanField(
        label="Fenster austauschen",
        required=False,
    )
    cellar_renovation = forms.BooleanField(
        label="Kellerdeckendämmung",
        required=False,
    )

    def clean(self):
        cleaned_data = super().clean()
        errors = {}

        if cleaned_data.get("facade_renovation") and not cleaned_data.get("facade_renovation_details"):
            errors["facade_renovation_details"] = (
                "Bitte mindestens eine Spezifikation fürs Fassade sanieren auswählen."
            )

        if cleaned_data.get("roof_renovation") and not cleaned_data.get("roof_renovation_details"):
            errors["roof_renovation_details"] = "Bitte mindestens eine Spezifikation fürs Dach sanieren auswählen."

        if errors:
            raise forms.ValidationError(errors)

        return cleaned_data


class FinancialSupportForm(ValidationForm):
    subsidy = forms.MultipleChoiceField(
        label="Zuschüsse",
        choices=[
            ("sub1", "Steuerliche Förderung energetischer Sanierungsmaßnahmen"),
            (
                "sub2",
                "BAFA - Bundesförderung für effiziente Gebäude - Maßnahmen an der Gebäudehülle - "
                "(BEG EM) (Zuschuss inkl. iSFP-Bonus)",
            ),
            (
                "sub3",
                "KfW - Bundesförderung für effiziente Gebäude - Heizungsförderung für Privatpersonen - "
                "Wohngebäude (BEG EM) (Nr. 458) (Zuschuss inkl. Klima-Bonus)",
            ),
            (
                "sub4",
                "KfW - Bundesförderung für effiziente Gebäude - Heizungsförderung für Privatpersonen - "
                "Wohngebäude (BEG EM) (Nr. 458) (Effizienz-Bonus)",
            ),
            ("sub5", "Einkommensbonus"),
            ("sub6", "Emissionsminderungszuschlag"),
        ],
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )
    subsidy_hidden = forms.CharField(widget=forms.HiddenInput(), required=False, initial="none")
    promotional_loan = forms.MultipleChoiceField(
        label="Förderkredit",
        choices=[
            ("loan1", "KfW - Bundesförderung für effiziente Gebäude - Ergänzungskredit"),
        ],
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )
    promotional_loan_hidden = forms.CharField(widget=forms.HiddenInput(), required=False, initial="none")
