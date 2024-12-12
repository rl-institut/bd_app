import ast
import json
from abc import abstractmethod
from collections.abc import Callable
from enum import IntEnum
from typing import Any
from typing import Optional

from django.core.validators import MaxValueValidator
from django.core.validators import MinValueValidator
from django.forms import Form
from django.forms import ValidationError
from django.http import HttpResponse
from django.shortcuts import reverse
from django.template import Template
from django.template.context_processors import csrf
from django.template.loader import get_template
from django.views.generic import TemplateView
from django_htmx.http import HttpResponseClientRedirect
from django_htmx.http import retarget

from . import forms
from .navigation import SidebarNavigationMixin


class FlowError(Exception):
    """Thrown when a flow fails."""


class StateStatus(IntEnum):
    New = 0  # if state is called the first time
    Set = 1  # if state gets POST request
    Unchanged = 2  # if state has not changed and next state is called
    Changed = 3  # if state is revisited with POST request differing from session
    Error = 4  # if something went wrong within the state


class StateResponse:
    """Base class for holding state content."""

    def __init__(self, content: Any) -> None:
        self.content = content


class HTMLStateResponse(StateResponse):
    """State response holding HTML to be rendered."""

    def __init__(self, html: str) -> None:
        super().__init__(html)


class SwapHTMLStateResponse(HTMLStateResponse):
    """State response holding HTML to be swapped into other target."""


class RedirectStateResponse(StateResponse):
    """State response holding URL to redirect to."""

    def __init__(self, url: str) -> None:
        super().__init__(url)


class State:
    """
    Represents a state in a flow, handling transitions, rendering responses and managing state in session.

    Attributes:
        flow (Flow): The flow instance to which this state belongs.
        name (str): The identifier for the HTML target associated with this state.
        label (str, optional): An optional label for the state.
    """

    def __init__(
        self,
        flow: "Flow",
        name: str,
        label: str | None = None,
    ):
        self.flow = flow
        self.name = name
        self.label = label
        self._transition = None
        super().__init__()

    def transition(self, transition: "Transition") -> "State":
        """Assigns a transition to the state and sets the flow context."""
        transition.flow = self.flow
        self._transition = transition
        return self

    def next(self) -> Optional["State"]:
        """Determines the next state by following the current transition."""
        if self._transition is None:
            if isinstance(self.flow.end, EndState):
                return self.flow.end
            error_msg = f"No next state or end state defined for state '{self.name}'."
            raise FlowError(error_msg)
        return self._transition.follow(self)

    def store_state(self):
        """Saves the current state's input value to the session if the request method is POST."""
        if self.flow.request.method == "POST":
            value = self.flow.request.POST[self.name]
            session_data = self.flow.request.session.get("django_htmx_flow", {})
            session_data[self.name] = value
            self.flow.request.session["django_htmx_flow"] = session_data

    def remove_state(self):
        """Removes the current state's value from the session if it exists."""
        session_data = self.flow.request.session.get("django_htmx_flow", {})
        if self.name in session_data:
            del session_data[self.name]
            self.flow.request.session["django_htmx_flow"] = session_data

    def check_state(self) -> StateStatus:
        """Checks the status of the current state based on the session and POST data."""
        session_data = self.flow.request.session.get("django_htmx_flow", {})
        if self.name not in self.flow.request.POST and self.name not in session_data:
            return StateStatus.New
        if self.name in self.flow.request.POST and self.name not in session_data:
            return StateStatus.Set
        if self.name in self.flow.request.POST and self.flow.request.POST[self.name] != session_data.get(
            self.name,
        ):
            return StateStatus.Changed
        return StateStatus.Unchanged

    @property
    def response(self) -> dict[str, StateResponse]:
        """Return response of current state."""
        return {self.name: StateResponse(self.name)}

    @property
    def reset_response(self) -> dict[str, StateResponse]:
        """Return response of current state in case of reset."""
        return {self.name: StateResponse(self.name)}

    @property
    def error_response(self) -> dict[str, StateResponse]:
        """Return response of current state."""
        return {self.name: StateResponse("Something went wrong.")}

    def set(
        self,
        previous_state: StateStatus = StateStatus.Unchanged,
    ) -> dict[str, StateResponse]:
        """Sets or updates the state using check_state()."""
        status = StateStatus.New if previous_state == StateStatus.Set else self.check_state()
        if status == StateStatus.New:
            return self.response
        if status == StateStatus.Error:
            return self.error_response
        if status == StateStatus.Set:
            self.store_state()
            following_states = self.next().set(status)
        elif status == StateStatus.Unchanged:
            following_states = self.next().set(status)
        elif status == StateStatus.Changed:
            following_states = self.next().reset()
            self.store_state()
            next_state = self.next()
            following_states.update(next_state.response)
        else:
            error_msg = f"Unknown state status '{status}'."
            raise FlowError(error_msg)

        if self.flow.request.htmx:
            return following_states
        following_states.update(self.response)
        return following_states

    def reset(self) -> dict[str, StateResponse]:
        """Reset current state and following state."""
        try:
            following_node = self.next()
        except FlowError:
            following_node = None
        self.remove_state()
        # In case of reset, do not forward redirect responses
        if following_node is None or isinstance(following_node, EndState):
            following_states = {}
        else:
            following_states = following_node.reset()
        following_states.update(self.reset_response)
        return following_states

    @property
    def data(self) -> dict[str, Any]:
        return {self.name: self.name}


