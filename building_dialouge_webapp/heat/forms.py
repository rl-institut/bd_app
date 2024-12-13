from django import forms
from django.forms import ValidationError


class BuildingTypeForm(forms.Form):
    building_type = forms.ChoiceField(
        label="building_type",
        choices=[
            ("single_family", "Einfamlienhaus"),
            ("apartment_building", "Mehrfamilienhaus"),
        ],
        widget=forms.RadioSelect,
    )


class BuildingTypeProtectionForm(forms.Form):
    monument_protection = forms.ChoiceField(
        label="monument_protection",
        choices=[("yes", "Ja"), ("no", "Nein")],
    )


class BuildingDataForm(forms.Form):
    construction_year = forms.IntegerField(
        label="construction_year",
        widget=forms.NumberInput(attrs={"class": "form-control"}),
        max_value=2030,
        min_value=1850,
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


class CellarHeatingForm(forms.Form):
    cellar_heating = forms.ChoiceField(
        label="cellar_heating",
        choices=[
            ("no_cellar", "Kein Keller"),
            ("without_heating", "Keller ohne Heizung"),
            ("with_heating", "Keller mit Heizung"),
        ],
        widget=forms.RadioSelect,
    )


class CellarDetailsForm(forms.Form):
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
    )
    cellar_height = forms.FloatField(
        label="cellar_height",
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )


class CellarInsulationForm(forms.Form):
    cellar_ceiling_insulation_exists = forms.ChoiceField(
        label="cellar_ceiling_insulation_exists",
        choices=[(True, "Ja"), ("doesnt_exist", "Nein")],
    )


class CellarInsulationYearForm(forms.Form):
    cellar_insulation_year = forms.IntegerField(
        label="cellar_insulation_year",
        widget=forms.NumberInput(attrs={"class": "form-control"}),
        max_value=2030,  # aktuelles Jahr per python bekommen?
        min_value=1850,
    )


class HeatingSystemForm(forms.Form):
    heating_system = forms.ChoiceField(
        label="Heizungsart",
        choices=[
            ("central_heating", "Zentralheizung"),
            ("level_heating", "Etagenheizung"),
            ("night_storage", "Nachtspeicherheizung"),
        ],
        widget=forms.RadioSelect,
    )


class HeatingSourceForm(forms.Form):
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


class HotwaterHeatingSystemForm(forms.Form):
    hotwater_heating_system = forms.ChoiceField(
        label="Warmwasserbereitung erfolgt in ",
        choices=[
            ("boiler", "Boiler / Durchlauferhitzer"),
            ("heater", "Heizanlage"),
        ],
        widget=forms.RadioSelect,
    )


class HotwaterHeatingMeasuredForm(forms.Form):
    hotwater_measured = forms.ChoiceField(
        label="Wird der WW Verbrauch separat gemessen?",
        choices=[(True, "Ja"), (False, "Nein")],
    )


class HotwaterHeatingSolarExistsForm(forms.Form):
    solar_thermal_exists = forms.ChoiceField(
        label="Solarthermieanlage vorhanden?",
        choices=[
            ("only_hotwater", "Ja, für Warmwasser"),
            ("both", "Ja, für WW und Heizung"),
            ("doesnt_exist", "Nein"),
        ],
        widget=forms.RadioSelect,
    )


class HotwaterHeatingSolarKnownForm(forms.Form):
    solar_thermal_energy_known = forms.ChoiceField(
        label="Heizenergie bekannt?",
        choices=[("known", "Ja"), ("unknown", "Unbekannt")],
    )


class HotwaterHeatingSolarEnergyForm(forms.Form):
    solar_thermal_energy = forms.IntegerField(
        label="Heizenergie",
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )


