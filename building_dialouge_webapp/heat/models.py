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


class Load(models.Model):
    """Model to hold timeseries for different setups of load component."""

    number_people = models.IntegerField()
    eec = models.IntegerField()
    profile = ArrayField(models.FloatField())

    class Meta:
        unique_together = ("number_people", "eec")

    def __str__(self):
        return f"Load ({self.number_people}, {self.eec})"


class Heat(models.Model):
    """Model to hold timeseries for different setups of heat component."""

    profile = ArrayField(models.FloatField())

    def __str__(self):
        return "Heat"


class Hotwater(models.Model):
    """Model to hold timeseries for different setups of hotwater component."""

    number_people = models.IntegerField()
    profile = ArrayField(models.FloatField())

    def __str__(self):
        return f"Hotwater ({self.number_people})"


class Heatpump(models.Model):
    """Model to hold air, water and brine timeseries for different setups of heatpump component."""

    medium = models.CharField()  # to distinguish between air, water and brine medium
    type_temperature = models.CharField()
    profile = ArrayField(models.FloatField())

    class Meta:
        unique_together = ("medium", "type_temperature")

    def __str__(self):
        return f"Heatpump ({self.medium}, {self.type_temperature})"