class EndState(State):
    """
    Last state in a flow

    Can be set explicitly or will be silently set.
    """

    def __init__(self, flow: "Flow", url: str, label: str = "end"):
        super().__init__(flow, name="", label=label)
        self.url = url

    def set(
        self,
        previous_state: StateStatus = StateStatus.Unchanged,
    ) -> dict[str, StateResponse]:
        return self.response

    def reset(self) -> dict[str, StateResponse]:
        return self.reset_response

    @property
    def response(self) -> dict[str, StateResponse]:
        """Return response of current state."""
        return {self.name: RedirectStateResponse(self.url)}

    @property
    def reset_response(self) -> dict[str, StateResponse]:
        """Return response of current state."""
        return {}


class TemplateState(State):
    extra_context = None

    def __init__(
        self,
        flow: "Flow",
        name: str,
        template_name: Template | str,
        label: str | None = None,
    ):
        self.template_name = template_name
        super().__init__(flow, name, label)

    def get_context_data(self):
        context = {}
        if self.extra_context is not None:
            context.update(self.extra_context)
        return context

    @property
    def response(self) -> dict[str, StateResponse]:
        context = self.get_context_data()
        return {
            self.name: HTMLStateResponse(
                get_template(self.template_name).render(context),
            ),
        }

    @property
    def reset_response(self) -> dict[str, StateResponse]:
        """Return HTML including HTMX swap-oob in order to remove/reset HTML for current target."""
        return {
            self.name: SwapHTMLStateResponse(
                f'<div id="{self.name}" hx-swap-oob="innerHTML"></div>',
            ),
        }


