import pandas as pd

from building_dialouge_webapp.heat.models import Solarthermal

ts = pd.Series(range(8760))
Solarthermal(type="heat", temperature=60, elevation_angle=40, direction_angle=120, profile=ts.tolist()).save()
