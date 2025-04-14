from django_oemof.standalone import init_django

init_django(installed_apps=["building_dialouge_webapp.heat"])
from django_oemof import hooks  # noqa: E402
from django_oemof import simulation  # noqa: E402

RENOVATION_SCENARIO = "scenario1"
PARAMETERS = {
    "renovation_scenario": RENOVATION_SCENARIO,
    "django_htmx_flow": {
        "building_type": "single_family",
        "construction_year": 1955,
        "number_persons": 2,
        "monument_protection": "no",
        "building_type_done": "True",
        "roof_insulation_year": 1955,
        "upper_storey_ceiling_insulation_year": 1956,
        "cellar_insulation_year": 1955,
        "facade_insulation_year": 1988,
        "insulation_done": "True",
        "energy_source": "gas",
        "solar_thermal_exists": "doesnt_exist",
        "hotwater_heating_done": "True",
        "flat_roof": "doesnt_exist",
        "roof_orientation": "se",
        "roof_inclination_known": "known",
        "roof_inclination": 50,
        "roof_done": "True",
        "heating_system_construction_year": 1988,
        "heating_storage_exists": "exists",
        "heating_storage_capacity_known": "known",
        "heating_storage_capacity": 100,
        "heating_done": "True",
        "pv_exists": "doesnt_exist",
        "scenario1-primary_heating": "heat_pump",
        "subsidy": ["sub1", "sub2", "sub3", "sub4", "sub5", "sub6"],
        "subsidy_hidden": "",
        "promotional_loan": ["loan1"],
        "promotional_loan_hidden": "",
        "financial_support_done": "True",
        "hotwater_supply": "instantaneous_water_heater",
        "scenario1-heat_pump_type": "air_heat_pump",
        "scenario1-secondary_heating": ["pv"],
        "scenario1-secondary_heating_hidden": "none",
        "scenario1-facade_renovation": False,
        "scenario1-roof_renovation": False,
        "scenario1-roof_renovation_details": "",
        "scenario1-window_renovation": False,
        "scenario1-cellar_renovation": False,
        "scenario1-entrance_renovation": False,
        "scenario1-renovation_input_hidden": "",
        "scenario1-renovation_request_done": "True",
        "v": "True",
    },
}

parameters = hooks.apply_hooks(
    hook_type=hooks.HookType.SETUP,
    scenario="oeprom",
    data=PARAMETERS,
    request=None,
)
simulation_id = simulation.simulate_scenario(scenario="oeprom", parameters=parameters)
