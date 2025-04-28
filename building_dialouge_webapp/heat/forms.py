import json

from django import forms
from django.core.validators import MaxValueValidator
from django.core.validators import MinValueValidator
from django.forms.widgets import RadioSelect


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


class HouseTypeSelect(RadioSelect):
    template_name = "forms/energy_source.html"

    INFOS = {
        "single_family": "Ein Einfamilienhaus ist ein Wohngebäude mit einer Wohneinheit, das von einer "
        "Familie oder einem Haushalt bewohnt wird. Einliegerwohnungen, wie z.B. Ferienwohnungen, zählen "
        "als Sonderfall mit zwei Wohneinheiten dazu.",
        "apartment_building": "Ein Mehrfamilienhaus ist ein Wohngebäude mit mehreren Wohneinheiten, in denen "
        "verschiedene Familien oder Haushalte getrennt voneinander wohnen.",
        "terraced_house": "Ein Reihenhaus ist ein Einfamilienhaus in geschlossener Bauweise, das direkt an "
        "benachbarte, ähnliche oder identische Einfamilienhäuser grenzt und mit ihnen eine oder zwei Seitenwände "
        "teilt. Es bietet eine kosteneffiziente Wohnlösung mit eigenem Eingang und oft einem kleinen Garten.",
    }

    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):  # noqa: PLR0913
        option = super().create_option(name, value, label, selected, index, subindex, attrs)
        option["info"] = self.INFOS.get(value, "")
        return option


class BuildingTypeForm(ValidationForm):
    building_type = forms.ChoiceField(
        label="Gebäudeart",
        choices=[
            ("single_family", "Einfamilienhaus"),
            ("apartment_building", "Mehrfamilienhaus"),
            ("terraced_house", "Reihenhaus"),
        ],
        widget=HouseTypeSelect(),
    )
    construction_year = forms.IntegerField(
        label="Baujahr",
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )
    number_persons = forms.IntegerField(
        label="Anzahl Personen",
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )

    def validate_with_session(self):
        min_max_defaults = {
            "single_family": {
                "number_persons": {"min": 1, "max": 10},
            },
            "apartment_building": {
                "number_persons": {"min": 2, "max": 100},
            },
            "terraced_house": {
                "number_persons": {"min": 1, "max": 10},
            },
        }

        building_type = self.data.get("building_type") or self.initial.get("building_type")
        if building_type:
            field_rules = min_max_defaults[building_type]
            for field_name, rules in field_rules.items():
                if field_name in self.fields:
                    self.fields[field_name].widget.attrs.update(
                        {"min": rules["min"], "max": rules["max"]},
                    )
                    self.fields[field_name].validators.append(MinValueValidator(rules["min"]))
                    self.fields[field_name].validators.append(MaxValueValidator(rules["max"]))


class BuildingTypeProtectionForm(ValidationForm):
    monument_protection = forms.ChoiceField(
        label="Denkmalschutz?",
        choices=[("no", "Nein"), ("yes", "Ja")],
        widget=forms.RadioSelect,
    )


class InsulationForm(ValidationForm):
    insulation_choices = forms.MultipleChoiceField(
        label="",
        choices=[
            ("roof_insulation_year", "Dach"),
            ("upper_storey_ceiling_insulation_year", "Oberste Geschossdecke"),
            ("cellar_insulation_year", "Kellerdecke"),
            ("facade_insulation_year", "Fassade"),
            ("window_insulation_year", "Fenster"),
        ],
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )

    def validate_with_session(self):
        data = self.request.session.get("django_htmx_flow", {})

        building_construction_year = data.get("construction_year", None)
        if building_construction_year:
            for fieldname in self.fields.values():
                fieldname.validators = [v for v in fieldname.validators if not isinstance(v, MinValueValidator)]
                fieldname.widget.attrs.update(
                    {"min": building_construction_year},
                )
                fieldname.validators.append(MinValueValidator(building_construction_year))


