from django import forms
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

    context = {
        "form_instances": [f() for f in form_classes],
    }

    return render(request, "pages/heat_forms.html", context)
