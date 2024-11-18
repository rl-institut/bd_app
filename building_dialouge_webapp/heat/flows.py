from abc import abstractmethod
from collections.abc import Callable
from enum import IntEnum
from typing import Any
from typing import Optional

from django.forms import Form
from django.http import HttpResponse
from django.http import QueryDict
from django.shortcuts import reverse
from django.template import Template
from django.template.context_processors import csrf
from django.template.loader import get_template
from django.views.generic import TemplateView
from django_htmx.http import HttpResponseClientRedirect
from django_htmx.http import retarget

from . import forms


class FlowError(Exception):
    """Thrown when a flow fails."""


class StateStatus(IntEnum):
    New = 0  # if state is called the first time
    Set = 1  # if state gets POST request
    Unchanged = 2  # if state has not changed and next state is called
    Changed = 3  # if state is revisited with POST request differing from session


class StateResponse:
    """Base class for holding state content."""

    def __init__(self, content: Any) -> None:
        self.content = content


class HTMLStateResponse(StateResponse):
    """State response holding HTML to be rendered."""

    def __init__(self, html: str) -> None:
        super().__init__(html)


class HTMLResetStateResponse(StateResponse):
    """State response holding HTML in order to reset page content."""

    def __init__(self, html: str) -> None:
        super().__init__(html)


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

    def set(self) -> dict[str, StateResponse]:
        """Sets or updates the state using check_state()."""
        status = self.check_state()
        if status == StateStatus.New:
            return self.response
        if status == StateStatus.Set:
            self.store_state()
            following_states = self.next().set()
        elif status == StateStatus.Unchanged:
            following_states = self.next().set()
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


class EndState(State):
    """
    Last state in a flow

    Can be set explicitly or will be silently set.
    """

    def __init__(self, flow: "Flow", url: str, label: str = "end"):
        super().__init__(flow, name="", label=label)
        self.url = url

    def set(self) -> dict[str, StateResponse]:
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
        return self.flow.request.GET

    @property
    def response(self) -> dict[str, StateResponse]:
        context = self.get_context_data()
        return {self.name: HTMLStateResponse(get_template(self.template_name).render(context))}

    @property
    def reset_response(self) -> dict[str, StateResponse]:
        """Return HTML including HTMX swap-oob in order to remove/reset HTML for current target."""
        return {self.name: HTMLResetStateResponse(f'<div id="{self.name}" hx-swap-oob="innerHTML"></div>')}


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

    @property
    def response(self) -> dict[str, StateResponse]:
        """Renders the form with data from the session if available; otherwise, renders a blank form.
        Describe what template_name can do and that its used for infotext
        """
        status = self.check_state()
        data = None if status == StateStatus.New else self.flow.request.session.get("django_htmx_flow", {})
        context = self.get_context_data()
        if isinstance(context, QueryDict):
            context = context.dict()
        if self.template_name is None:
            # render form without helptext
            csrf_token = csrf(self.flow.request)["csrf_token"]
            return {
                self.name: HTMLStateResponse(
                    f"""
                    <div class="step-question">
                        <div class="step-container">
                            <div class="main">
                                <form hx-post="" hx-trigger="change">
                                    <input type="hidden" name="csrfmiddlewaretoken" value="{csrf_token}">
                                    {self.form_class(data).render()}
                                </form>
                            </div>
                        </div>
                        <div class="help">
                        </div>
                    </div>
                    """,
                ),
            }
        context["form"] = self.form_class(data)
        return {self.name: HTMLStateResponse(get_template(self.template_name).render(context))}

    def store_state(self):
        """Stores each form field's input value to the session."""
        if self.flow.request.method == "POST":
            session_data = self.flow.request.session.get("django_htmx_flow", {})
            form_instance = self.form_class(self.flow.request.POST)
            if form_instance.is_valid():
                form_data = form_instance.cleaned_data
                for field_name, value in form_data.items():
                    session_data[field_name] = value
                self.flow.request.session["django_htmx_flow"] = session_data

    def remove_state(self):
        """Removes each form field's stored value from the session."""
        session_data = self.flow.request.session.get("django_htmx_flow", {})
        form_instance = self.form_class()
        for field in form_instance.fields:
            if field in session_data:
                del session_data[field]
        self.flow.request.session["django_htmx_flow"] = session_data

    def check_state(self) -> StateStatus:
        """Checks the state status using all form fields."""
        session_data = self.flow.request.session.get("django_htmx_flow", {})
        form_fields = self.form_class().fields

        if all(field not in self.flow.request.POST and field not in session_data for field in form_fields):
            return StateStatus.New
        if any(field in self.flow.request.POST and field not in session_data for field in form_fields):
            return StateStatus.Set
        if any(
            field in self.flow.request.POST and self.flow.request.POST[field] != session_data.get(field)
            for field in form_fields
        ):
            return StateStatus.Changed
        return StateStatus.Unchanged