class FormState(TemplateState):
    """
    Represents a state with a form within a flow, handling storage, and
    change detection of individual form field values in the session.

    Attributes:
        flow (Flow): The flow instance to which this state belongs.
        name (str): The identifier for the HTML target associated with this state.
        form_class (type[Form]): Form class associated with the current state.
        template_name (str | None): Optional template name for rendering the form.
        label (str, optional): An optional label for the state.
    """

    def __init__(  # noqa: PLR0913
        self,
        flow: "Flow",
        name: str,
        form_class: type[Form],
        template_name: str | None = None,
        label: str | None = None,
    ):
        super().__init__(flow, name, template_name, label)
        self.form_class = form_class

    def _render_form(self, data):
        context = self.get_context_data()
        if self.template_name is None:
            csrf_token = csrf(self.flow.request)["csrf_token"]
            form_instance = self.form_class(data, prefix=self.flow.prefix)
            self.apply_dynamic_rules(form_instance)
            rendered_form = (
                f'<input type="hidden" name="csrfmiddlewaretoken" value="{csrf_token}">\n {form_instance.as_div()}'
            )
            return {self.name: HTMLStateResponse(rendered_form)}
        form_instance = self.form_class(data, prefix=self.flow.prefix)
        self.apply_dynamic_rules(form_instance)
        context["form"] = form_instance
        return {
            self.name: HTMLStateResponse(
                get_template(self.template_name).render(
                    context,
                    request=self.flow.request,
                ),
            ),
        }

    def apply_dynamic_rules(self, form):
        """Applies dynamic rules to the form instance."""
        with open("building_dialouge_webapp/static/json/validation.json") as file:  # noqa: PTH123
            dynamic_rules = json.load(file)
            form_rules = dynamic_rules.get(self.form_class.__name__, {})
        if form_rules:
            for field_name, rules in form_rules.items():
                """ complex validation logic still needs to be done, maybe kinda like this:
                    if field_name == "complex":
                    custom_validation = self.get_dynamic_validator(rules)
                    for target_field in rules.get("target_fields", []):
                        if target_field in form.fields:
                            form.fields[target_field].validators.append(custom_validation) """

                if field_name in form.fields:
                    field = form.fields[field_name]
                    for rule, value in rules.items():
                        setattr(field, rule, value)
                        if rule == "min_value":
                            field.widget.attrs["min"] = value
                            field.validators.append(MinValueValidator(value))
                        elif rule == "max_value":
                            field.widget.attrs["max"] = value
                            field.validators.append(MaxValueValidator(value))

    def get_dynamic_validator(self, rules):
        """Generates a dynamic validation function based on the rules."""

        def dynamic_validator(value):
            value1 = self.flow.request.session.get("django_htmx_flow", {}).get(rules["value1"])
            value2 = value

            condition = rules.get("measure")
            if value1 is not None and condition:
                if not ast.literal_eval(condition, {"value1": value1, "value2": value2}):
                    raise ValidationError(rules.get("message", "Invalid input based on dynamic validation."))

        return dynamic_validator

    @property
    def response(self) -> dict[str, StateResponse]:
        """Renders the form with data from the session if available; otherwise, renders a blank form."""
        status = self.check_state()
        data = None if status == StateStatus.New else self.flow.request.session.get("django_htmx_flow", {})
        return self._render_form(data)

    @property
    def error_response(self) -> dict[str, StateResponse]:
        """Renders the form with incorrect data from the request."""
        form_instance = self.form_class(self.flow.request.POST, prefix=self.flow.prefix)
        self.apply_dynamic_rules(form_instance)
        return self._render_form(self.flow.request.POST)

    def store_state(self):
        """Stores each form field's input value to the session."""
        if self.flow.request.method == "POST":
            session_data = self.flow.request.session.get("django_htmx_flow", {})
            form_instance = self.form_class(
                self.flow.request.POST,
                prefix=self.flow.prefix,
            )
            self.apply_dynamic_rules(form_instance)
            if form_instance.is_valid():
                form_data = form_instance.cleaned_data
                for field_name, value in form_data.items():
                    session_data[field_name if self.flow.prefix is None else f"{self.flow.prefix}-{field_name}"] = (
                        value
                    )
                self.flow.request.session["django_htmx_flow"] = session_data

    def remove_state(self):
        """Removes each form field's stored value from the session."""
        session_data = self.flow.request.session.get("django_htmx_flow", {})
        form_instance = self.form_class(prefix=self.flow.prefix)
        self.apply_dynamic_rules(form_instance)
        for field in form_instance.fields:
            key = field if self.flow.prefix is None else f"{self.flow.prefix}-{field}"
            if key in session_data:
                del session_data[key]
        self.flow.request.session["django_htmx_flow"] = session_data

    def check_state(self) -> StateStatus:  # noqa: PLR0911
        """Checks the state status using all form fields."""
        session_data = self.flow.request.session.get("django_htmx_flow", {})

        required_fields = [
            field_name if self.flow.prefix is None else f"{self.flow.prefix}-{field_name}"
            for field_name, field in self.form_class.base_fields.items()
        ]
        form = self.form_class(self.flow.request.POST, prefix=self.flow.prefix)

        if not form.is_valid():
            if any(field in required_fields for field in self.flow.request.POST):
                return StateStatus.Error
            if all(field in session_data for field in required_fields):
                # This line is only called in case of latest state firing
                return StateStatus.Unchanged
            return StateStatus.New

        # If form is valid, state is either SET, CHANGED or UNCHANGED
        if all(field not in session_data for field in required_fields):
            return StateStatus.Set

        if all(field not in self.flow.request.POST for field in required_fields):
            # This means no field is required and thus this could be a HTMX request where form is not included
            return StateStatus.Unchanged
        form_data = form.cleaned_data
        if all(
            session_data.get(field)
            == form_data.get(
                field if self.flow.prefix is None else field[len(self.flow.prefix) + 1 :],
            )
            for field in required_fields
        ):
            return StateStatus.Unchanged
        return StateStatus.Changed

    @property
    def data(self) -> dict[str, Any]:
        """Return cleaned data of the form with data from the session."""
        session_data = self.flow.request.session.get("django_htmx_flow", {})
        form = self.form_class(session_data, prefix=self.flow.prefix)
        if form.is_valid():
            return form.cleaned_data
        error_msg = f"Invalid data in flow '{self.name}': {form.errors}."
        raise FlowError(error_msg)


