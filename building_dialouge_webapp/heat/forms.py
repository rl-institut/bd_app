from django import forms


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
        choices=[(True, "Yes"), (False, "No")],
    )
