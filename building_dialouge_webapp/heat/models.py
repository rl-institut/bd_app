from django.db import models
from viewflow.workflow.models import Process


class Roof(models.Model):
    """Model for roof."""

    roof_type = models.CharField(
        max_length=50,
        choices=[
            ("flachdach", "Flachdach"),
            ("satteldach", "Satteldach"),
            ("walmdach", "Walmdach"),
        ],
        blank=True,
    )
    roof_area = models.FloatField(blank=True)
    roof_orientation = models.CharField(max_length=100, blank=True)
    number_roof_windows = models.IntegerField(blank=True)
    roof_usage = models.CharField(max_length=100, blank=True)
    roof_insulation_exists = models.BooleanField(null=True, blank=True)

    def __str__(self):
        if self.pk:
            return f"#{self.roof_type}"
        return super().__str__()


class RoofProcess(Process):
    """
    This model extends the base viewflow `Process` model.

    """

    class Meta:
        proxy = True
        verbose_name_plural = "Roof process"

    def is_flat_roof(self):
        try:
            return self.artifact.roof.roof_type == "Flachdach"
        except Roof.DoesNotExist:
            return None