class FormInfoState(FormState):
    def __init__(  # noqa: PLR0913
        self,
        flow: "Flow",
        name: str,
        form_class: type[Form],
        info_text: str | dict[str, str | tuple[str, str]],
        template_name: str | None = None,
        label: str | None = None,
    ):
        super().__init__(flow, name, form_class, template_name, label)
        # info text is mapped as {target: (response text, reset text)}
        if isinstance(info_text, str):
            self.info_text = {"_info": (info_text, "")}
        else:
            self.info_text = {
                target: (value, "") if isinstance(value, str) else value for target, value in info_text.items()
            }

    @property
    def response(self) -> dict[str, StateResponse]:
        form_response = {
            target: SwapHTMLStateResponse(
                f'<div id="{target}" hx-swap-oob="innerHTML">{text[0]}</div>',
            )
            for target, text in self.info_text.items()
        }
        form_response.update(**super().response)
        return form_response

    @property
    def reset_response(self) -> dict[str, StateResponse]:
        form_response = {
            target: SwapHTMLStateResponse(
                f'<div id="{target}" hx-swap-oob="innerHTML">{text[1]}</div>',
            )
            for target, text in self.info_text.items()
        }
        form_response.update(**super().reset_response)
        return form_response


class Transition:
    def __init__(self):
        # These are set once Transition is added to state
        self.flow = None

    @abstractmethod
    def follow(self, state: "State") -> "State":
        """Must be implemented by subclasses."""

    def _state(self, state_name) -> "State":
        return getattr(self.flow, state_name)


class Next(Transition):
    def __init__(self, next_state: str):
        super().__init__()
        self.next_state = next_state

    def follow(self, state: "State") -> "State":
        return self._state(self.next_state)


class Switch(Transition):
    """
    Attributes:
        lookup (str): the field of the corresponding form on wich the switch depends
        cases : .case("returned value of the field", "name of next state")
    """

    def __init__(self, lookup: str | Callable | None = None):
        super().__init__()
        self.lookup = lookup
        self.cases = {}

    def case(self, value: Any, state_name: str) -> "Switch":
        self.cases[value] = state_name
        return self

    def default(self, state_name: str) -> "Switch":
        self.cases["_default"] = state_name
        return self

    def follow(self, state: "State") -> "State":
        result = (
            self.lookup(state)
            if self.lookup is not None and not isinstance(self.lookup, str)
            else self.default_switch_fct(state)
        )
        if result in self.cases:
            return self._state(self.cases[result])
        if "_default" in self.cases:
            return self._state(self.cases["_default"])
        error_msg = f"No option for result '{result}' found, no default given."
        raise FlowError(error_msg)

    def default_switch_fct(self, state: "State") -> Any:
        key = self.lookup if isinstance(self.lookup, str) else state.name
        key = key if self.flow.prefix is None else f"{self.flow.prefix}-{key}"
        session_data = self.flow.request.session.get("django_htmx_flow", {})
        if key in session_data:
            return session_data[key]
        if key in self.flow.request.POST:
            return self.flow.request.POST[key]
        error_msg = f"Could not find lookup {key=} in request or session."
        raise FlowError(error_msg)


