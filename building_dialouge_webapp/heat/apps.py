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

        hooks.register_hook(
            hooks.HookType.SETUP,
            hooks.Hook(scenario=hooks.ALL_SCENARIOS, function=bd_hooks.read_flow_data),
        )

        hooks.register_hook(
            hooks.HookType.SETUP,
            hooks.Hook(scenario=hooks.ALL_SCENARIOS, function=bd_hooks.get_renovation_data),
        )

        hooks.register_hook(
            hooks.HookType.SETUP,
            hooks.Hook(scenario=hooks.ALL_SCENARIOS, function=bd_hooks.calculate_energy_demand),
        )
