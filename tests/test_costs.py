from building_dialouge_webapp.heat import settings


def test_technology_costs():
    capacitiy_costs = settings.get_capacity_cost("firewood")
    assert capacitiy_costs == round(
        sum([882.93, 882.93, 560.77, 560.77, 560.77]) / 5 + sum([34.60, 34.60, 18.60, 18.60, 18.60]) / 5,
        2,
    )
