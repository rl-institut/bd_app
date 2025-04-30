from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable

    from django.forms import Form
    from django.template import Template

from enum import IntEnum
from typing import Any

from django.http import HttpResponse
from django.shortcuts import reverse
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
        target (str): The identifier for the HTML target associated with this state.
        label (str, optional): An optional label for the state.
    """

    def __init__(
        self,
        flow: Flow,
        target: str,
        label: str | None = None,
        lookup: str | None = None,
    ):
        self.flow = flow
        self.target = target
        self.label = label
        self._transition = None
        self.lookup = lookup if lookup else target
        super().__init__()

    def transition(self, transition: Transition) -> State:
        """Assigns a transition to the state and sets the flow context."""
        transition.flow = self.flow
        self._transition = transition
        return self

    def next(self) -> State | None:
        """Determines the next state by following the current transition."""
        if self._transition is None:
            if isinstance(self.flow.end, EndState):
                return self.flow.end
            error_msg = f"No next state or end state defined for state '{self.target}'."
            raise FlowError(error_msg)
        return self._transition.follow(self)

    def store_state(self):
        """Saves the current state's input value to the session if the request method is POST."""
        if self.flow.request.method == "POST":
            value = self.flow.request.POST[self.lookup]
            session_data = self.flow.request.session.get("django_htmx_flow", {})
            session_data[self.lookup] = value
            self.flow.request.session["django_htmx_flow"] = session_data

    def remove_state(self):
        """Removes the current state's value from the session if it exists."""
        session_data = self.flow.request.session.get("django_htmx_flow", {})
        if self.lookup in session_data:
            del session_data[self.lookup]
            self.flow.request.session["django_htmx_flow"] = session_data

    def check_state(self) -> StateStatus:
        """Checks the status of the current state based on the session and POST data."""
        session_data = self.flow.request.session.get("django_htmx_flow", {})
        if self.lookup not in self.flow.request.POST and self.lookup not in session_data:
            return StateStatus.New
        if self.lookup in self.flow.request.POST and self.lookup not in session_data:
            return StateStatus.Set
        if self.lookup in self.flow.request.POST and self.flow.request.POST[self.lookup] != session_data.get(
            self.lookup,
        ):
            return StateStatus.Changed
        return StateStatus.Unchanged

    def response(self, *, swap=False) -> dict[str, StateResponse]:
        """Return response of current state."""
        return {self.target: StateResponse(self.target)}

    def reset_response(self) -> dict[str, StateResponse]:
        """Return response of current state in case of reset."""
        return {self.target: StateResponse(self.target)}

    def error_response(self) -> dict[str, StateResponse]:
        """Return response of current state."""
        return {self.target: StateResponse("Something went wrong.")}

    def set(
        self,
        previous_state: StateStatus = StateStatus.Unchanged,
    ) -> dict[str, StateResponse]:
        """Sets or updates the state using check_state()."""
        status = self.check_state()
        if status == StateStatus.New:
            return self.response()
        if status == StateStatus.Error:
            self.remove_state()
            following_states = self.error_response()
            following_states.update(self.next().reset())
            return following_states
        if status == StateStatus.Set:
            self.store_state()
            # This line allows clearing of form errors after sending valid form and
            # assures rendering of forms which have only non-required fields
            following_states = self.response(swap=True)
            following_states.update(self.next().set(status))
        elif status == StateStatus.Unchanged:
            following_states = self.next().set(status)
        elif status == StateStatus.Changed:
            following_states = self.next().reset()
            self.store_state()
            following_states.update(self.response(swap=True))
            following_states.update(self.next().set(status))
        else:
            error_msg = f"Unknown state status '{status}'."
            raise FlowError(error_msg)

        if self.flow.request.htmx:
            return following_states
        following_states.update(self.response())
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
        following_states.update(self.reset_response())
        return following_states

    @property
    def data(self) -> dict[str, Any]:
        session_data = self.flow.request.session.get("django_htmx_flow", {})
        if self.lookup in session_data:
            return {self.lookup: session_data[self.lookup]}
        return {}


