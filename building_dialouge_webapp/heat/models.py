"""Module to set up DB models for building dialouge."""

from django.contrib.postgres.fields import ArrayField
from django.db import models


class Solarthermal(models.Model):
    """Model to hold heat and load timeseries for different setups of solarthermal component."""

    type = models.CharField()  # to distinguish between heat and load demand
    temperature = models.IntegerField()
    elevation_angle = models.IntegerField()
    direction_angle = models.IntegerField()
    profile = ArrayField(models.FloatField())

    class Meta:
        unique_together = ("type", "temperature", "elevation_angle", "direction_angle")

    def __str__(self):
        return f"Solarthermal ({self.type}, {self.temperature}, {self.elevation_angle}, {self.direction_angle})"


class Photovoltaic(models.Model):
    """Model to hold timeseries for different setups of photovoltaic component."""

    elevation_angle = models.IntegerField()
    direction_angle = models.IntegerField()
    profile = ArrayField(models.FloatField())

    class Meta:
        unique_together = ("elevation_angle", "direction_angle")

    def __str__(self):
        return f"Photovoltaic ({self.elevation_angle}, {self.direction_angle})"
