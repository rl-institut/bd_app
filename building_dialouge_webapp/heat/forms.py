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
        "single_family": "Ein Einfamilienhaus ist ein Wohngebäude, das für die Nutzung durch "
        "eine einzige Familie bzw. einen einzigen Haushalt vorgesehen ist. Ein Haus gilt auch "
        "dann als Einfamilienhaus, wenn es zwei Wohneinheiten enthält und eine davon eine "
        "Einliegerwohnung ist, also von untergeordnete Bedeutung ist (Beispiel: Ferienwohnung).",
        "apartment_building": "Wohngebäude, das mehrere separate Wohneinheiten enthält, die von "
        "verschiedenen Familien oder Haushalten bewohnt werden.",
        "terraced_house": "Ein Reihenhaus ist ein Einfamilienhaus, das in einer Reihe identischer "
        "oder ähnlicher Häuser direkt aneinandergebaut ist. Es teilt sich mindestens eine Seitenwand "
        "mit dem Nachbarhaus und bietet eine kosteneffiziente Wohnlösung mit eigenem Eingang und "
        "oft einem kleinen Garten.",
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
        "gas": "Fossiler Brennstoff, der häufig zur effizienten und sauberen Wärmeerzeugung in "
        "Heizkesseln verwendet wird.",
        "oil": "Flüssiger fossiler Brennstoff, der in speziellen Kesseln verbrannt wird, "
        "um Wärme für Gebäude zu erzeugen, und bietet eine hohe Energiedichte.",
        "district_heating": "Wird durch ein zentrales Heizkraftwerk erzeugt und über isolierte "
        "Rohrleitungen direkt zu Gebäuden transportiert, was effiziente und umweltfreundliche "
        "Beheizung ermöglicht.",
        "liquid_gas": "Ein unter Druck verflüssigtes Gasgemisch, das in Tanks gespeichert wird "
        "und eine flexible Heizlösung für Gebiete ohne Erdgasanschluss bietet.",
        "wood_pellets": "Verdichtete Holzabfälle, die als umweltfreundlicher Brennstoff für "
        "Pelletöfen und -kessel genutzt werden, um Wärme zu erzeugen.",
        "geothermal_pump": "Sie nutzt die konstante Erdwärme unter der Oberfläche, um Gebäude "
        "effizient und umweltfreundlich zu heizen und zu kühlen.",
        "air_heat_pump": "Sie entzieht der Außenluft Wärme, um Gebäude zu beheizen, und sind eine "
        "effiziente Heizoption bei milden Klimabedingungen.",
        "groundwater": "Nutzt die Wärmeenergie aus Grundwasser oder einem Solekreislauf, um "
        "besonders effizient Wärme zu erzeugen.",
        "heating_rod": "Elektrisches Heizelement, das direkt in Wasserboilern oder Heizkörpern "
        "eingesetzt wird, um Wasser schnell zu erhitzen oder zusätzliche Wärme zu liefern.",
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
            ("geothermal_pump", "Erdwärmepumpe"),
            ("air_heat_pump", "Luftwärmepumpe"),
            ("groundwater", "Grundwasser- oder Solewärmepumpe"),
            ("heating_rod", "Heizstab"),
        ],
        widget=EnergySourceSelect(),
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


class RoofTypeSelect(RadioSelect):
    template_name = "forms/energy_source.html"

    INFOS = {
        "exists": "Ein Flachdach ist ein Dach mit einer sehr geringen Neigung, das fast waagerecht verläuft.",
    }

    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):  # noqa: PLR0913
        option = super().create_option(name, value, label, selected, index, subindex, attrs)
        option["info"] = self.INFOS.get(value, "")
        return option


class RoofTypeForm(forms.Form):
    flat_roof = forms.ChoiceField(
        label="Besitzt ihr Gebäude ein Flachdach?",
        choices=[
            ("exists", "Ja"),
            ("doesnt_exist", "Nein"),
        ],
        widget=RoofTypeSelect(),
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
        label="Dachneigung in Grad",
        widget=forms.NumberInput(attrs={"class": "form-control"}),
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
        template_name="forms/heating-storage-capacity.html",
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
            ("geothermal_pump", "Erdwärmepumpe"),
            ("air_heat_pump", "Luftwärmepumpe"),
            ("groundwater", "Grundwasser- oder Solewärmepumpe"),
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
        label="Fassade dämmen",
        required=False,
    )
    roof_renovation = forms.BooleanField(
        label="Dach",
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
    window_renovation = forms.BooleanField(
        label="Fenster austauschen",
        required=False,
    )
    cellar_renovation = forms.BooleanField(
        label="Kellerdeckendämmung",
        required=False,
    )
    entrance_renovation = forms.BooleanField(
        label="Eingangstür erneuern",
        required=False,
    )
    renovation_input_hidden = forms.CharField(widget=forms.HiddenInput(), required=False, initial="none")

    def clean_renovation_input_hidden(self):
        return self.cleaned_data.get("renovation_input_hidden", "none")

    def clean(self):
        cleaned_data = super().clean()
        errors = {}

        if cleaned_data.get("roof_renovation") and not cleaned_data.get("roof_renovation_details"):
            errors["roof_renovation_details"] = "Bitte eine Spezifikation fürs Dach sanieren auswählen."

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
