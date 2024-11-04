from django.http import HttpResponse
from django.shortcuts import render

from .forms import ElectricityConsumptionForm
from .forms import ElectricityGenerationForm
from .forms import ElectricityStorageForm
from .forms import HeatConsumptionForm
from .forms import HeatGenerationForm
from .forms import HeatGenerationForm2
from .forms import HeatStorageForm
from .forms import RoofDetailsForm
from .forms import RoofInsulationForm
from .forms import RoofTypeForm
from .forms import WindowAreaForm


def handle_forms(request):
    """
    This view renders a list which contains all the forms for the app (GET)
    or it gets all the responses from the submits and validates the forms (POST).

    Parameters:
    - request: HttpRequest object representing the client's request.

    Returns:
    - HttpResponse object containing the rendered template with the list
        of form instances.
    - HttpResponse object indicating successful form processing if all
        forms are valid.
    """
    form_classes = [
        ElectricityConsumptionForm,
        ElectricityGenerationForm,
        ElectricityStorageForm,
        HeatGenerationForm,
        HeatGenerationForm2,
        HeatConsumptionForm,
        HeatStorageForm,
    ]

    if request.method == "POST":
        # Instantiate form instances with submitted data
        form_instances = [f(request.POST) for f in form_classes]
        all_valid = all(form.is_valid() for form in form_instances)

        context = {"form_instances": form_instances}
        if all_valid:
            for form in form_instances:
                print(form.cleaned_data)  # noqa: T201
                # logic to handle form data
            return HttpResponse("All forms are valid and have been processed.")

    else:
        context = {
            "form_instances": [f() for f in form_classes],
        }

    return render(request, "pages/heat_forms.html", context)


roof_form_steps = {
    "roof_type": ["pages/roof.html", "roof_type_form", RoofTypeForm],
    "roof_details": [
        "partials/roof_details_partial.html",
        "roof_details_form",
        RoofDetailsForm,
    ],
    "roof_insulation": [
        "partials/roof_insulation_partial.html",
        "roof_insulation_form",
        RoofInsulationForm,
    ],
}


def roof_view(request):  # noqa: C901
    """
    This view renders the first roof-page load with its forms (GET)
    or it renders partials with the next forms depending on the input (POST).

    Parameters:
    - request: HttpRequest object representing the client's request.

    Returns:
    - render, with the fitting partial and form
    """
    session_dict = request.session.get("all_user_answers", {})
    if request.method == "GET":
        # needed for simulating a fresh start of the view,
        # don't use when testing reloading input data
        request.session.pop("all_user_answers", None)
        if request.session.get("all_user_answers", {}):
            forms_to_render = []

            for step, (
                partial_name,
                template_variable,
                form_class,
            ) in roof_form_steps.items():
                form_fields = form_class().fields.keys()

                # Check if all fields in this form already have data in the session
                if all(field in session_dict for field in form_fields):
                    initial_data = {field: session_dict[field] for field in form_fields}
                    form = form_class(initial=initial_data)
                    with open(  # noqa: PTH123
                        "building_dialouge_webapp/templates/" + partial_name,
                    ) as file:
                        partial_as_string = file.read()
                    forms_to_render.append(
                        (step, partial_as_string, template_variable, form),
                    )
                else:
                    # If any missing, render this form next without initial data
                    form = form_class()
                    with open(  # noqa: PTH123
                        "building_dialouge_webapp/templates/" + partial_name,
                    ) as file:
                        partial_as_string = file.read()
                    forms_to_render.append(
                        (step, partial_as_string, template_variable, form),
                    )
                    break
            context = {
                **{
                    template_variable: form
                    for _, _, template_variable, form in forms_to_render
                },
                **{
                    partial_name: partial_as_string
                    for partial_name, partial_as_string, _, _ in forms_to_render
                },
            }
            return render(request, "pages/roof.html", context)

        partial_name, template_variable, form_class = roof_form_steps["roof_type"]

    if request.htmx:
        request_dict = request.POST.dict()
        compare_dict = session_dict | request_dict

        if "flachdach" in compare_dict.values():
            form = RoofTypeForm(request.POST)
            if form.is_valid():
                form_input = form.cleaned_data
                session_dict.update(form_input)
                request.session["all_user_answers"] = session_dict
            partial_name, template_variable, form_class = roof_form_steps[
                "roof_insulation"
            ]

        elif (
            "satteldach" in compare_dict.values() or "walmdach" in compare_dict.values()
        ) and "roof_area" not in compare_dict:
            form = RoofTypeForm(request.POST)
            if form.is_valid():
                form_input = form.cleaned_data
                session_dict.update(form_input)
                request.session["all_user_answers"] = session_dict
            partial_name, template_variable, form_class = roof_form_steps[
                "roof_details"
            ]
            form_instance = form_class()
        else:
            form = RoofDetailsForm(request.POST)
            if form.is_valid():
                form_input = form.cleaned_data
                session_dict.update(form_input)
                request.session["all_user_answers"] = session_dict
            partial_name, template_variable, form_class = roof_form_steps[
                "roof_insulation"
            ]

    form_instance = form_class()
    return render(request, partial_name, {template_variable: form_instance})


window_form_steps = {
    "window_area": ["pages/window.html", "window_area_form", WindowAreaForm],
}


def window_view(request):
    """
    This view renders the first window-page load with its forms (GET)
    or it renders partials with the next forms depending on the input (POST).

    Parameters:
    - request: HttpRequest object representing the client's request.

    Returns:
    - render, with the fitting partial and form
    """

    partial_name, template_variable, form_class = window_form_steps["window_area"]
    form_instance = form_class()
    return render(request, partial_name, {template_variable: form_instance})
