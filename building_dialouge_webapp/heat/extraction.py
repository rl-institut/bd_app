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


def coefficient_of_performance(medium: list = ['air', 'water', 'brine'] , type_temp: list = ['VL75C', 'VL40C']) -> pd.Series:  
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

def hotwater_per_person(number_people: list =[1, 2, 3, 4, 5]) -> pd.Series:
    """
    This function returns the hotwater-usage
     per number of people in a household.
    """

    # read csv-file
    df_hotwater = pd.read_csv(hotwater_pp_path)

    # dict for checking allowed type
    allowed_number_people = {1, 2, 3, 4, 5}

    # checking allowed type
    if number_people not in allowed_number_people:
        raise ValueError(f'Invalid number of people: {number_people}. Allowed number of people: 1, 2, 3, 4, 5')
    
    # column name for column to be read
    column_name = f'HW-{number_people}P-60C'

    # checking column name
    if column_name not in df_hotwater.columns:
        raise ValueError(f'Invalid number of people {number_people}. Column name {column_name} not found.')
    
    # extract desired column as timeseries
    hotwater_timeseries = df_hotwater[column_name]
    
    return hotwater_timeseries

# example
# print(hotwater_per_person(3))

def load(number_people: list =[1, 2, 3, 4, 5], eec: list =[0, 1, 2, 3, 4]) -> pd.Series:
    """
    This function returns the load
    per number of people in a household
    and energy efficeincy class.
    """

    # read csv-file
    df_load = pd.read_csv(load_path)

    # dicts for checking allowed types
    allowed_number_people = {1, 2, 3, 4, 5}
    allowed_eec = {0, 1, 2, 3, 4}

    # checking allowed types
    if number_people not in allowed_number_people:
        raise ValueError(f'Invalid number of people {number_people}. Allowed number of people: 1, 2, 3, 4, 5')
    if eec not in allowed_eec:
        raise ValueError(f'Invalid energy efficency class {medium}. Allowed energy efficency classes: 0, 1, 2, 3, 4')

    # column name for column to be read
    column_name = f'EL-SEK{eec}P{number_people}'

    # checking coulmn name
    if column_name not in df_load.columns:
        raise ValueError(f'Invalid energy efficency class {eec} for chosen number of people {number_people}. Column name {column_name} not found.')
    
    # extract desired column as timeseries
    load_timeseries = df_load[column_name]
    
    return load_timeseries


def photovoltaic(elev_angle, direc_angle, type):
    """
    This function returns the energy output from
    photovoltaics per elevation angle, directional angle
    and type.
    """

    # read csv-file
    df_pv = pd.read_csv(pv_path)

    # dicts for checking allowed types
    allowed_elev_angle = {0, 10, 20, 30, 40, 45, 50, 60, 70, 80, 90}
    allowed_direc_angle = {0, 120, 150, 180, 210, 240, 270, 30, 300, 330, 360, 60, 90}
    # what about the type?

    # checking allowed types
    if elev_angle not in allowed_elev_angle:
        raise ValueError(f'Invalid elevation angle {elev_angle}. Allowed elevation angles: {allowed_elev_angle}')
    if direc_angle not in allowed_direc_angle:
        raise ValueError(f'Invalid directional angle {direc_angle}. Allowed directional angles: {allowed_direc_angle}')

    # column name for column to be read
    column_name = f'PV-H{elev_angle}-A{direc_angle}'

    # checking coulmn name
    if column_name not in df_pv.columns:
        raise ValueError(f'Invalid elevation angle {elev_angle} for chosen directional angle {direc_angle}. Column name {column_name} not found.')
    
    # extract desired column as timeseries
    pv_timeseries = df_pv[column_name]
    
    return pv_timeseries


def solarthermal(elev_angle, direc_angle, type):
    """
    This function returns the energy output from
    solarthermal per elevation angle, directional angle
    and type.
    """