class EndState(State):
    """
    Last state in a flow

    Can be set explicitly or will be silently set.
    """

    def __init__(self, flow: Flow, url: str, label: str = "end"):
        super().__init__(flow, target="", label=label)
        self.url = url

    def set(
        self,
        previous_state: StateStatus = StateStatus.Unchanged,
    ) -> dict[str, StateResponse]:
        return self.response()

    def reset(self) -> dict[str, StateResponse]:
        return self.reset_response()

    def response(self, *, swap=False) -> dict[str, StateResponse]:
        """Return response of current state."""
        return {self.target: RedirectStateResponse(self.url)}

    def reset_response(self) -> dict[str, StateResponse]:
        """Return response of current state."""
        return {}


class TemplateState(State):
    extra_context = {}

    def __init__(  # noqa: PLR0913
        self,
        flow: Flow,
        target: str,
        template_name: Template | str,
        lookup: str | None = None,
        label: str | None = None,
        context: dict[str, Any] | None = None,
        reset_template_name: str | None = None,
        reset_context: dict[str, Any] | None = None,
    ):
        self.template_name = template_name
        self.reset_template_name = reset_template_name
        self.reset_context = reset_context
        self.context = context or {}
        super().__init__(flow, target, label, lookup)

    def get_context_data(self):
        context = self.context
        if self.extra_context is not None:
            context.update(self.extra_context)
        return context

    def response(self, *, swap=False) -> dict[str, StateResponse]:
        context = self.get_context_data()
        response_format = SwapHTMLStateResponse if swap else HTMLStateResponse
        return {
            self.target: response_format(
                get_template(self.template_name).render(context),
            ),
        }

    def reset_response(self) -> dict[str, StateResponse]:
        """Return HTML including HTMX swap-oob in order to remove/reset HTML for current target."""
        if self.reset_template_name:
            return {
                self.target: SwapHTMLStateResponse(
                    f'<div id="{self.target}" hx-swap-oob="innerHTML">'
                    f"{get_template(self.reset_template_name).render(self.reset_context)}"
                    f"</div>",
                ),
            }
        return {
            self.target: SwapHTMLStateResponse(
                f'<div id="{self.target}" hx-swap-oob="innerHTML"></div>',
            ),
        }


class StopState(TemplateState):
    def __init__(self, flow, lookup: str, next_botton_text: str = "Weiter"):
        super().__init__(
            flow=flow,
            target="next_button",
            template_name="partials/next_button.html",
            context={
                "hx_vals": f'{{"{lookup}": "True"}}',
                "next_btn_text": next_botton_text,
            },
            reset_template_name="partials/next_button.html",
            reset_context={
                "next_disabled": True,
                "next_btn_text": next_botton_text,
            },
            lookup=lookup,
        )


