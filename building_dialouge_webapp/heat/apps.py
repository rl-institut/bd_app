from django.apps import AppConfig


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
            bd_hooks.init_roof,
            bd_hooks.init_renovation_data,
        )

        # noinspection PyPep8Naming
        PARAMETER_FUNCTIONS = (  # noqa: N806
            bd_hooks.set_up_loads,
            bd_hooks.set_up_volatiles,
            bd_hooks.set_up_heatpump,
            bd_hooks.unpack_oeprom,
        )

        for func in SETUP_FUNCTIONS:
            hooks.register_hook(
                hooks.HookType.SETUP,
                hooks.Hook(scenario=hooks.ALL_SCENARIOS, function=func),
            )

        for func in PARAMETER_FUNCTIONS:
            hooks.register_hook(
                hooks.HookType.PARAMETER,
                hooks.Hook(scenario=hooks.ALL_SCENARIOS, function=func),
            )