class Flow(TemplateView):
    prefix: str | None = None

    def __init__(self, prefix: str | None = None):
        self.prefix = prefix
        self.request = None
        self.start = None
        self.end = None
        super().__init__()

    def dispatch(self, request, *args, **kwargs) -> HttpResponse:
        self.request = request
        state_partials = self.start.set()

        if request.htmx:
            try:
                redirect_response = next(
                    partial for partial in state_partials.values() if isinstance(partial, RedirectStateResponse)
                )
                return HttpResponseClientRedirect(reverse(redirect_response.content))
            except StopIteration:
                pass
            # Merge reset responses
            target = None
            html_response = ""
            ordered_partials = dict(
                sorted(
                    state_partials.items(),
                    key=lambda item: isinstance(item[1], SwapHTMLStateResponse),
                ),
            )
            for name, state_response in ordered_partials.items():
                html_response += state_response.content
                if isinstance(state_response, HTMLStateResponse) and not isinstance(
                    state_response,
                    SwapHTMLStateResponse,
                ):
                    target = name
            response = HttpResponse(html_response, content_type="text/html")
            return retarget(response, f"#{target}")

        # Traditional request
        context = self.get_context_data(**kwargs)
        # Remove reset responses from partials
        state_partials = {
            name: response
            for name, response in state_partials.items()
            if not isinstance(response, (SwapHTMLStateResponse, RedirectStateResponse))
        }
        context.update(state_partials)
        # Fill template with state partials by adding them with their target_id
        return self.render_to_response(context)

    def finished(self, request):
        """Check if the given flow is finished."""
        self.request = request
        node = self.start
        while True:
            if node.check_state() != StateStatus.Unchanged:
                return False
            node = node.next()
            if isinstance(node, EndState):
                return True

    def reset(self, request):
        """Reset the Flow, delete its nodes"""
        self.request = request
        node = self.start
        while True:
            next_node = node.next()
            node.remove_state()
            node = next_node
            if isinstance(node, EndState):
                break

    def data(self, request) -> dict[str, Any]:
        """Get data of the flow if finished."""
        self.request = request

        data = {}
        node = self.start
        while True:
            data.update(node.data)
            node = node.next()
            if isinstance(node, EndState):
                break
        return data


class BuildingTypeFlow(SidebarNavigationMixin, Flow):
    template_name = "pages/building_type.html"
    extra_context = {
        "back_url": "heat:intro_consumption",
        "next_includes": "#building_type,#monument_protection",
    }

    def __init__(self):
        super().__init__()
        self.start = FormState(
            self,
            name="building_type",
            form_class=forms.BuildingTypeForm,
            template_name="partials/building_type_help.html",
        ).transition(
            Next("monument_protection"),
        )

        self.monument_protection = FormState(
            self,
            name="monument_protection",
            form_class=forms.BuildingTypeProtectionForm,
            template_name="partials/building_type_protection_help.html",
        ).transition(
            Switch("monument_protection").case("yes", "dead_end_monument_protection").default("end"),
        )

        self.dead_end_monument_protection = EndState(
            self,
            url="heat:dead_end_monument_protection",
        )

        self.end = EndState(self, url="heat:building_data")


class BuildingDataFlow(SidebarNavigationMixin, Flow):
    template_name = "pages/building_data.html"
    extra_context = {
        "back_url": "heat:building_type",
        "next_includes": "#building_data",
    }

    def __init__(self):
        super().__init__()
        self.start = FormState(
            self,
            name="building_data",
            form_class=forms.BuildingDataForm,
            template_name="partials/building_data_help.html",
        ).transition(
            Next("end"),
        )

        self.end = EndState(self, url="heat:cellar")


class CellarFlow(SidebarNavigationMixin, Flow):
    template_name = "pages/cellar.html"
    extra_context = {
        "back_url": "heat:building_data",
        "next_includes": "#cellar_heating,#cellar_details,#cellar_insulation_exists,#cellar_insulation_year",
    }

    def __init__(self):
        super().__init__()
        self.start = FormState(
            self,
            name="cellar_heating",
            form_class=forms.CellarHeatingForm,
        ).transition(
            Switch("cellar_heating").case("no_cellar", "end").default("cellar_details"),
        )

        self.cellar_details = FormState(
            self,
            name="cellar_details",
            form_class=forms.CellarDetailsForm,
        ).transition(
            Next("cellar_insulation_exists"),
        )

        self.cellar_insulation_exists = FormState(
            self,
            name="cellar_insulation_exists",
            form_class=forms.CellarInsulationForm,
        ).transition(
            Switch("cellar_ceiling_insulation_exists").case("doesnt_exist", "end").default("cellar_insulation_year"),
        )

        self.cellar_insulation_year = FormState(
            self,
            name="cellar_insulation_year",
            form_class=forms.CellarInsulationYearForm,
        ).transition(
            Next("end"),
        )

        self.end = EndState(self, url="heat:hotwater_heating")


