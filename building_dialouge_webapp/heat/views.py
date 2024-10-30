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


def put_step_in_session(request, name_session_list, current_step):
    """
    Handles the saving of a step in the session.
    returns: form_step_list, the list with all steps used in this view
    """
    form_step_list = request.session.get(name_session_list, [])
    form_step_list.append(current_step)
    request.session[name_session_list] = form_step_list

    return form_step_list


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
    compare_dict = {}  # noqa: F841

    if request.method == "GET":
        # del request.session["form_input"] # noqa: ERA001
        if request.session.get("form_input", []) == []:
            partial_name, template_variable, form_class = roof_form_steps["roof_type"]
            print("empty session")  # noqa: T201

    if request.method == "POST":
        request_dict = request.POST.dict()
        session_dict = request.session.get("form_input", [])  # noqa: F841
        print(request_dict)  # noqa: T201
        if request.POST.get("roof_type") == "flachdach":
            form = RoofTypeForm(request.POST)
            if form.is_valid():
                form_input = form.cleaned_data
                request.session["form_input"] = form_input
            partial_name, template_variable, form_class = roof_form_steps[
                "roof_insulation"
            ]

        elif (
            request.POST.get("roof_type") == "satteldach"
            or request.POST.get("roof_type") == "walmdach"
        ):
            form = RoofTypeForm(request.POST)
            if form.is_valid():
                form_input = form.cleaned_data
                request.session["form_input"] = form_input
            partial_name, template_variable, form_class = roof_form_steps[
                "roof_details"
            ]

        else:
            form = RoofDetailsForm(request.POST)
            if form.is_valid():
                form_input = form.cleaned_data
                request.session["form_input"] = form_input
            partial_name, template_variable, form_class = roof_form_steps[
                "roof_insulation"
            ]

    print(request.session["form_input"])  # noqa: T201
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
    form_step = put_step_in_session(request, "window_step", "window_area")

    partial_name, template_variable, form_class = window_form_steps[form_step[-1]]
    form_instance = form_class()
    return render(request, partial_name, {template_variable: form_instance})
