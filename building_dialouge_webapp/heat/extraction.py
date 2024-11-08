import numpy as np
import pandas as pd
import os

# code inspired by oemof-B3/tests/test_data_processing.py


# define the paths
DATA_PATH = os.path.abspath(os.path.dirname(__file__))
# should be something like: DATA_PATH = '/home/miria/git_repos/bd_app/building_dialouge_webapp/heat'

def full_path(filename):
    return os.path.join(DATA_PATH, "data/data_raw", filename)

cop_air_path = full_path("profile_cop_air_raw.csv")
cop_water_path = full_path("profile_cop_water_raw.csv")
cop_brine_path = full_path("profile_cop_brine_raw.csv")

hotwater_pp_path = full_path("profile_hotwater_raw.csv")

load_path = full_path("profile_load_raw.csv")

pv_path = full_path("profile_PV_raw.csv")

sth_heat_path = full_path("profile_STH_heat_raw.csv")
sth_load_path = full_path("profile_STH_load_raw.csv")



def coefficient_of_performance(medium, type):
    """
    This function calculates the coefficient of
    performance (COP) depending on medium and type.
    """


def hotwater_per_person(number_people):
    """
    This function returns the hotwater-usage
     per number of people in a household.
    """

def load(number_people, eef):
    """
    This function returns the load
    per number of people in a household
    and energy efficeincy class.
    """

def photovoltaic(elev_angle, direc_angle, type):
    """
    This function returns the energy (?) given by
    photovoltaics per elevation angle, directional angle
    and type.
    """

def solarthermal(elev_angle, direc_angle, type):
    """
    This function returns the energy (?) given by
    solarthermal per elevation angle, directional angle
    and type.
    """


