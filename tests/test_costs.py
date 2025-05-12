from building_dialouge_webapp.heat import settings


def test_technology_costs_avg():
    ep_costs = settings.get_ep_cost("firewood")
    avg_capex = sum([882.93, 882.93, 560.77, 560.77, 560.77]) / 5
    avg_opex = sum([34.60, 34.60, 18.60, 18.60, 18.60]) / 5
    annuity = avg_capex * 0.12 * 1.12**20 / (1.12**20 - 1)
    assert round(ep_costs, 2) == round(annuity + avg_opex, 2)


def test_technology_costs_specified():
    ep_costs = settings.get_ep_cost("firewood", 150)
    avg_capex = 560.77
    avg_opex = 18.60
    annuity = avg_capex * 0.12 * 1.12**20 / (1.12**20 - 1)
    assert round(ep_costs, 2) == round(annuity + avg_opex, 2)