class FormInfoState(FormState):
    def __init__(  # noqa: PLR0913
        self,
        flow: "Flow",
        name: str,
        form_class: type[Form],
        info_text: str,
        template_name: str | None = None,
        label: str | None = None,
    ):
        super().__init__(flow, name, form_class, template_name, label)
        self.info_text = info_text

    @property
    def response(self) -> dict[str, StateResponse]:
        form_response = {"info": HTMLStateResponse(f'<div id="info" hx-swap-oob="innerHTML">{self.info_text}</div>')}
        form_response.update(**super().response)
        return form_response

    @property
    def reset_response(self) -> dict[str, StateResponse]:
        form_response = {"info": HTMLStateResponse('<div id="info" hx-swap-oob="innerHTML"></div>')}
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
        session_data = self.flow.request.session.get("django_htmx_flow", {})
        if key in session_data:
            return session_data[key]
        if key in self.flow.request.POST:
            return self.flow.request.POST[key]
        error_msg = f"Could not find lookup {key=} in request or session."
        raise FlowError(error_msg)


class Flow(TemplateView):
    def __init__(self):
        self.start = None
        self.end = None
        super().__init__()

    def dispatch(self, request, *args, **kwargs) -> HttpResponse:
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
            for name, state_response in state_partials.items():
                html_response += state_response.content
                if isinstance(state_response, HTMLStateResponse):
                    target = name
            response = HttpResponse(html_response, content_type="text/html")
            return retarget(response, f"#{target}")

        # Traditional request
        context = self.get_context_data(**kwargs)
        # Remove reset responses from partials
        state_partials = {
            name: response
            for name, response in state_partials.items()
            if not isinstance(response, (HTMLResetStateResponse, RedirectStateResponse))
        }
        context.update(state_partials)
        # Fill template with state partials by adding them with their target_id
        return self.render_to_response(context)


class BuildingTypeFlow(Flow):
    template_name = "pages/building_type.html"

    def __init__(self):
        super().__init__()
        self.start = FormState(
            self,
            name="building_type",
            form_class=forms.BuildingTypeForm,
        ).transition(
            Next("monument_protection"),
        )

        self.monument_protection = FormState(
            self,
            name="monument_protection",
            form_class=forms.BuildingTypeProtectionForm,
        ).transition(
            Switch("monument_protection").case("yes", "dead_end_monument_protection").default("end"),
        )
        # TODO: make dead end popup or view and update url
        self.dead_end_monument_protection = EndState(self, url="heat:home")

        self.end = EndState(self, url="heat:building_data")


class BuildingDataFlow(Flow):
    template_name = "pages/building_data.html"

    def __init__(self):
        super().__init__()
        self.start = FormInfoState(
            self,
            name="building_data",
            form_class=forms.BuildingDataForm,
            info_text="Wohneinheiten: Die Anzahl der Wohneinheiten ...",
        ).transition(
            Next("end"),
        )

        self.end = EndState(self, url="heat:cellar")


class CellarFlow(Flow):
    template_name = "pages/cellar.html"

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

        self.end = EndState(self, url="heat:roof")


class RoofFlow(Flow):
    template_name = "pages/roof.html"

    def __init__(self):
        super().__init__()
        self.start = FormState(
            self,
            name="roof_type",
            form_class=forms.RoofTypeForm,
            template_name="partials/roof_info.html",
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
        self.end = EndState(self, url="heat:home")