class FormState(TemplateState):
    """
    Represents a state with a form within a flow, handling storage, and
    change detection of individual form field values in the session.

    Attributes:
        flow (Flow): The flow instance to which this state belongs.
        target (str): The identifier for the HTML target associated with this state.
        form_class (type[Form]): Form class associated with the current state.
        template_name (str | None): Optional template name for rendering the form.
        label (str, optional): An optional label for the state.
    """

    def __init__(  # noqa: PLR0913
        self,
        flow: Flow,
        target: str,
        form_class: type[forms.ValidationForm],
        template_name: str | None = None,
        label: str | None = None,
    ):
        super().__init__(flow, target, template_name, label)
        self.form_class = form_class

    def _init_form(self, data: dict[str, Any] | None = None) -> Form:
        if "request" in self.form_class.__init__.__code__.co_varnames:
            return self.form_class(
                data,
                prefix=self.flow.prefix,
                request=self.flow.request,
            )
        return self.form_class(data, prefix=self.flow.prefix)

    def _render_form(self, data) -> str:
        context = self.get_context_data()
        if self.template_name is None:
            csrf_token = csrf(self.flow.request)["csrf_token"]
            form_instance = self._init_form(data)
            return f'<input type="hidden" name="csrfmiddlewaretoken" value="{csrf_token}">\n {form_instance.as_div()}'
        form_instance = self._init_form(data)
        context["form"] = form_instance
        return get_template(self.template_name).render(
            context,
            request=self.flow.request,
        )

    def response(self, *, swap=False) -> dict[str, StateResponse]:
        """Renders the form with data from the session if available; otherwise, renders a blank form."""
        status = self.check_state()
        data = None if status == StateStatus.New else self.flow.request.session.get("django_htmx_flow", {})
        content = self._render_form(data)
        if swap:
            return {
                self.target: SwapHTMLStateResponse(
                    f'<div id="{self.target}" hx-swap-oob="innerHTML">{content}</div>',
                ),
            }
        return {self.target: HTMLStateResponse(content)}

    def error_response(self) -> dict[str, StateResponse]:
        """Renders the form with incorrect data from the request."""
        return {self.target: HTMLStateResponse(self._render_form(self.flow.request.POST))}

    def store_state(self):
        """Stores each form field's input value to the session."""
        if self.flow.request.method == "POST":
            session_data = self.flow.request.session.get("django_htmx_flow", {})
            form_instance = self._init_form(self.flow.request.POST)
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
        form_instance = self._init_form()
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
        form = self._init_form(self.flow.request.POST)

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
        form = self._init_form(session_data)
        if form.is_valid():
            return form.cleaned_data
        error_msg = f"Invalid data in flow '{self.target}': {form.errors}."
        raise FlowError(error_msg)


class Transition:
    def __init__(self):
        # These are set once Transition is added to state
        self.flow = None

    @abstractmethod
    def follow(self, state: State) -> State:
        """Must be implemented by subclasses."""

    def _state(self, state_name) -> State:
        return getattr(self.flow, state_name)


class Next(Transition):
    def __init__(self, next_state: str):
        super().__init__()
        self.next_state = next_state

    def follow(self, state: State) -> State:
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

    def case(self, value: Any, state_name: str) -> Switch:
        self.cases[value] = state_name
        return self

    def default(self, state_name: str) -> Switch:
        self.cases["_default"] = state_name
        return self

    def follow(self, state: State) -> State:
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

    def default_switch_fct(self, state: State) -> Any:
        key = self.lookup if isinstance(self.lookup, str) else state.target
        key = key if self.flow.prefix is None else f"{self.flow.prefix}-{key}"
        session_data = self.flow.request.session.get("django_htmx_flow", {})
        if key in session_data:
            return session_data[key]
        if key in self.flow.request.POST:
            return self.flow.request.POST[key]
        error_msg = f"Could not find lookup {key=} in request or session."
        raise FlowError(error_msg)


class Flow(TemplateView):
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
        "back_url": "heat:intro_inventory",
        "next_disabled": True,
    }

    def __init__(self):
        super().__init__()
        self.start = FormState(
            self,
            target="building_type",
            form_class=forms.BuildingTypeForm,
            template_name="partials/building_type_help.html",
        ).transition(
            Next("building_details"),
        )

        self.building_details = FormState(
            self,
            target="building_details",
            form_class=forms.BuildingDetailsForm,
        ).transition(
            Next("monument_protection"),
        )

        self.monument_protection = FormState(
            self,
            target="monument_protection",
            form_class=forms.BuildingTypeProtectionForm,
            template_name="partials/building_type_protection_help.html",
        ).transition(
            Switch("monument_protection").case("yes", "dead_end_stop").default("stop"),
        )

        self.dead_end_stop = StopState(
            self,
            lookup="building_type_done",
            next_botton_text="Speichern",
        ).transition(Next("dead_end_monument_protection"))

        self.dead_end_monument_protection = EndState(
            self,
            url="heat:dead_end_monument_protection",
        )

        self.stop = StopState(
            self,
            lookup="building_type_done",
            next_botton_text="Speichern",
        ).transition(Next("end"))
        self.end = EndState(self, url="heat:insulation")


