from typing import Any

from viewflow import this
from viewflow.workflow import flow

from . import views
from .models import RoofProcess


class RoofProcessFlow(flow.Flow):
    process_class = RoofProcess

    # Start the flow with the RoofTypeForm
    start = flow.Start(views.RoofTypeView.as_view()).Next(this.split_roof_type)

    # Split the flow based on roof_type selected
    split_roof_type = (
        flow.Switch()
        .Case(this.roof_insulation, lambda act: act.process.roof_type == "Flachdach")
        .Default(this.roof_details)
    )

    roof_insulation = flow.View(views.RoofInsulationView.as_view()).Next(this.end)

    roof_details = flow.View(views.RoofDetailsView.as_view()).Next(this.roof_usage)

    roof_usage = flow.View(views.RoofUsageView.as_view()).Next(this.roof_insulation)

    end = flow.End()

    def has_view_permission(self, user: Any, obj: Any | None = None) -> bool:
        return True


class RoofViewset(flow.FlowViewset):
    def has_view_permission(self, user, obj=None):
        return True