class HotwaterHeatingFlow(SidebarNavigationMixin, Flow):
    template_name = "pages/hotwater_heating.html"
    extra_context = {
        "back_url": "heat:cellar",
        "next_includes": (
            "#heating_system,#heating_source,#hotwater_heating_system,"
            "#hotwater_measured,#solar_thermal_exists,#solar_thermal_energy_known,"
            "#solar_thermal_energy,#solar_thermal_details"
        ),
    }

    def __init__(self):
        super().__init__()
        self.start = FormState(
            self,
            name="heating_system",
            form_class=forms.HeatingSystemForm,
            template_name="partials/heating_system_help.html",
        ).transition(
            Switch("heating_system").case("central_heating", "heating_source").default("dead_end_heating"),
        )

        self.dead_end_heating = EndState(self, url="heat:dead_end_heating")

        self.heating_source = FormState(
            self,
            name="heating_source",
            form_class=forms.HeatingSourceForm,
            template_name="partials/heating_source_help.html",
        ).transition(
            Next("hotwater_heating_system"),
        )

        self.hotwater_heating_system = FormState(
            self,
            name="hotwater_heating_system",
            form_class=forms.HotwaterHeatingSystemForm,
            template_name="partials/hotwater_heating_system_help.html",
        ).transition(
            Switch("hotwater_heating_system").case("boiler", "solar_thermal_exists").default("hotwater_measured"),
        )

        self.hotwater_measured = FormState(
            self,
            name="hotwater_measured",
            form_class=forms.HotwaterHeatingMeasuredForm,
        ).transition(
            Next("solar_thermal_exists"),
        )

        self.solar_thermal_exists = FormState(
            self,
            name="solar_thermal_exists",
            form_class=forms.HotwaterHeatingSolarExistsForm,
        ).transition(
            Switch("solar_thermal_exists").case("doesnt_exist", "end").default("solar_thermal_energy_known"),
        )

        self.solar_thermal_energy_known = FormState(
            self,
            name="solar_thermal_energy_known",
            form_class=forms.HotwaterHeatingSolarKnownForm,
            template_name="partials/solar_thermal_energy_known_help.html",
        ).transition(
            Switch("solar_thermal_energy_known")
            .case("known", "solar_thermal_energy")
            .default("solar_thermal_details"),
        )

        self.solar_thermal_energy = FormState(
            self,
            name="solar_thermal_energy",
            form_class=forms.HotwaterHeatingSolarEnergyForm,
        ).transition(
            Next("end"),
        )

        self.solar_thermal_details = FormState(
            self,
            name="solar_thermal_details",
            form_class=forms.HotwaterHeatingSolarDetailsForm,
        ).transition(
            Next("end"),
        )

        self.end = EndState(self, url="heat:consumption_input")


class ConsumptionInputFlow(SidebarNavigationMixin, Flow):
    template_name = "pages/consumption_input.html"
    extra_context = {
        "back_url": "heat:hotwater_heating",
        "next_includes": "#consumption_input",
    }

    def __init__(self):
        super().__init__()
        self.start = FormState(
            self,
            name="consumption_input",
            form_class=forms.ConsumptionInputForm,
        ).transition(
            Next("end"),
        )

        self.end = EndState(self, url="heat:consumption_result")