class InsulationFlow(SidebarNavigationMixin, Flow):
    template_name = "pages/insulation.html"
    extra_context = {
        "back_url": "heat:building_type",
        "next_disabled": True,
    }

    def __init__(self):
        super().__init__()
        self.start = FormState(
            self,
            target="insulation",
            form_class=forms.InsulationForm,
        ).transition(
            Next("stop"),
        )

        self.stop = StopState(
            self,
            lookup="insulation_done",
            next_botton_text="Speichern",
        ).transition(Next("end"))
        self.end = EndState(self, url="heat:heating")


class HeatingFlow(SidebarNavigationMixin, Flow):
    template_name = "pages/heating.html"
    extra_context = {
        "back_url": "heat:insulation",
        "next_disabled": True,
    }

    def __init__(self):
        super().__init__()
        self.start = FormState(
            self,
            target="heating_source",
            form_class=forms.HeatingSourceForm,
        ).transition(
            Next("heating_year"),
        )

        self.heating_year = FormState(
            self,
            target="heating_year",
            form_class=forms.HeatingYearForm,
        ).transition(
            Next("solar_thermal_exists"),
        )

        self.solar_thermal_exists = FormState(
            self,
            target="solar_thermal_exists",
            form_class=forms.HeatingSolarExistsForm,
            template_name="partials/heating_solar_help.html",
        ).transition(
            Switch("solar_thermal_exists").case("doesnt_exist", "stop").default("solar_thermal_area"),
        )

        self.solar_thermal_area = FormState(
            self,
            target="solar_thermal_area",
            form_class=forms.HeatingSolarAreaForm,
        ).transition(
            Next("stop"),
        )

        self.stop = StopState(
            self,
            lookup="hotwater_heating_done",
            next_botton_text="Speichern",
        ).transition(Next("end"))
        self.end = EndState(self, url="heat:hotwater")


class HotwaterFlow(SidebarNavigationMixin, Flow):
    template_name = "pages/hotwater.html"
    extra_context = {
        "back_url": "heat:heating",
        "next_disabled": True,
    }

    def __init__(self):
        super().__init__()

        self.start = FormState(
            self,
            target="hotwater_supply",
            form_class=forms.HotwaterSupplyForm,
        ).transition(
            Next("heating_storage_exists"),
        )

        self.heating_storage_exists = FormState(
            self,
            target="heating_storage_exists",
            form_class=forms.HeatingStorageExistsForm,
        ).transition(
            Switch("heating_storage_exists").case("exists", "heating_storage_capacity").default("stop"),
        )

        self.heating_storage_capacity = FormState(
            self,
            target="heating_storage_capacity",
            form_class=forms.HeatingStorageCapacityForm,
            template_name="partials/heating_storage_help.html",
        ).transition(
            Next("stop"),
        )

        self.stop = StopState(
            self,
            lookup="heating_done",
            next_botton_text="Speichern",
        ).transition(Next("end"))
        self.end = EndState(self, url="heat:roof")


class RoofFlow(SidebarNavigationMixin, Flow):
    template_name = "pages/roof.html"
    extra_context = {
        "back_url": "heat:hotwater",
        "next_disabled": True,
    }

    def __init__(self):
        super().__init__()
        self.start = FormState(
            self,
            target="flat_roof",
            form_class=forms.RoofTypeForm,
            template_name="partials/roof_help.html",
        ).transition(
            Switch("flat_roof").case("exists", "stop").default("roof_orientation"),
        )
        self.roof_orientation = FormState(
            self,
            target="roof_orientation",
            form_class=forms.RoofOrientationForm,
            template_name="partials/roof_orientation_help.html",
        ).transition(
            Next("roof_inclination_known"),
        )

        self.roof_inclination_known = FormState(
            self,
            target="roof_inclination_known",
            form_class=forms.RoofInclinationKnownForm,
        ).transition(
            Switch("roof_inclination_known").case("known", "roof_inclination").default("stop"),
        )

        self.roof_inclination = FormState(
            self,
            target="roof_inclination",
            form_class=forms.RoofInclinationForm,
            template_name="partials/roof_inclination_help.html",
        ).transition(Next("stop"))

        self.stop = StopState(
            self,
            lookup="roof_done",
            next_botton_text="Speichern",
        ).transition(Next("end"))
        self.end = EndState(self, url="heat:pv_system")