class HotwaterHeatingSolarDetailsForm(forms.Form):
    solar_thermal_area = forms.FloatField(
        label="Kollektorfläche in m²",
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )
    roof_pitch = forms.IntegerField(
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


class ConsumptionInputForm(forms.Form):
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
    heating_conpumtion_unit = forms.ChoiceField(
        choices=[("kwh", "kWh"), ("l", "l"), ("kg", "kg"), ("m³", "m³")],
    )
    heating_energy_source_cost = forms.FloatField(
        label="Brennstoffkosten in €",
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )
    hotwater_consumption = forms.FloatField(
        label="Warmwasser: Verbrauch m³ pro kWh",
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )
    hotwater_temperature = forms.IntegerField(
        label="Warmwasser: Temperatur",
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get("heating_consumption_period_start")
        end = cleaned_data.get("heating_consumption_period_end")

        if start and end:
            if end <= start:
                raise ValidationError("End date must be after start date.")  # noqa: TRY003, EM101


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


class RoofDetailsForm(forms.Form):
    roof_area = forms.IntegerField(
        label="roof_area",
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )
    roof_orientation = forms.ChoiceField(
        label="In welcher Richtung ist ihr Dach ausgerichtet?",
        choices=[
            ("n", "N"),
            ("no", "NO"),
            ("o", "O"),
            ("so", "SO"),
            ("sw", "SW"),
            ("s", "S"),
            ("w", "W"),
            ("nw", "NW"),
        ],
        widget=forms.RadioSelect,
    )
    number_roof_windows = forms.IntegerField(
        label="number_of_windows",
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )


class RoofUsageNowForm(forms.Form):
    roof_usage_now = forms.ChoiceField(
        label="roof_usage_now",
        choices=[
            ("all_used", "Vollständig genutzt/beheizt"),
            ("part_used", "Teilweise genutzt/beheizt"),
            ("not_used", "Nicht genutzt/beheizt"),
        ],
        widget=forms.RadioSelect,
    )


class RoofUsageFutureForm(forms.Form):
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
        max_value=100,
        min_value=0,
    )


class RoofInsulationForm(forms.Form):
    roof_insulation_exists = forms.ChoiceField(
        label="roof_insulation_exists",
        choices=[(True, "Ja"), (False, "Nein")],
    )


class WindowAreaForm(forms.Form):
    window_area = forms.ChoiceField(
        label="Umfang Fensterflächen",
        choices=[
            ("small", "Niedrig (wenige Fensterflächen)"),
            ("medium", "Mittel (durchschnittlich große Fensterflächen)"),
            ("large", "Hoch (viele Fensterfächen)"),
        ],
        widget=forms.RadioSelect,
    )


class WindowDetailsForm(forms.Form):
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
        label="Fenstertyp",
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
        max_value=2030,
        min_value=1850,
    )
    window_share = forms.IntegerField(
        label="prozentualer Anteil (bei mehreren Typen)",
        widget=forms.NumberInput(attrs={"class": "form-control"}),
        max_value=100,
        min_value=0,
    )

    def clean(self):
        cleaned_data = super().clean()
        choice = cleaned_data.get("window_construction_year")
        year = cleaned_data.get("seperate_year")

        if choice == "year" and not year:
            self.add_error("seperate_year", "Bitte ein Jahr angeben.")

        return cleaned_data


class FacadeForm(forms.Form):
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


class FacadeInsulationForm(forms.Form):
    facade_insulation_exists = forms.ChoiceField(
        label="Dämmung vorhanden?",
        choices=[("exists", "Ja"), ("doesnt_exist", "Nein"), ("unkown", "Unbekannt")],
    )


class FacadeInsulationYearForm(forms.Form):
    facade_construction_year = forms.IntegerField(
        label="Jahr",
        widget=forms.NumberInput(attrs={"class": "form-control"}),
        max_value=2030,
        min_value=1850,
    )


class HeatingForm(forms.Form):
    heating_system_construction_year = forms.IntegerField(
        label="Baujahr Heizung",
        widget=forms.NumberInput(attrs={"class": "form-control"}),
        max_value=2030,
        min_value=1850,
    )
    condensing_boiler_exists = forms.ChoiceField(
        label="Brennwerttechnik vorhanden?",
        choices=[(True, "Ja"), (False, "Nein"), ("unkown", "Unbekannt")],
        widget=forms.RadioSelect,
    )


class HeatingHydraulicForm(forms.Form):
    hydraulic_balancing_done = forms.ChoiceField(
        label="Hydraulischer Abgleich durchgeführt?",
        choices=[(True, "Ja"), (False, "Nein"), ("unkown", "Unbekannt")],
        widget=forms.RadioSelect,
    )


class HeatingDetailsForm(forms.Form):
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


