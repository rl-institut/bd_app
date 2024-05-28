from django import forms
from django.http import HttpResponse
from django.shortcuts import render

from .forms import *  # noqa: F403


def load_all_forms(request):
    """
    This view renders a list which contains all the forms for the app.

    Parameters:
    - request: HttpRequest object representing the client's request.

    Returns:
    - HttpResponse object containing the rendered template with the list
        of form instances.
    """
    form_classes = [
        f
        for f in globals().values()
        if isinstance(f, type) and issubclass(f, forms.Form)
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
