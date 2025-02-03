import os

import pandas as pd

"""
TO-DO:
- resample -> Question: not all modules have a timestamp-csv and its a different file setup?
                        just use, what is given and use this file instead of the raw_data file?
- types in pv function -> Question: what about type?
- option of csv choosing in sth function -> Question: csv files STH_load and STH_heat have the
                                                        same column names atm, could not figure out
                                                        what the differnet use is. do we need both?
"""

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


def coefficient_of_performance(medium: int, type_temp: int) -> pd.Series:
    """
    This function returns the coefficient of
    performance (COP) depending on medium and type (temperature dependent).

    Allowed mediums: 'air', 'water', 'brine'
    Allowed type of temperature dependency: 'VL75C', 'VL40C'
    """
    # file paths corresponding to medium
    medium_paths = {
        "air": cop_air_path,
        "water": cop_water_path,
        "brine": cop_brine_path,
    }

    # dicts for checking allowed types
    allowed_medium = {"air", "water", "brine"}
    allowed_type_temp = {"VL75C", "VL40C"}

    # checking allowed types
    if medium not in allowed_medium:
        raise ValueError(f"Invalid medium {medium}. Allowed mediums: {allowed_medium}")
    if type_temp not in allowed_type_temp:
        raise ValueError(f"Invalid temperature {medium}. Allowed temperatures: {allowed_type_temp}")

    # read csv-file according to medium given
    df_medium = pd.read_csv(medium_paths[medium])

    # column name for column to be read
    column_name = f"COP-{medium.capitalize()}-{type_temp}"

    # checking coulmn name
    if column_name not in df_medium.columns:
        raise ValueError(f"Invalid temperature {type_temp} for medium {medium}. Column name {column_name} not found.")

    # extract desired column as timeseries
    cop_timeseries = df_medium[column_name]

    return cop_timeseries


# example
# print(coefficient_of_performance('fish', 'VL75C'))


def hotwater_per_person(number_people: int) -> pd.Series:
    """
    This function returns the hotwater-usage
    per number of people in a household.

    Allowed number of people: 1, 2, 3, 4, 5
    """

    # read csv-file
    df_hotwater = pd.read_csv(hotwater_pp_path)

    # dict for checking allowed type
    allowed_number_people = {1, 2, 3, 4, 5}

    # checking allowed type
    if number_people not in allowed_number_people:
        raise ValueError(
            f"Invalid number of people: {number_people}. Allowed number of people: {allowed_number_people}"
        )

    # column name for column to be read
    column_name = f"HW-{number_people}P-60C"

    # checking column name
    if column_name not in df_hotwater.columns:
        raise ValueError(f"Invalid number of people {number_people}. Column name {column_name} not found.")

    # extract desired column as timeseries
    hotwater_timeseries = df_hotwater[column_name]

    return hotwater_timeseries


# example
# print(hotwater_per_person(3))


def load(number_people: int, eec: int) -> pd.Series:
    """
    This function returns the load
    per number of people in a household
    and energy efficeincy class.

    Allowed number of people: 1, 2, 3, 4, 5
    Allowed energy efficency classes: 0, 1, 2, 3, 4
    """

    # read csv-file
    df_load = pd.read_csv(load_path)

    # dicts for checking allowed types
    allowed_number_people = {1, 2, 3, 4, 5}
    allowed_eec = {0, 1, 2, 3, 4}

    # checking allowed types
    if number_people not in allowed_number_people:
        raise ValueError(
            f"Invalid number of people {number_people}. Allowed number of people: {allowed_number_people}"
        )
    if eec not in allowed_eec:
        raise ValueError(f"Invalid energy efficency class {eec}. Allowed energy efficency classes: {allowed_eec}")

    # column name for column to be read
    column_name = f"EL-SEK{eec}P{number_people}"

    # checking coulmn name
    if column_name not in df_load.columns:
        raise ValueError(
            f"Invalid energy efficency class {eec} for chosen number of people {number_people}. Column name {column_name} not found."
        )

    # extract desired column as timeseries
    load_timeseries = df_load[column_name]

    return load_timeseries


