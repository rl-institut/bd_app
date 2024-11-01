from abc import abstractmethod
from collections.abc import Callable
from collections.abc import Iterable
from typing import Any
from typing import Optional

from django.forms import Form
from django.http import HttpResponse
from django.template import Template
from django.views.generic import TemplateView
from django.views.generic.edit import ContextMixin
from django.views.generic.edit import FormMixin
from django.views.generic.edit import TemplateResponseMixin


class TransitionError(Exception):
    """Thrown when a transition fails."""


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
            return None
        return self._transition.follow(self)

    @property
    def data(self) -> dict:
        return self.flow.data

    def render(self, request, *args, **kwargs) -> HttpResponse:
        return HttpResponse(self.response)


class TemplateState(TemplateResponseMixin, ContextMixin):
    def __init__(
        self,
        flow: "Flow",
        target_id: str,
        template_name: Template | str,
        label: str | None = None,
    ):
        self.template_name = template_name
        super().__init__(flow, target_id, label)

    def render(self, request, *args, **kwargs) -> HttpResponse:
        context = self.get_context_data(**kwargs)
        self.request = request
        return self.render_to_response(context)


class FormState(TemplateState, FormMixin):
    def __init__(  # noqa: PLR0913
        self,
        flow: "Flow",
        target_id: str,
        form_class: Form,
        template_name: str | None = None,
        label: str | None = None,
    ):
        super().__init__(flow, target_id, template_name, label)
        self.form_class = form_class

    def render_to_response(self, context, **response_kwargs) -> HttpResponse:
        if self.template_name is None:
            return HttpResponse(str(context["form"]))
        return super().render_to_response(context, **response_kwargs)


class Transition:
    def __init__(self):
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
    def __init__(self, fct: Callable):
        super().__init__()
        self.fct = fct
        self.cases = {}

    def case(self, value: Any, state_name: str) -> "Switch":
        self.cases[value] = state_name
        return self

    def default(self, state_name: str) -> "Switch":
        self.cases["_default"] = state_name
        return self

    def follow(self, state: "State") -> "State":
        result = self.fct(state)
        if result in self.cases:
            return self._state(self.cases[result])
        if "_default" in self.cases:
            return self._state(self.cases["_default"])
        error_msg = f"No option for result '{result}' found, no default given."
        raise TransitionError(error_msg)


class Flow(TemplateView):
    def __init__(self):
        self.data = {}
        self.start = None
        self.end = None
        super().__init__()

    def run(self, data) -> Iterable["State"]:
        self.data = data
        current_node = self.start
        while True:
            yield current_node
            current_node = current_node.next()
            if current_node is None:
                break

    def dispatch(self, request, *args, **kwargs):
        state: State = next(self.run(request))
        return state.render(request, *args, **kwargs)


class RoofFlow(Flow):
    def __init__(self):
        super().__init__()
        self.start = State(
            self,
            target_id="roof_type",
            label="start",
            response="start",
        ).transition(
            Switch(lambda state: state.data["roof_type"])
            .case("a", "a")
            .case("b", "b")
            .default("c"),
        )
        self.a = State(self, target_id="a", label="a", response="htmx.html")
        self.b = State(self, target_id="b", label="b", response="b")
        self.c = State(self, target_id="c", label="c", response="c")


# TODO: Apply templates
# TODO: Implement reset()
#   check if State is fresh
