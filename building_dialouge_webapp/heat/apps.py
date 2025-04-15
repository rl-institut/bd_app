from django.apps import AppConfig
from django.conf import settings


class HeatConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "building_dialouge_webapp.heat"

    def ready(self) -> None:
        """Content in here is run when app is ready."""
        # pylint: disable=C0415
        from django_oemof import hooks

        # pylint: disable=C0415
        from building_dialouge_webapp.heat import hooks as bd_hooks

        # noinspection PyPep8Naming
        SETUP_FUNCTIONS = (  # noqa: N806
            bd_hooks.init_parameters,
            bd_hooks.init_flow_data,
            bd_hooks.init_renovation_scenario,
            bd_hooks.init_tabula_data,
            bd_hooks.init_roof,
            bd_hooks.init_renovation_data,
        )

        # noinspection PyPep8Naming
        PARAMETER_FUNCTIONS = (  # noqa: N806
            bd_hooks.set_up_loads,
            bd_hooks.set_up_volatiles,
            bd_hooks.set_up_heatpumps,
            bd_hooks.set_up_conversion_technologies,
            bd_hooks.set_up_hotwater_supply,
            bd_hooks.set_up_storages,
            bd_hooks.unpack_oeprom,
        )

        for func in SETUP_FUNCTIONS:
            hooks.register_hook(
                hooks.HookType.SETUP,
                hooks.Hook(scenario="oeprom", function=func),
            )

        for func in PARAMETER_FUNCTIONS:
            hooks.register_hook(
                hooks.HookType.PARAMETER,
                hooks.Hook(scenario="oeprom", function=func),
            )

        if settings.DEBUG:
            hooks.register_hook(
                hooks.HookType.ENERGYSYSTEM,
                hooks.Hook(scenario="oeprom", function=bd_hooks.debug_input_data),
            )

        hooks.register_hook(
            hooks.HookType.MODEL,
            hooks.Hook(scenario="oeprom", function=bd_hooks.couple_battery_storage_to_pv_capacity),
        )
