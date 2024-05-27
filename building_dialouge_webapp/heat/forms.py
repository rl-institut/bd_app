from django import forms


class ElectricityConsumptionForm(forms.Form):
    household_members = forms.ChoiceField(
        label="Wie viele Personen leben in ihrem Haushalt?",
        choices=[
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
        initial=1,
        required=False,
    )
    net_electricity_consumption2 = forms.ChoiceField(
        label="oder ungefähr",
        choices=[
            ("high_consumption", "viel"),
            ("medium_consumption", "mittel"),
            ("low_consumption", "wenig"),
        ],
        required=False,
        widget=forms.Select(attrs={"class": "form-select"}),
    )


class ElectricityGenerationForm(forms.Form):
    pv_owned = forms.BooleanField(
        label="Haben Sie eine PV-Anlage?",
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )
    instlled_pv_power = forms.IntegerField(
        label="Wie groß ist die installierte Leistung?",
        widget=forms.NumberInput(attrs={"class": "form-control"}),
        initial=1,
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
        widget=forms.RadioSelect(attrs={"class": "form-check-input"}),
    )
    roof_angle = forms.ChoiceField(
        label="Welchen Winkel hat das Dach?",
        choices=[
            ("north", "Flach"),
            ("east", "Schräg"),
        ],
        widget=forms.RadioSelect(attrs={"class": "form-check-input"}),
    )


class HeatGenerationForm(forms.Form):
    heat_output = forms.IntegerField(
        label="thermische Leistung der Heizungsanlage (Kessel)",
        widget=forms.NumberInput(attrs={"class": "form-control"}),
        initial=1,
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
        widget=forms.CheckboxSelectMultiple(attrs={"class": "form-check-input"}),
    )

    solar_thermal_system = forms.BooleanField(
        label="Haben Sie eine Solarthermieanlage?",
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )
    collector_surface = forms.IntegerField(
        label="Kollektorfläche",
        widget=forms.NumberInput(attrs={"class": "form-control"}),
        initial=1,
    )
    collector_cardinal_direction = forms.ChoiceField(
        label="In welcher Richtung ist sie ausgerichtet?",
        choices=[
            ("north", "Norden"),
            ("east", "Osten"),
            ("south", "Süden"),
            ("west", "Westen"),
        ],
        widget=forms.RadioSelect(attrs={"class": "form-check-input"}),
    )
    roof_angle = forms.ChoiceField(
        label="Welchen Winkel hat das Dach?",
        choices=[
            ("north", "Flach"),
            ("east", "Schräg"),
        ],
        widget=forms.RadioSelect(attrs={"class": "form-check-input"}),
    )


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


class HeatStorageForm(forms.Form):
    buffer_storage_owned = forms.BooleanField(
        label="Ist ein Pufferspeicher vorhanden?",
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )


class ElectricityStorageForm(forms.Form):
    battery_owned = forms.BooleanField(
        label="Ist eine Batterie vorhanden?",
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )
    storage_max_capacity = forms.CharField(
        widget=forms.HiddenInput(),
    )  # TODO: add js-based slider?
