from abc import abstractmethod
from collections.abc import Callable
from enum import IntEnum
from typing import Any
from typing import Optional

from django.forms import ChoiceField
from django.forms import Form
from django.forms import IntegerField
from django.http import HttpResponse
from django.template import Template
from django.template.context_processors import csrf
from django.template.loader import get_template
from django.views.generic import TemplateView
from django_htmx.http import retarget


class RoofTypeForm(Form):
    roof_type = ChoiceField(
        label="Dachform",
        choices=(
            ("flat", "Flachdach"),
            ("spitz", "Spitzdach"),
            ("other", "Andere Dachform"),
        ),
    )


class RoofAreaForm(Form):
    roof_area = IntegerField(label="Dachfläche")


class FlowError(Exception):
    """Thrown when a flow fails."""


class StateStatus(IntEnum):
    New = 0  # if state is called the first time
    Set = 1  # if state gets POST request
    Unchanged = 2  # if state has not changed and next state is called
    Changed = 3  # if state is revisited with POST request differing from session


class State:
    def __init__(
        self,
        flow: "Flow",
        target_id: str,
        response: str,
        label: str | None = None,
    ):
        self.flow = flow
        self.target_id = target_id
        self.label = label
        self._transition = None
        self.response = response
        super().__init__()

    def transition(self, transition: "Transition") -> "State":
        transition.flow = self.flow
        self._transition = transition
        return self

    def next(self) -> Optional["State"]:
        if self._transition is None:
            return EndState(self.flow)
        return self._transition.follow(self)

    def render(self) -> str:
        """Render HTML for current target."""
        return self.response

    def render_reset(self) -> str:
        """Return HTML including HTMX swap-oob in order to remove/reset HTML for current target."""
        return f'<div id="{self.target_id}" hx-swap-oob="innerHTML"></div>'

    def store_state(self):
        if self.flow.request.method == "POST":
            value = self.flow.request.POST[self.target_id]
            self.flow.request.session[self.target_id] = value

    def remove_state(self):
        if self.target_id in self.flow.request.session:
            del self.flow.request.session[self.target_id]

    def check_state(self) -> StateStatus:
        if self.target_id not in self.flow.request.POST and self.target_id not in self.flow.request.session:
            return StateStatus.New
        if self.target_id in self.flow.request.POST and self.target_id not in self.flow.request.session:
            return StateStatus.Set
        if (
            self.target_id in self.flow.request.POST
            and self.flow.request.POST[self.target_id] != self.flow.request.session[self.target_id]
        ):
            return StateStatus.Changed
        return StateStatus.Unchanged

    def set(self) -> dict[str, str]:
        status = self.check_state()
        if status == StateStatus.New:
            return {self.target_id: self.render()}
        if status == StateStatus.Set:
            self.store_state()
            following_states = self.next().set()
            following_states[self.target_id] = self.render()
            return following_states
        if status == StateStatus.Unchanged:
            following_states = self.next().set()
            following_states[self.target_id] = self.render()
            return following_states
        if status == StateStatus.Changed:
            following_states = self.next().reset()
            self.store_state()
            next_state = self.next()
            if self.flow.request.htmx:
                return {
                    next_state.target_id: next_state.render()
                    + "\n".join(v for k, v in following_states.items() if k != next_state.target_id),
                    self.target_id: self.render(),
                }
            return {
                next_state.target_id: next_state.render(),
                self.target_id: self.render(),
            }
        error_msg = f"Unknown state status '{status}'."
        raise FlowError(error_msg)

    def reset(self):
        """Reset current state and following."""
        following_node = self.next()
        self.remove_state()
        following_states = {} if following_node is None else following_node.reset()
        following_states[self.target_id] = self.render_reset()
        return following_states


class EndState(State):
    """
    Last state in a flow

    Can be set explicitly or will be silently set.
    """

    def __init__(self, flow: "Flow", label: str = "end"):
        super().__init__(flow, target_id="", response="", label=label)

    def set(self) -> dict[str, str]:
        return {}

    def reset(self) -> dict[str, str]:
        return {}


class TemplateState(State):
    def __init__(
        self,
        flow: "Flow",
        target_id: str,
        template_name: Template | str,
        label: str | None = None,
    ):
        self.template_name = template_name
        super().__init__(flow, target_id, label)

    def get_context_data(self):
        return self.flow.request.GET

    def render(self) -> str:
        context = self.get_context_data()
        return get_template(self.template_name).render(context)


class FormState(TemplateState):
    def __init__(  # noqa: PLR0913
        self,
        flow: "Flow",
        target_id: str,
        form_class: type[Form],
        template_name: str | None = None,
        label: str | None = None,
    ):
        super().__init__(flow, target_id, template_name, label)
        self.form_class = form_class

    def render(self) -> str:
        status = self.check_state()
        data = None if status == StateStatus.New else self.flow.request.session
        context = self.get_context_data()
        if self.template_name is None:
            csrf_token = csrf(self.flow.request)["csrf_token"]
            return (
                f'<form hx-post="" hx-trigger="change">'
                f'<input type="hidden" name="csrfmiddlewaretoken" value="{csrf_token}">'
                f"{self.form_class(data).render()}"
                f"</form>"
            )
        context["form"] = self.form_class(data)
        return get_template(self.template_name).render(context)


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
        key = self.lookup if isinstance(self.lookup, str) else state.target_id
        if key in self.flow.request.session:
            return self.flow.request.session[key]
        if key in self.flow.request.POST:
            return self.flow.request.POST[key]
        error_msg = f"Could not find lookup {key=} in request or session."
        raise FlowError(error_msg)


class Flow(TemplateView):
    def __init__(self):
        self.start = None
        self.end = EndState(self)
        super().__init__()

    def dispatch(self, request, *args, **kwargs) -> HttpResponse:
        state_partials = self.start.set()

        if request.htmx:
            target = next(iter(state_partials.keys()))
            content = next(iter(state_partials.values()))
            response = HttpResponse(content, content_type="text/html")
            return retarget(response, f"#{target}")

        # Traditional request
        context = self.get_context_data(**kwargs)
        context.update(state_partials)
        # Fill template with state partials by adding them with their target_id
        return self.render_to_response(context)


class RoofFlow(Flow):
    template_name = "pages/roof.html"

    def __init__(self):
        super().__init__()
        self.start = FormState(
            self,
            target_id="roof_type",
            form_class=RoofTypeForm,
        ).transition(
            Switch("roof_type").case("flat", "flat_roof").case("spitz", "spitz").default("other"),
        )
        self.flat_roof = FormState(self, target_id="roof_area", form_class=RoofAreaForm)
        self.spitz = State(self, target_id="spitz", response="Spitzdach!")
        self.other = State(self, target_id="other", response="Anderes Dach")
