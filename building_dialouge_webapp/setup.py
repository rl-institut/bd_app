from building_dialouge_webapp.heat import extraction
from building_dialouge_webapp.heat import models


def import_heatpump_data():
    allowed_medium = {"air", "water", "brine"}
    allowed_type_temp = {"VL75C", "VL40C"}

    for medium in allowed_medium:
        for temp in allowed_type_temp:
            heatpump_timeseries = extraction.coefficient_of_performance(medium=medium, type_temp=temp)
            models.Heatpump(medium=medium, type_temperature=temp, profile=heatpump_timeseries.tolist()).save()


def import_hotwater_data():
    allowed_number_people = {1, 2, 3, 4, 5}

    for number_people in allowed_number_people:
        hotwater_timeseries = extraction.hotwater_per_person(number_people=number_people)
        models.Hotwater(number_people=number_people, profile=hotwater_timeseries.tolist()).save()


def import_load_data():
    allowed_number_people = {1, 2, 3, 4, 5}
    allowed_eec = {0, 1, 2, 3, 4}

    for number_people in allowed_number_people:
        for eec in allowed_eec:
            load_timeseries = extraction.load(number_people=number_people, eec=eec)
            models.Load(number_people=number_people, eec=eec, profile=load_timeseries.tolist()).save()


def import_photovoltaic_data():
    allowed_elev_angle = {0, 10, 20, 30, 40, 45, 50, 60, 70, 80, 90}
    allowed_direc_angle = {0, 120, 150, 180, 210, 240, 270, 30, 300, 330, 360, 60, 90}

    for elev in allowed_elev_angle:
        for direc in allowed_direc_angle:
            if elev == 45 and direc not in (0, 120, 240, 360):  # noqa: PLR2004
                continue  # These combinations do not exist for some reason - must be checked!
            photovoltaic_timeseries = extraction.photovoltaic(elev, direc)
            models.Photovoltaic(
                elevation_angle=elev,
                direction_angle=direc,
                profile=photovoltaic_timeseries.tolist(),
            ).save()


def import_solarthermal_data():
    alllowed_type = {"heat", "load"}
    allowed_type_temp = {40, 75}
    allowed_elev_angle = {0, 10, 20, 30, 40, 45, 50, 60, 70, 80, 90}
    allowed_direc_angle = {0, 120, 150, 180, 210, 240, 270, 30, 300, 330, 360, 60, 90}

    for type_sth in alllowed_type:
        for temp in allowed_type_temp:
            for elev in allowed_elev_angle:
                for direc in allowed_direc_angle:
                    if elev == 45 and direc not in (0, 120, 240, 360):  # noqa: PLR2004
                        continue  # These combinations do not exist for some reason - must be checked!
                    sth_timeseries = extraction.solarthermal(type_sth, temp, elev, direc)
                    models.Solarthermal(
                        type=type_sth,
                        temperature=temp,
                        elevation_angle=elev,
                        direction_angle=direc,
                        profile=sth_timeseries.tolist(),
                    ).save()


def load_profiles():
    import_load_data()
    import_heatpump_data()
    import_hotwater_data()
    import_photovoltaic_data()
    import_solarthermal_data()