class RoofFlow(SidebarNavigationMixin, Flow):
    template_name = "pages/roof.html"
    extra_context = {
        "back_url": "heat:home",
        "next_includes": "#roof_type,#roof_details,#roof_usage_now,#roof_usage_future,#roof_insulation",
    }

    def __init__(self):
        super().__init__()
        self.start = FormState(
            self,
            name="roof_type",
            form_class=forms.RoofTypeForm,
            template_name="partials/roof_help.html",
        ).transition(
            Switch("roof_type").case("flachdach", "roof_insulation").default("roof_details"),
        )
        # roof_type results going to roof_details and roof_usage
        self.roof_details = FormState(
            self,
            name="roof_details",
            form_class=forms.RoofDetailsForm,
        ).transition(
            Next("roof_usage_now"),
        )
        self.roof_usage_now = FormInfoState(
            self,
            name="roof_usage_now",
            form_class=forms.RoofUsageNowForm,
            info_text="Dachnutzung",
        ).transition(
            Switch("roof_usage_now").case("all_used", "roof_insulation").default("roof_usage_future"),
        )
        # roof_usage results going to future usage
        self.roof_usage_future = FormState(
            self,
            name="roof_usage_future",
            form_class=forms.RoofUsageFutureForm,
        ).transition(Next("roof_insulation"))
        # last Form is Insulation
        self.roof_insulation = FormState(
            self,
            name="roof_insulation",
            form_class=forms.RoofInsulationForm,
        ).transition(
            Next("end"),
        )
        self.end = EndState(self, url="heat:window")


class WindowFlow(SidebarNavigationMixin, Flow):
    template_name = "pages/window.html"
    extra_context = {
        "back_url": "heat:roof",
        "next_includes": "#window_area,#window_details",
    }

    def __init__(self):
        super().__init__()
        self.start = FormState(
            self,
            name="window_area",
            form_class=forms.WindowAreaForm,
        ).transition(
            Next("window_details"),
        )

        self.window_details = FormState(
            self,
            name="window_details",
            form_class=forms.WindowDetailsForm,
            template_name="partials/window_details_help.html",
        ).transition(
            Next("end"),
        )

        self.end = EndState(self, url="heat:facade")


class FacadeFlow(SidebarNavigationMixin, Flow):
    template_name = "pages/facade.html"
    extra_context = {
        "back_url": "heat:window",
        "next_includes": "#facade_details,#facade_insulation_exists,#facade_insulation_year",
    }

    def __init__(self):
        super().__init__()
        self.start = FormState(
            self,
            name="facade_details",
            form_class=forms.FacadeForm,
        ).transition(
            Next("facade_insulation_exists"),
        )

        self.facade_insulation_exists = FormState(
            self,
            name="facade_insulation_exists",
            form_class=forms.FacadeInsulationForm,
            template_name="partials/facade_insulation_help.html",
        ).transition(
            Switch("facade_insulation_exists").case("exists", "facade_insulation_year").default("end"),
        )

        self.facade_insulation_year = FormState(
            self,
            name="facade_insulation_year",
            form_class=forms.FacadeInsulationYearForm,
        ).transition(
            Next("end"),
        )

        self.end = EndState(self, url="heat:heating")


class HeatingFlow(SidebarNavigationMixin, Flow):
    template_name = "pages/heating.html"
    extra_context = {
        "back_url": "heat:facade",
        "next_includes": "#heating,#heating_hydraulic,#heating_details,#heating_storage",
    }

    def __init__(self):
        super().__init__()
        self.start = FormState(
            self,
            name="heating",
            form_class=forms.HeatingForm,
        ).transition(
            Next("heating_hydraulic"),
        )

        self.heating_hydraulic = FormState(
            self,
            name="heating_hydraulic",
            form_class=forms.HeatingHydraulicForm,
            template_name="partials/heating_hydraulic_help.html",
        ).transition(
            Next("heating_details"),
        )

        self.heating_details = FormState(
            self,
            name="heating_details",
            form_class=forms.HeatingDetailsForm,
        ).transition(
            Next("heating_storage"),
        )

        self.heating_storage = FormState(
            self,
            name="heating_storage",
            form_class=forms.HeatingStorageForm,
            template_name="partials/heating_storage_help.html",
        ).transition(
            Next("end"),
        )

        self.end = EndState(self, url="heat:pv_system")


