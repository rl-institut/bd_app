from django import forms


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


class RoofInsulationForm(forms.Form):
    roof_insulation_exists = forms.ChoiceField(
        label="roof_insulation_exists",
        choices=[(True, "Yes"), (False, "No")],
    )


class ElectricityConsumptionForm(forms.Form):
    household_members = forms.ChoiceField(
        label="Wie viele Personen leben in ihrem Haushalt?",
        choices=[
            ("", "bitte auswählen"),
            ("1", "1"),
            ("2", "2"),
            ("3", "3"),
            ("4", "4"),
            ("5", "5"),
        ],
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    net_electricity_consumption1 = forms.IntegerField(
        label="Netto strom Verbrauch genau:",
        widget=forms.NumberInput(attrs={"class": "form-control"}),
        required=False,
    )
    net_electricity_consumption2 = forms.ChoiceField(
        label="oder ungefähr",
        choices=[
            ("", "bitte auswählen"),
            ("high_consumption", "viel"),
            ("medium_consumption", "mittel"),
            ("low_consumption", "wenig"),
        ],
        required=False,
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    def clean(self):
        cleaned_data = super().clean()
        net_electricity_consumption1 = cleaned_data.get("net_electricity_consumption1")
        net_electricity_consumption2 = cleaned_data.get("net_electricity_consumption2")

        if not net_electricity_consumption1 and not net_electricity_consumption2:
            self.add_error(
                "net_electricity_consumption2",
                "Nettostromverbrauch entweder genau oder ungefähr eingeben.",
            )

        return cleaned_data


class ElectricityGenerationForm(forms.Form):
    pv_owned = forms.BooleanField(
        label="Haben Sie eine PV-Anlage?",
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
        required=False,
    )
    installed_pv_power = forms.IntegerField(
        label="Wie groß ist die installierte Leistung?",
        widget=forms.NumberInput(attrs={"class": "form-control"}),
        required=False,
    )
    roof_cardinal_direction = forms.ChoiceField(
        label="In welcher Richtung ist ihr Haus ausgerichtet?",
        choices=[
            ("north", "Norden"),
            ("east", "Osten"),
            ("south_east", "Süd/Ost"),
            ("south", "Süden"),
            ("west", "Westen"),
        ],
        widget=forms.RadioSelect,
    )
    roof_angle = forms.ChoiceField(
        label="Welchen Winkel hat das Dach?",
        choices=[
            ("north", "Flach"),
            ("east", "Schräg"),
        ],
        widget=forms.RadioSelect,
    )

    def clean(self):
        cleaned_data = super().clean()
        pv_owned = cleaned_data.get("pv_owned")
        installed_pv_power = cleaned_data.get("installed_pv_power")

        if pv_owned and not installed_pv_power:
            self.add_error("installed_pv_power", "Installierte Leistung eingeben.")
        if not pv_owned and installed_pv_power:
            self.add_error(
                "pv_owned",
                "Ankreuzen/auswählen, wenn eine installierte Leistung eingegeben wird.",
            )

        return cleaned_data


class HeatGenerationForm(forms.Form):
    heat_output = forms.IntegerField(
        label="thermische Leistung der Heizungsanlage (Kessel)",
        widget=forms.NumberInput(attrs={"class": "form-control"}),
        required=False,
    )
    cannot_enter_info = forms.BooleanField(
        label="nicht vorhanden",
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )
    heat_pump_share = forms.MultipleChoiceField(
        label="Aus welchen Anteilen setzt sich ihre Wärmepumpe zusammen?",
        choices=[
            ("air", "Luft"),
            ("water", "Wasser"),
            ("brine", "Sole"),
            ("no_heat_pump", "keine Wärmepumpe"),
        ],
        widget=forms.CheckboxSelectMultiple,
    )

    def clean(self):
        cleaned_data = super().clean()
        heat_output = cleaned_data.get("heat_output")
        cannot_enter_info = cleaned_data.get("cannot_enter_info")

        if not heat_output and not cannot_enter_info:
            self.add_error("cannot_enter_info", "'Nicht vorhanden' auswählen.")
        if heat_output and cannot_enter_info:
            self.add_error(
                "heat_output",
                "Keine Leistung eintragen, wenn 'Nicht vorhanden'.",
            )

        return cleaned_data


class HeatGenerationForm2(forms.Form):
    solar_thermal_system = forms.BooleanField(
        label="Haben Sie eine Solarthermieanlage?",
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
        required=False,
    )
    collector_surface = forms.IntegerField(
        label="Kollektorfläche",
        widget=forms.NumberInput(attrs={"class": "form-control"}),
        required=False,
    )
    collector_cardinal_direction = forms.ChoiceField(
        label="In welcher Richtung ist sie ausgerichtet?",
        choices=[
            ("north", "Norden"),
            ("east", "Osten"),
            ("south", "Süden"),
            ("west", "Westen"),
        ],
        widget=forms.RadioSelect,
    )
    roof_angle = forms.ChoiceField(
        label="Welchen Winkel hat das Dach?",
        choices=[
            ("north", "Flach"),
            ("east", "Schräg"),
        ],
        widget=forms.RadioSelect,
    )

    def clean(self):
        cleaned_data = super().clean()
        solar_thermal_system = cleaned_data.get("solar_thermal_system")
        collector_surface = cleaned_data.get("collector_surface")
        collector_cardinal_direction = cleaned_data.get("collector_cardinal_direction")

        if solar_thermal_system:
            if not collector_surface:
                self.add_error(
                    "collector_surface",
                    "Dieses Feld ausfüllen, wenn Solarthermieanlage vorhanden.",
                )
            if not collector_cardinal_direction:
                self.add_error(
                    "collector_cardinal_direction",
                    "Dieses Feld ausfüllen, wenn Solarthermieanlage vorhanden.",
                )
        elif collector_surface or collector_cardinal_direction:
            error_message = "Kollektorfläche und Ausrichtung auslassen, wenn keine Solarthermieanlage vorhanden."
            raise forms.ValidationError(error_message)

        return cleaned_data


class HeatConsumptionForm(forms.Form):
    heating_requirement1 = forms.IntegerField(
        label="Jahresheizbedarf pro m² genau:",
        widget=forms.NumberInput(attrs={"class": "form-control"}),
        initial=1,
        required=False,
    )
    heating_requirement2 = forms.ChoiceField(
        label="ungefähr:",
        choices=[
            ("high_consumption", "viel"),
            ("medium_consumption", "mittel"),
            ("low_consumption", "wenig"),
        ],
        required=False,
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    def clean(self):
        cleaned_data = super().clean()
        heating_requirement1 = cleaned_data.get("heating_requirement1")
        heating_requirement2 = cleaned_data.get("heating_requirement2")

        if not heating_requirement1 and not heating_requirement2:
            self.add_error(
                "heating_requirement2",
                "Jahresheizbedarf entweder genau oder ungefähr eingeben.",
            )

        return cleaned_data


class HeatStorageForm(forms.Form):
    buffer_storage_owned = forms.BooleanField(
        label="Ist ein Pufferspeicher vorhanden?",
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
        required=False,
    )


class ElectricityStorageForm(forms.Form):
    battery_owned = forms.BooleanField(
        label="Ist eine Batterie vorhanden?",
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
        required=False,
    )
