from pathlib import Path

import pandas as pd

# define the paths
DATA_PATH = Path(Path(__file__).parent)
# should be something like: DATA_PATH = '/home/miria/git_repos/bd_app/building_dialouge_webapp/heat'


def full_path(filename):
    return Path(DATA_PATH) / "data/data_raw" / filename


cop_air_path = full_path("profile_cop_air_raw.csv")
cop_water_path = full_path("profile_cop_water_raw.csv")
cop_brine_path = full_path("profile_cop_brine_raw.csv")

hotwater_pp_path = full_path("profile_hotwater_raw.csv")

load_path = full_path("profile_load_raw.csv")

pv_path = full_path("profile_PV_raw.csv")

sth_heat_path = full_path("profile_STH_heat_raw.csv")
sth_load_path = full_path("profile_STH_load_raw.csv")


def coefficient_of_performance(medium: str, type_temp: str) -> pd.Series:
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
        msg = f"Invalid medium {medium}. Allowed mediums: {allowed_medium}"
        raise ValueError(msg)
    if type_temp not in allowed_type_temp:
        msg = f"Invalid temperature {medium}. Allowed temperatures: {allowed_type_temp}"
        raise ValueError(msg)

    # read csv-file according to medium given
    df_medium = pd.read_csv(medium_paths[medium])

    # column name for column to be read
    column_name = f"COP-{medium.capitalize()}-{type_temp}"

    # checking coulmn name
    if column_name not in df_medium.columns:
        msg = f"Invalid temperature {type_temp} for medium {medium}. Column name {column_name} not found."
        raise ValueError(msg)

    # extract desired column as timeseries and return it
    return df_medium[column_name]


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
        msg = f"Invalid number of people: {number_people}. Allowed number of people: {allowed_number_people}"
        raise ValueError(msg)

    # column name for column to be read
    column_name = f"HW-{number_people}P-60C"

    # checking column name
    if column_name not in df_hotwater.columns:
        msg = f"Invalid number of people {number_people}. Column name {column_name} not found."
        raise ValueError

    # extract desired column as timeseries and return it
    return df_hotwater[column_name]


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
        msg = f"Invalid number of people {number_people}. Allowed number of people: {allowed_number_people}"
        raise ValueError(msg)
    if eec not in allowed_eec:
        msg = f"Invalid energy efficency class {eec}. Allowed energy efficency classes: {allowed_eec}"
        raise ValueError(msg)

    # column name for column to be read
    column_name = f"EL-SEK{eec}P{number_people}"

    # checking coulmn name
    if column_name not in df_load.columns:
        msg = f"Invalid energy efficency class {eec} for chosen number of people {number_people}. \
                Column name {column_name} not found."
        raise ValueError(msg)

    # extract desired column as timeseries and return it
    return df_load[column_name]


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
        msg = f"Invalid elevation angle {elev_angle}. Allowed elevation angles: {allowed_elev_angle}"
        raise ValueError(msg)
    if direc_angle not in allowed_direc_angle:
        msg = f"Invalid directional angle {direc_angle}. Allowed directional angles: {allowed_direc_angle}"
        raise ValueError(msg)

    # column name for column to be read
    column_name = f"PV-H{elev_angle}-A{direc_angle}"

    # checking coulmn name
    if column_name not in df_pv.columns:
        msg = f"Invalid elevation angle {elev_angle} for chosen directional angle {direc_angle}. \
                Column name {column_name} not found."
        raise ValueError(msg)

    # extract desired column as timeseries and return it
    return df_pv[column_name]


def solarthermal(type_sth: str, type_temp: int, elev_angle: int, direc_angle: int) -> pd.Series:
    """
    This function returns the energy output from
    solarthermal per elevation angle, directional angle
    and type (temperature dependent).

    Allowed type of solarthermal: 'heat', 'load'
    Alowed type depending on temperature: 40, 75
    Allowed elevation angles: 0, 10, 20, 30, 40, 45, 50, 60, 70, 80, 90
    Allowed directional angle: 0, 120, 150, 180, 210, 240, 270, 30, 300, 330, 360, 60, 90
    """
    # csv files STH_load and STH_heat have the same column names atm
    # file paths corresponding to type

    type_paths = {
        "load": sth_load_path,
        "heat": sth_heat_path,
    }

    # dicts for checking allowed types
    alllowed_type = {"heat", "load"}
    allowed_type_temp = {40, 75}
    allowed_elev_angle = {0, 10, 20, 30, 40, 45, 50, 60, 70, 80, 90}
    allowed_direc_angle = {0, 120, 150, 180, 210, 240, 270, 30, 300, 330, 360, 60, 90}

    # checking allowed types
    if type_sth not in alllowed_type:
        msg = f"Invalid type {type_sth}. Allowed types: {alllowed_type}"
        raise ValueError(msg)
    if type_temp not in allowed_type_temp:
        msg = f"Invalid type of temperature {type_temp}. Allowed types: {allowed_type_temp}"
        raise ValueError(msg)
    if elev_angle not in allowed_elev_angle:
        msg = f"Invalid elevation angle {elev_angle}. Allowed elevation angles: {allowed_elev_angle}"
        raise ValueError(msg)
    if direc_angle not in allowed_direc_angle:
        msg = f"Invalid directional angle {direc_angle}. Allowed directional angles: {allowed_direc_angle}"
        raise ValueError(msg)

    # read csv-file according to type given
    df_sth = pd.read_csv(type_paths[type_sth])

    # column name for column to be read
    column_name = f"STH-VL{type_temp}-H{elev_angle}-A{direc_angle}"

    # checking coulmn name
    if column_name not in df_sth.columns:
        msg = f"Invalid elevation angle {elev_angle} and directional angle {direc_angle} for chosen \
                type {type_temp}. Column name {column_name} not found."
        raise ValueError(msg)

    # extract desired column as timeseries and return it
    return df_sth[column_name]
