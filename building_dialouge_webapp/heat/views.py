from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.shortcuts import render
from django.views import generic
from viewflow.workflow.flow.views import TaskSuccessUrlMixin

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
from .forms import RoofUsageForm
from .models import Roof

# old implementation of forms, using it for instatiating Roof model


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


# BPMN Flow - views


def roof_type_view(request):
    roof_instance = request.activation.process

    if request.method == "POST":
        form = RoofTypeForm(request.POST, instance=roof_instance)
        if form.is_valid():
            form.save()
            request.activation.execute()
            return redirect(request.activation.get_next_url())

    else:
        form = RoofTypeForm(instance=roof_instance)

    return render(request, "pages/roof_type_form.html", {"form": form})


def roof_insulation_view(request):
    roof_instance = request.activation.process

    if request.method == "POST":
        form = RoofInsulationForm(request.POST, instance=roof_instance)
        if form.is_valid():
            form.save()
            request.activation.execute()
            return redirect(request.activation.get_next_url())
    else:
        form = RoofInsulationForm(instance=roof_instance)

    return render(request, "pages/roof_insulation_form.html", {"form": form})


def roof_details_view(request):
    roof_instance = request.activation.process

    if request.method == "POST":
        form = RoofDetailsForm(request.POST, instance=roof_instance)
        if form.is_valid():
            form.save()
            request.activation.execute()
            return redirect(request.activation.get_next_url())
    else:
        form = RoofDetailsForm(instance=roof_instance)

    return render(request, "pages/roof_details_form.html", {"form": form})


def roof_usage_view(request):
    roof_instance = request.activation.process.artifact

    if request.method == "POST":
        form = RoofUsageForm(request.POST, instance=roof_instance)
        if form.is_valid():
            form.save()
            request.activation.execute()
            return redirect(request.activation.get_next_url())
    else:
        form = RoofUsageForm(instance=roof_instance)

    return render(request, "pages/roof_usage_form.html", {"form": form})


class RoofTypeView(TaskSuccessUrlMixin, generic.FormView):
    model = Roof
    form_class = RoofTypeForm
    template_name = "pages/roof_type_form.html"

    def form_valid(self, form):
        self.request.activation.process.roof_type = form.cleaned_data["roof_type"]
        self.request.activation.execute()
        return HttpResponseRedirect(self.get_success_url())


class RoofInsulationView(TaskSuccessUrlMixin, generic.UpdateView):
    model = Roof
    form_class = RoofInsulationForm
    template_name = "pages/roof_insulation_form.html"

    def get_object(self):
        return self.request.activation.process.artifact

    def form_valid(self, form):
        self.object = form.save()

        self.request.activation.process.artifact = self.object

        self.request.activation
        return HttpResponseRedirect(self.get_success_url())


class RoofDetailsView(TaskSuccessUrlMixin, generic.UpdateView):
    model = Roof
    form_class = RoofDetailsForm
    template_name = "pages/roof_details_form.html"

    def get_object(self):
        return self.request.activation.process.artifact

    def form_valid(self, form):
        self.object = form.save()

        self.request.activation.process.artifact = self.object

        self.request.activation.execute()
        return HttpResponseRedirect(self.get_success_url())


class RoofUsageView(TaskSuccessUrlMixin, generic.UpdateView):
    model = Roof
    form_class = RoofUsageForm
    template_name = "pages/roof_usage_form.html"

    def get_object(self):
        return self.request.activation.process.artifact

    def form_valid(self, form):
        self.object = form.save()

        self.request.activation.process.artifact = self.object

        self.request.activation.execute()
        return HttpResponseRedirect(self.get_success_url())