# example
# print(load(3, 9))


def photovoltaic(elev_angle: int, direc_angle: int) -> pd.Series:
    """
    This function returns the energy output from
    photovoltaics per elevation angle, directional angle
    and type.

    Allowed elevation angles: 0, 10, 20, 30, 40, 45, 50, 60, 70, 80, 90
    Allowed directional angle: 0, 120, 150, 180, 210, 240, 270, 30, 300, 330, 360, 60, 90
    """
    # what about type?

    # read csv-file
    df_pv = pd.read_csv(pv_path)

    # dicts for checking allowed types
    allowed_elev_angle = {0, 10, 20, 30, 40, 45, 50, 60, 70, 80, 90}
    allowed_direc_angle = {0, 120, 150, 180, 210, 240, 270, 30, 300, 330, 360, 60, 90}
    # what about the type?

    # checking allowed types
    if elev_angle not in allowed_elev_angle:
        raise ValueError(f"Invalid elevation angle {elev_angle}. Allowed elevation angles: {allowed_elev_angle}")
    if direc_angle not in allowed_direc_angle:
        raise ValueError(f"Invalid directional angle {direc_angle}. Allowed directional angles: {allowed_direc_angle}")

    # column name for column to be read
    column_name = f"PV-H{elev_angle}-A{direc_angle}"

    # checking coulmn name
    if column_name not in df_pv.columns:
        raise ValueError(
            f"Invalid elevation angle {elev_angle} for chosen directional angle {direc_angle}. Column name {column_name} not found."
        )

    # extract desired column as timeseries
    pv_timeseries = df_pv[column_name]

    return pv_timeseries


# example
# print(photovoltaic(10,210))


def solarthermal(type_temp: int, elev_angle: int, direc_angle: int) -> pd.Series:
    """
    This function returns the energy output from
    solarthermal per elevation angle, directional angle
    and type (temperature dependent).

    Alowed type depending on temperature: 40, 75
    Allowed elevation angles: 0, 10, 20, 30, 40, 45, 50, 60, 70, 80, 90
    Allowed directional angle: 0, 120, 150, 180, 210, 240, 270, 30, 300, 330, 360, 60, 90
    """
    # csv files STH_load and STH_heat have the same column names atm

    # read csv-files
    df_sth_load = pd.read_csv(sth_load_path)
    # df_sth_heat = pd.read_csv(sth_heat_path) -> for what is it needed?

    # dicts for checking allowed types
    allowed_type_temp = {40, 75}
    allowed_elev_angle = {0, 10, 20, 30, 40, 45, 50, 60, 70, 80, 90}
    allowed_direc_angle = {0, 120, 150, 180, 210, 240, 270, 30, 300, 330, 360, 60, 90}

    # checking allowed types
    if type not in allowed_type_temp:
        raise ValueError(f"Invalid type {type_temp}. Allowed types: {allowed_type_temp}")
    if elev_angle not in allowed_elev_angle:
        raise ValueError(f"Invalid elevation angle {elev_angle}. Allowed elevation angles: {allowed_elev_angle}")
    if direc_angle not in allowed_direc_angle:
        raise ValueError(f"Invalid directional angle {direc_angle}. Allowed directional angles: {allowed_direc_angle}")

    # column name for column to be read
    column_name = f"STH-VL{type}-H{elev_angle}-A{direc_angle}"

    # checking coulmn name
    if column_name not in df_sth_load.columns:
        raise ValueError(
            f"Invalid elevation angle {elev_angle} and directional angle {direc_angle} for chosen type {type_temp}. Column name {column_name} not found."
        )

    # extract desired column as timeseries
    sth_timeseries = df_sth_load[column_name]

    return sth_timeseries


# example
# print(solarthermal(10,210,40))