class PVSystemFlow(SidebarNavigationMixin, Flow):
    template_name = "pages/pv_system.html"
    extra_context = {
        "back_url": "heat:roof",
        "next_disabled": True,
    }

    def __init__(self):
        super().__init__()
        self.start = FormState(
            self,
            target="pv_system",
            form_class=forms.PVSystemForm,
        ).transition(
            Switch("pv_exists").case("doesnt_exist", "stop").default("pv_capacity"),
        )

        self.pv_capacity = FormState(
            self,
            target="pv_capacity",
            form_class=forms.PVSystemCapacityForm,
            template_name="partials/pv_system_capacity_help.html",
        ).transition(
            Next("pv_system_battery_exists"),
        )

        self.pv_system_battery_exists = FormState(
            self,
            target="pv_system_battery_exists",
            form_class=forms.PVSystemBatteryExistsForm,
        ).transition(
            Switch("battery_exists").case("doesnt_exist", "stop").default("pv_battery_capacity_known"),
        )

        self.pv_battery_capacity_known = FormState(
            self,
            target="pv_battery_capacity_known",
            form_class=forms.PVSystemBatteryCapacityKnownForm,
        ).transition(
            Switch("battery_capacity_known").case("known", "pv_system_battery").default("stop"),
        )

        self.pv_system_battery = FormState(
            self,
            target="pv_system_battery",
            form_class=forms.PVSystemBatteryCapacityForm,
            template_name="partials/pv_system_battery_help.html",
        ).transition(
            Next("stop"),
        )

        self.stop = StopState(
            self,
            lookup="v",
            next_botton_text="Speichern",
        ).transition(Next("end"))
        self.end = EndState(self, url="heat:intro_renovation")


class RenovationRequestFlow(SidebarNavigationMixin, Flow):
    template_name = "pages/renovation_request.html"
    extra_context = {
        "back_url": "heat:renovation_overview",
        "next_disabled": True,
    }

    def __init__(self, prefix=None):
        super().__init__(prefix=prefix)
        self.start = FormState(
            self,
            target="primary_heating",
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
            target="renovation_biomass",
            form_class=forms.RenovationBioMassForm,
        ).transition(
            Next("renovation_details"),
        )

        self.renovation_heatpump = FormState(
            self,
            target="renovation_heatpump",
            form_class=forms.RenovationHeatPumpForm,
        ).transition(
            Next("renovation_details"),
        )

        self.renovation_pvsolar = FormState(
            self,
            target="renovation_pvsolar",
            form_class=forms.RenovationPVSolarForm,
        ).transition(
            Next("renovation_details"),
        )

        self.renovation_solar = FormState(
            self,
            target="renovation_solar",
            form_class=forms.RenovationSolarForm,
        ).transition(
            Next("renovation_details"),
        )

        self.renovation_details = FormState(
            self,
            target="renovation_details",
            form_class=forms.RenovationRequestForm,
        ).transition(
            Next("stop"),
        )

        self.stop = StopState(
            self,
            lookup=f"{prefix}-renovation_request_done",
            next_botton_text="Speichern",
        ).transition(
            Next("end"),
        )
        self.end = EndState(self, url="heat:renovation_overview")

    def dispatch(self, request, *args, **kwargs):
        # Retrieve the prefix dynamically
        self.prefix = kwargs.get("scenario", self.prefix)
        return super().dispatch(request, *args, **kwargs)


class FinancialSupportFlow(SidebarNavigationMixin, Flow):
    template_name = "pages/financial_support.html"
    extra_context = {
        "back_url": "heat:renovation_overview",
        "next_disabled": False,
    }

    def __init__(self):
        super().__init__()
        self.start = FormState(
            self,
            target="financial_support",
            form_class=forms.FinancialSupportForm,
            template_name="partials/financial_support_help.html",
        ).transition(
            Next("stop"),
        )
        self.stop = StopState(
            self,
            lookup="financial_support_done",
            next_botton_text="Speichern",
        ).transition(
            Next("end"),
        )
        self.end = EndState(self, url="heat:optimization_start")
