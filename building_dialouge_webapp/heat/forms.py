import json
import re
from datetime import datetime
from datetime import timedelta
from datetime import timezone

import heat.settings as heat_settings
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
        label="Gebäudeart",
        choices=[
            ("single_family", "Einfamlienhaus"),
            ("apartment_building", "Mehrfamilienhaus"),
        ],
        widget=forms.RadioSelect,
    )


class BuildingTypeProtectionForm(ValidationForm):
    monument_protection = forms.ChoiceField(
        label="Denkmalschutz?",
        choices=[("no", "Nein"), ("yes", "Ja")],
        widget=forms.RadioSelect,
    )


class BuildingDataForm(ValidationForm):
    construction_year = forms.IntegerField(
        label="Baujahr",
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )
    number_persons = forms.IntegerField(
        label="Anzahl Personen",
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )
    number_flats = forms.IntegerField(
        label="Anzahl Wohneinheiten",
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )
    living_space = forms.IntegerField(
        label="Wohnfläche",
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )
    number_floors = forms.IntegerField(
        label="Anzahl Vollgeschosse",
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )
    adjoining_building = forms.ChoiceField(
        label="Angrenzendes Gebäude",
        choices=[
            ("no", "Nein / Freistehend"),
            ("1_side", "Eine Seite / Reihenendhaus"),
            ("2_side", "Zwei Seiten / Reihenmittelhaus"),
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


class InsulationForm(ValidationForm):
    roof_insulation_year = forms.IntegerField(
        label="Dach: Jahr",
        widget=forms.NumberInput(attrs={"class": "form-control"}),
        required=False,
    )
    upper_storey_ceiling_insulation_year = forms.IntegerField(
        label="Obere Geschossdecke: Jahr",
        widget=forms.NumberInput(attrs={"class": "form-control"}),
        required=False,
    )
    cellar_insulation_year = forms.IntegerField(
        label="Keller: Jahr",
        widget=forms.NumberInput(attrs={"class": "form-control"}),
        required=False,
    )
    facade_insulation_year = forms.IntegerField(
        label="Fassade: Jahr",
        widget=forms.NumberInput(attrs={"class": "form-control"}),
        required=False,
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


class HotwaterHeatingSolarExistsForm(ValidationForm):
    solar_thermal_exists = forms.ChoiceField(
        label="Solarthermieanlage vorhanden?",
        choices=[
            ("exist", "Ja"),
            ("doesnt_exist", "Nein"),
        ],
        widget=forms.RadioSelect,
    )


class HotwaterHeatingSolarKnownForm(ValidationForm):
    solar_thermal_area_known = forms.ChoiceField(
        label="Kollektorfläche bekannt?",
        choices=[("known", "Ja"), ("unknown", "Unbekannt")],
        widget=forms.RadioSelect,
    )


class HotwaterHeatingSolarAreaForm(ValidationForm):
    solar_thermal_area = forms.FloatField(
        label="Kollektorfläche in m²",
        widget=forms.NumberInput(attrs={"class": "form-control"}),
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
        heating_max = heat_settings.HEATING_MAX
        power_max = heat_settings.POWER_MAX
        data = self.request.session.get("django_htmx_flow", {})
        # Count occurrences of "heating" and "power" as consumption_type in session
        pattern = re.compile(r"^year[1-6]-consumption_type$")
        relevant_data = {k: v for k, v in data.items() if pattern.match(k)}

        heating_count = sum(1 for v in relevant_data.values() if v == "heating")
        power_count = sum(1 for v in relevant_data.values() if v == "power")

        # Determine initial value and whether to disable the field
        if heating_count >= heating_max:
            self.fields["consumption_type"].initial = "power"
            self.fields["consumption_type"].widget.attrs["disabled"] = True
        elif power_count >= power_max:
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
        label="Dachform",
        choices=[
            ("flachdach", "Flachdach"),
            ("satteldach", "Satteldach"),
            ("walmdach", "Walmdach"),
            ("other", "Andere Dachform"),
        ],
        widget=forms.RadioSelect,
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


class RoofInclinationKnownForm(ValidationForm):
    roof_inclination_known = forms.ChoiceField(
        label="Dachneigung bekannt?",
        choices=[("known", "Ja"), ("unknown", "Unbekannt")],
        widget=forms.RadioSelect,
    )


class RoofInclinationForm(ValidationForm):
    roof_inclination = forms.IntegerField(
        label="Dachneigung",
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )


class HeatingYearForm(ValidationForm):
    heating_system_construction_year = forms.IntegerField(
        label="Baujahr Heizung",
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )


class HeatingStorageExistsForm(ValidationForm):
    heating_storage_exists = forms.ChoiceField(
        label="Wärmespeicher vorhanden?",
        choices=[("exists", "Ja"), ("doesnt_exist", "Nein")],
        widget=forms.RadioSelect,
    )


class HeatingStorageKnownForm(ValidationForm):
    heating_storage_capacity_known = forms.ChoiceField(
        label="Fassungsvermögen des Wärmespeichers bekannt?",
        choices=[("known", "Ja"), ("unknown", "Unbekannt")],
        widget=forms.RadioSelect,
    )


class HeatingStorageCapacityForm(ValidationForm):
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


class PVSystemCapacityKnownForm(ValidationForm):
    pv_capacity_known = forms.ChoiceField(
        label="Leistung bekannt?",
        choices=[("known", "Ja"), ("unknown", "Unbekannt")],
        widget=forms.RadioSelect,
    )


class PVSystemCapacityForm(ValidationForm):
    pv_capacity = forms.IntegerField(
        label="Nennleistung in kWp",
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )


class PVSystemBatteryExistsForm(ValidationForm):
    battery_exists = forms.ChoiceField(
        label="Batterie vorhanden?",
        choices=[("exists", "Ja"), ("doesnt_exist", "Nein")],
        widget=forms.RadioSelect,
    )


class PVSystemBatteryCapacityKnownForm(ValidationForm):
    battery_capacity_known = forms.ChoiceField(
        label="Kapazität bekannt?",
        choices=[("known", "Ja"), ("unknown", "Unbekannt")],
        widget=forms.RadioSelect,
    )


class PVSystemBatteryCapacityForm(ValidationForm):
    battery_capacity = forms.IntegerField(
        label="Speicherkapazität in kWh",
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
