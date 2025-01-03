import numpy as np
import pandas as pd
import os


# code inspired by oemof-B3/tests/test_data_processing.py
# and     oemof-B3/scripts/prepare_heat_demand.py


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


def coefficient_of_performance(medium: list = ['air', 'water', 'brine'] , type_temp: list = ['VL75C', 'VL40C']) -> dict:  
    # medium wenn einzeln nur ein str, nicht list; genauso type_temp, OEMOF angucken
    """
    This function returns the coefficient of
    performance (COP) depending on medium and type. 
    """
    # file paths corresponding to medium
    medium_paths = {
        'air': cop_air_path,
        'water': cop_water_path,
        'brine': cop_brine_path
    }
    
    # Read csv-file
    # df_cop_air = pd.read_csv(cop_air_path)
    # df_cop_water = pd.read_csv(cop_water_path)
    # df_cop_brine = pd.read_csv(cop_brine_path)

    # empty dict for return
    cop_air_dict = {}
    cop_water_dict = {}
    cop_brine_dict = {}

    # dicts for checking allowed types
    allowed_medium = {'air', 'water', 'brine'}
    allowed_type_temp = {'VL75C', 'VL40C'}

    # checking allowed types
    if medium not in allowed_medium:
        raise ValueError(f'Invalid medium {medium}. Allowed mediums: air, water, brine')
    if type_temp not in allowed_type_temp:
        raise ValueError(f'Invalid temperature {medium}. Allowed temperatures: VL75C, VL40C')

    # read csv-file according to medium given
    df_medium = pd.read_csv(medium_paths[medium])

    # column name for column to be read
    column_name = f'COP-{medium.capitalize()}-{type_temp}'

    # checking coulmn name
    if column_name not in df_medium.columns:
        raise ValueError(f'Invalid temperature {type_temp} for medium {medium}. Column name {column_name} not found.')
    
    # extract desired column as timeseries
    cop_timeseries = df_medium[column_name]
    
    return cop_timeseries

# example
# print(coefficient_of_performance('air', 'VL75C'))

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