class PVSystemFlow(SidebarNavigationMixin, Flow):
    template_name = "pages/pv_system.html"
    extra_context = {
        "back_url": "heat:heating",
        "next_includes": "#pv_system,#pv_system_planned,#pv_system_details,#pv_system_battery",
    }

    def __init__(self):
        super().__init__()
        self.start = FormState(
            self,
            name="pv_system",
            form_class=forms.PVSystemForm,
        ).transition(
            Switch("pv_exists").case("doesnt_exist", "pv_system_planned").default("pv_system_details"),
        )

        self.pv_system_planned = FormState(
            self,
            name="pv_system_planned",
            form_class=forms.PVSystemPlannedForm,
        ).transition(
            Next("end"),
        )

        self.pv_system_details = FormState(
            self,
            name="pv_system_details",
            form_class=forms.PVSystemDetailsForm,
            template_name="partials/pv_system_details_help.html",
        ).transition(
            Next("pv_system_battery"),
        )

        self.pv_system_battery = FormState(
            self,
            name="pv_system_battery",
            form_class=forms.PVSystemBatteryForm,
            template_name="partials/pv_system_battery_help.html",
        ).transition(
            Next("end"),
        )

        self.end = EndState(self, url="heat:ventilation_system")


class VentilationSystemFlow(SidebarNavigationMixin, Flow):
    template_name = "pages/ventilation_system.html"
    extra_context = {
        "back_url": "heat:pv_system",
        "next_includes": "#ventilation_system_exists,#ventilation_system_year",
    }

    def __init__(self):
        super().__init__()
        self.start = FormState(
            self,
            name="ventilation_system_exists",
            form_class=forms.VentilationSystemForm,
            template_name="partials/ventilation_system_help.html",
        ).transition(
            Switch("ventilation_system_exists").case("doesnt_exist", "end").default("ventilation_system_year"),
        )

        self.ventilation_system_year = FormState(
            self,
            name="ventilation_system_year",
            form_class=forms.VentilationSystemYearForm,
        ).transition(
            Next("end"),
        )

        self.end = EndState(self, url="heat:intro_renovation")


class RenovationRequestFlow(SidebarNavigationMixin, Flow):
    template_name = "pages/renovation_request.html"
    extra_context = {
        "back_url": "heat:intro_renovation",
        "next_includes": (
            "#primary_heating,#renovation_biomass,#renovation_heatpump,"
            "#renovation_pvsolar,#renovation_solar,#renovation_details"
        ),
    }

    def __init__(self, prefix=None):
        super().__init__(prefix=prefix)
        self.start = FormState(
            self,
            name="primary_heating",
            form_class=forms.RenovationTechnologyForm,
        ).transition(
            Switch("primary_heating")
            .case("bio_mass", "renovation_biomass")
            .case("heat_pump", "renovation_heatpump")
            .case("heating_rod", "renovation_pvsolar")
            .default("renovation_solar"),
        )

        self.renovation_biomass = FormState(
            self,
            name="renovation_biomass",
            form_class=forms.RenovationBioMassForm,
        ).transition(
            Next("renovation_details"),
        )

        self.renovation_heatpump = FormState(
            self,
            name="renovation_heatpump",
            form_class=forms.RenovationHeatPumpForm,
        ).transition(
            Next("renovation_details"),
        )

        self.renovation_pvsolar = FormState(
            self,
            name="renovation_pvsolar",
            form_class=forms.RenovationPVSolarForm,
        ).transition(
            Next("renovation_details"),
        )

        self.renovation_solar = FormState(
            self,
            name="renovation_solar",
            form_class=forms.RenovationSolarForm,
        ).transition(
            Next("renovation_details"),
        )

        self.renovation_details = FormInfoState(
            self,
            name="renovation_details",
            form_class=forms.RenovationRequestForm,
            info_text={"next_button": ("Speichern", "Weiter")},
        ).transition(
            Next("end"),
        )

        self.end = EndState(self, url="heat:renovation_overview")

    def dispatch(self, request, *args, **kwargs):
        # Retrieve the prefix dynamically
        self.prefix = kwargs.get("scenario", self.prefix)
        return super().dispatch(request, *args, **kwargs)


class FinancialSupporFlow(SidebarNavigationMixin, Flow):
    template_name = "pages/financial_support.html"
    extra_context = {
        "back_url": "heat:renovation_request",
        "next_includes": "#financial_support",
        "back_kwargs": "scenario1",
    }

    def __init__(self):
        super().__init__()
        self.start = FormState(
            self,
            name="financial_support",
            form_class=forms.FinancialSupportForm,
            template_name="partials/financial_support_help.html",
        ).transition(
            Next("end"),
        )

        self.end = EndState(self, url="heat:results")