class EnergySourceSelect(RadioSelect):
    template_name = "forms/energy_source.html"

    INFOS = {
        "gas": "Fossiler Brennstoff, der häufig zur Wärmeerzeugung in Heizkesseln verwendet wird.",
        "oil": "Flüssiger fossiler Brennstoff, der in Kesseln verbrannt wird, um Wärme einer hohen "
        "Energiedichte zu bereitzustellen.",
        "district_heating": "Wärme, die in einem zentralen Heizkraftwerk erzeugt und über gedämmte "
        "Rohrleitungen zum Gebäude transportiert wird.",
        "liquid_gas": "Unter Druck verflüssigtes Gasgemisch, das in Tanks gelagert wird und eine "
        "flexible Heizlösung für Gebiete ohne Erdgasanschluss bietet.",
        "wood_pellets": "Verdichtete Holzabfälle als Brennstoff für Pelletöfen und Pelletkessel",
        "air_heat_pump": "Entzieht der Umgebungsluft Wärme, um das Gebäude zu beheizen",
        "groundwater": "Entzieht dem Grundwasser oder einem Oberflächengewässer Wärme, um das Gebäude zu beheizen",
        "geothermal_pump": "Entzieht dem Erdreich Wärme, um das Gebäude zu beheizen",
        "heating_rod": "Elektrisches Heizelement, das in Wasserboilern oder Heizkörpern zur "
        "Wärmeerzeugung eingesetzt wird",
    }

    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):  # noqa: PLR0913
        option = super().create_option(name, value, label, selected, index, subindex, attrs)
        option["info"] = self.INFOS.get(value, "")
        return option


class HeatingSourceForm(ValidationForm):
    energy_source = forms.ChoiceField(
        label="Technologie / Energieträger",
        choices=[
            ("gas", "Erdgas"),
            ("oil", "Heizöl"),
            ("district_heating", "Fernwärme"),
            ("liquid_gas", "Flüssiggas"),
            ("wood_pellets", "Holzpellets"),
            ("air_heat_pump", "Luftwärmepumpe"),
            ("groundwater", "Grundwasser- oder Oberflächengewässerwärmepumpe"),
            ("geothermal_pump", "Erdwärmepumpe"),
            ("heating_rod", "Heizstab"),
        ],
        widget=EnergySourceSelect(),
    )


class HeatingYearForm(ValidationForm):
    heating_system_construction_year = forms.IntegerField(
        label="Baujahr Heizung",
        widget=forms.NumberInput(attrs={"class": "form-control"}),
        required=False,
    )

    def validate_with_session(self):
        data = self.request.session.get("django_htmx_flow", {})

        building_construction_year = data.get("construction_year", None)
        if building_construction_year:
            field = self.fields["heating_system_construction_year"]
            field.validators = [v for v in field.validators if not isinstance(v, MinValueValidator)]
            field.widget.attrs.update(
                {"min": building_construction_year},
            )
            field.validators.append(MinValueValidator(building_construction_year))


class HeatingSolarExistsForm(ValidationForm):
    solar_thermal_exists = forms.ChoiceField(
        label="Solarthermieanlage vorhanden?",
        choices=[
            ("exist", "Ja"),
            ("doesnt_exist", "Nein"),
        ],
        widget=forms.RadioSelect,
    )


class HeatingSolarAreaForm(ValidationForm):
    solar_thermal_area = forms.FloatField(
        label="Kollektorfläche in m²",
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )


class HotwaterSupplyForm(ValidationForm):
    hotwater_year = forms.IntegerField(
        label="Baujahr",
        widget=forms.NumberInput(attrs={"class": "form-control"}),
        required=False,
    )
    hotwater_supply = forms.ChoiceField(
        label="Wird das Warmwasser mittels Durchlauferhitzer erwärmt?",
        choices=[("instantaneous_water_heater", "Ja"), ("combined", "Nein")],
        widget=forms.RadioSelect,
    )

    def validate_with_session(self):
        data = self.request.session.get("django_htmx_flow", {})

        building_construction_year = data.get("construction_year", None)
        if building_construction_year:
            field = self.fields["hotwater_year"]
            field.validators = [v for v in field.validators if not isinstance(v, MinValueValidator)]
            field.widget.attrs.update(
                {"min": building_construction_year},
            )
            field.validators.append(MinValueValidator(building_construction_year))


class HeatingStorageExistsForm(ValidationForm):
    heating_storage_exists = forms.ChoiceField(
        label="Wärmespeicher vorhanden?",
        choices=[("exists", "Ja"), ("doesnt_exist", "Nein")],
        widget=forms.RadioSelect,
    )


class HeatingStorageCapacityForm(ValidationForm):
    heating_storage_capacity = forms.IntegerField(
        label="Wärmespeicher Fassungsvermögen in l",
        widget=forms.NumberInput(attrs={"class": "form-control"}),
        template_name="forms/heating-storage-capacity.html",
    )


