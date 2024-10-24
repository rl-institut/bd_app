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
    "roof_insulation": [
        "partials/roof_insulation_partial.html",
        "roof_insulation_form",
        RoofInsulationForm,
    ],
    "roof_details": [
        "partials/roof_details_partial.html",
        "roof_details_form",
        RoofDetailsForm,
    ],
}


def roof_view(request):
    """
    This view renders the first roof-page load with its forms (GET)
    or it renders partials with the next forms depending on the input (POST).

    Parameters:
    - request: HttpRequest object representing the client's request.

    Returns:
    - render, with the fitting partial and form
    """
    if request.method != "POST":
        form_step = put_step_in_session(request, "roof_step", "roof_type")
    if request.method == "POST":
        if request.POST.get("roof_type") == "flachdach":
            form_step = put_step_in_session(request, "roof_step", "roof_insulation")

        elif (
            request.POST.get("roof_type") == "satteldach"
            or request.POST.get("roof_type") == "walmdach"
        ):
            form_step = put_step_in_session(request, "roof_step", "roof_details")

        else:
            form_step = put_step_in_session(request, "roof_step", "roof_insulation")

    partial_name, template_variable, form_class = roof_form_steps[form_step[-1]]
    form_instance = form_class()
    return render(request, partial_name, {template_variable: form_instance})


def put_step_in_session(request, name_session_list, current_step):
    """
    Handles the saving of a step in the session.
    returns: form_step_list, the list with all steps used in this view
    """
    form_step_list = request.session.get(name_session_list, [])
    form_step_list.append(current_step)
    request.session["roof_step"] = form_step_list

    return form_step_list
