from django import template
from django.conf import settings

register = template.Library()


@register.simple_tag
def heating_icon(heating_component):
    heating_component = heating_component.replace(" ", "-")
    return f"images/icons/heating-technologies/24x24/{heating_component}-24x24.svg"


@register.simple_tag
def renovation_icon(renovation_component):
    renovation_filename = f"{renovation_component.replace(' ', '-')}-24x24.svg"
    renovations_folder = settings.APPS_DIR / "static" / "images" / "icons" / "renovation" / "24x24"
    if renovation_filename not in [f.name for f in renovations_folder.iterdir()]:
        renovation_filename = "Sanierung-24x24.svg"
    return f"images/icons/renovation/24x24/{renovation_filename}"