class RoofTypeSelect(RadioSelect):
    template_name = "forms/energy_source.html"

    INFOS = {
        "exists": "Besitzt ihr Gebäude ein Flachdach?",
    }

    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):  # noqa: PLR0913
        option = super().create_option(name, value, label, selected, index, subindex, attrs)
        option["info"] = self.INFOS.get(value, "")
        return option


class RoofTypeForm(forms.Form):
    flat_roof = forms.ChoiceField(
        label="Flachdach",
        choices=[
            ("exists", "Ja"),
            ("doesnt_exist", "Nein"),
        ],
        widget=RoofTypeSelect(),
    )


class CompassRadioSelect(forms.RadioSelect):
    template_name = "forms/compass.html"
    option_template_name = "forms/compass_radio_option.html"


class RoofOrientationForm(ValidationForm):
    roof_orientation = forms.ChoiceField(
        label="Dachausrichtung",
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
        widget=CompassRadioSelect(),
    )


class RoofInclinationKnownForm(ValidationForm):
    roof_inclination_known = forms.ChoiceField(
        label="Dachneigung bekannt?",
        choices=[("known", "Ja"), ("unknown", "Unbekannt")],
        widget=forms.RadioSelect,
    )


class RoofInclinationForm(ValidationForm):
    roof_inclination = forms.IntegerField(
        label="Dachneigung in Grad",
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )


class PVSystemForm(ValidationForm):
    pv_exists = forms.ChoiceField(
        label="PV-Anlage vorhanden?",
        choices=[(True, "Ja"), ("doesnt_exist", "Nein")],
        widget=forms.RadioSelect,
    )


class PVSystemCapacityForm(ValidationForm):
    pv_capacity = forms.IntegerField(
        label="Nennleistung in kWp",
        widget=forms.NumberInput(attrs={"class": "form-control"}),
        template_name="forms/pv-capacity.html",
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
        template_name="forms/pv-battery-capacity.html",
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
            ("air_heat_pump", "Luftwärmepumpe"),
            ("groundwater", "Wasserwärmepumpe"),
            ("geothermal_pump", "Erdwärmepumpe"),
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
    facade_renovation_choice = forms.MultipleChoiceField(
        label="",
        choices=[
            ("facade_renovation", "Fassade:"),
        ],
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )
    facade_renovation_details = forms.ChoiceField(
        label="",
        choices=[
            ("facade_insulate_renovation", "Fassade dämmen"),
            ("facade_glaster_renovation", "Fassade verputzen"),
        ],
        widget=forms.RadioSelect,
        required=False,
    )
    roof_renovation_choice = forms.MultipleChoiceField(
        label="",
        choices=[
            ("roof_renovation", "Dach:"),
        ],
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )
    roof_renovation_details = forms.ChoiceField(
        label="",
        choices=[
            ("cover", "Dach decken"),
            ("expand", "Dach ausbauen"),
        ],
        widget=forms.RadioSelect,
        required=False,
    )
    window_renovation_choice = forms.MultipleChoiceField(
        label="",
        choices=[
            ("window_renovation", "Fenster austauschen"),
        ],
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )
    cellar_renovation_choice = forms.MultipleChoiceField(
        label="",
        choices=[
            ("cellar_renovation", "Kellerdeckendämmung"),
        ],
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )
    upper_storey_ceiling_renovation_choice = forms.MultipleChoiceField(
        label="",
        choices=[
            ("upper_storey_ceiling_renovation", "Oberste Geschossdecke erneuern"),
        ],
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )
    renovation_input_hidden = forms.CharField(widget=forms.HiddenInput(), required=False, initial="none")

    def clean_renovation_input_hidden(self):
        return self.cleaned_data.get("renovation_input_hidden", "none")

    def clean(self):
        cleaned_data = super().clean()
        errors = {}

        # Autofill if one suboption was chosen
        if cleaned_data.get("roof_renovation_details"):
            cleaned_data["roof_renovation_choice"] = ["roof_renovation"]
        if cleaned_data.get("facade_renovation_details"):
            cleaned_data["facade_renovation_choice"] = ["facade_renovation"]

        # Return an error if no suboptin was chosen yet
        if cleaned_data.get("roof_renovation_choice") and not cleaned_data.get("roof_renovation_details"):
            errors["roof_renovation_details"] = "Bitte eine Spezifikation fürs Dach sanieren auswählen."

        if cleaned_data.get("facade_renovation_choice") and not cleaned_data.get("facade_renovation_details"):
            errors["facade_renovation_details"] = "Bitte eine Spezifikation fürs Fassade sanieren auswählen."

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