class HeatingStorageForm(forms.Form):
    heating_storage_capacity = forms.IntegerField(
        label="Wärmespeicher Fassungsvermögen in l",
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )


class PVSystemForm(forms.Form):
    pv_exists = forms.ChoiceField(
        label="PV-Anlage vorhanden?",
        choices=[(True, "Ja"), ("doesnt_exist", "Nein")],
        widget=forms.RadioSelect,
    )


class PVSystemPlannedForm(forms.Form):
    pv_planned = forms.ChoiceField(
        label="Beabsichtigen Sie, eine zu installieren?",
        choices=[(True, "Ja"), (False, "Nein")],
        widget=forms.RadioSelect,
    )


class PVSystemDetailsForm(forms.Form):
    pv_construction_year = forms.IntegerField(
        label="Baujahr",
        widget=forms.NumberInput(attrs={"class": "form-control"}),
        max_value=2030,
        min_value=1850,
    )
    pv_capacity = forms.IntegerField(
        label="Leistung in kWp",
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )


class PVSystemBatteryForm(forms.Form):
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


class VentilationSystemForm(forms.Form):
    ventilation_system_exists = forms.ChoiceField(
        label="Lüftungsanlage mit Wärmerückgewinnung vorhanden?",
        choices=[(True, "Ja"), ("doesnt_exist", "Nein")],
        widget=forms.RadioSelect,
    )


class VentilationSystemYearForm(forms.Form):
    ventilation_system_construction_year = forms.IntegerField(
        label="Baujahr",
        widget=forms.NumberInput(attrs={"class": "form-control"}),
        max_value=2030,
        min_value=1850,
    )


class RenovationTechnologyForm(forms.Form):
    primary_heating = forms.ChoiceField(
        label="Technologie/Energieträger",
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


class RenovationSolarForm(forms.Form):
    secondary_heating = forms.MultipleChoiceField(
        label="Heizungs-Untertechnologie",
        choices=[
            ("solar", "Solarthermie"),
        ],
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )


class RenovationPVSolarForm(forms.Form):
    secondary_heating = forms.MultipleChoiceField(
        label="Heizungs-Untertechnologie",
        choices=[
            ("pv", "PV-Anlage"),
            ("solar", "Solarthermie"),
        ],
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )


class RenovationBioMassForm(forms.Form):
    bio_mass_source = forms.ChoiceField(
        label="Heizungs-Untertechnologie",
        choices=[
            ("wood_pellets", "Holzpellets"),
            ("chip_heating", "Hackschnitzelheizungen"),
            ("firewood_boilder", "Scheitholzkessel"),
        ],
        widget=forms.RadioSelect,
    )
    secondary_heating = forms.MultipleChoiceField(
        label="",
        choices=[
            ("solar", "Solarthermie"),
        ],
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )


class RenovationHeatPumpForm(forms.Form):
    heat_pump_type = forms.ChoiceField(
        label="Heizungs-Untertechnologie",
        choices=[
            ("geothermal_pump", "Erdwärmepumpe"),
            ("air_heat_pump", "Luftwärmepumpe"),
            ("groundwater", "Grundwasser-/Solewärmepumpe"),
        ],
        widget=forms.RadioSelect,
    )
    secondary_heating = forms.MultipleChoiceField(
        label="",
        choices=[
            ("oil_heating", "Effiziente Öl- und Gasheizung"),
            ("heating_rod", "Heizstab"),
            ("pv", "PV-Anlage"),
            ("solar", "Solarthermie"),
        ],
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )


class RenovationRequestForm(forms.Form):
    facade_renovation = forms.BooleanField(
        label="Fassade sanieren",
        required=False,
    )
    facade_renovation_details = forms.MultipleChoiceField(
        label="",
        choices=[
            ("paint", "streichen"),
            ("plaster", "verputzen"),
            ("insulate", "dämmen"),
        ],
        widget=forms.CheckboxSelectMultiple,
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


class FinancialSupportForm(forms.Form):
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
    promotional_loan = forms.MultipleChoiceField(
        label="Förderkredit",
        choices=[
            ("loan1", "KfW - Bundesförderung für effiziente Gebäude - Ergänzungskredit"),
        ],
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )
