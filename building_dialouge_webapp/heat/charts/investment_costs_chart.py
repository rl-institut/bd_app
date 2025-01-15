import json


def generate_investment_chart_options(scenarios):
    scenario_count = len(scenarios)

    if scenario_count == 1:
        height_value = 160
        title_top = "60%"
    elif scenario_count == 3:
        height_value = 300
        title_top = "40%"
    else:
        height_value = scenario_count * 100
        title_top = "55%"

    y_axis_data = []
    renovation_data = []
    maintenance_data = []

    for scenario in reversed(scenarios):
        y_axis_data.append(scenario["name"])

        renovation_data.append({
            "value": scenario["renovation"],
            "itemStyle": {
                "color": "#80b1d3"
            }
        })

        maintenance_data.append({
            "value": scenario["maintenance"],
            "itemStyle": {
                "color": "#fdb462"
            }
        })

    option = {
        "grid": {
            "left": "10%",
            "right": "4%",
            "bottom": "3%",
            "height": height_value,
            "containLabel": True
        },
        "xAxis": {
            "type": "value",
            "axisLabel": {
                "show": True,
                "fontSize": 26,
                "color": "#b3b4b2",
                "rotate": 45,
            },
            "splitLine": {
                "show": True
            }
        },
        "yAxis": {
            "type": "category",
            "data": y_axis_data,
            "axisLine": {"show": False},
            "axisLabel": {
                "show": True,
                "fontSize": 28
            },
            "axisTick": {"show": False}
        },
        "title": {
            "text": "Zusammensetzung der Investitionskosten in €",
            "left": "0%",
            "top": title_top,
            "textStyle": {
                "fontWeight": "normal",
                "fontSize": 34,
                "color": "#6e6e6e"
            }
        },
        "series": [
            {
                "name": "Sanierung",
                "type": "bar",
                "stack": "total",
                "data": renovation_data,
                "label": {
                    "show": True,
                    "position": "insideRight",
                    "formatter": "({ value }) => value.toLocaleString('de-DE')",
                    "fontSize": 28,
                    "fontWeight": "bold"
                }
            },
            {
                "name": "Instandhaltungskosten",
                "type": "bar",
                "stack": "total",
                "data": maintenance_data,
                "label": {
                    "show": True,
                    "position": "insideRight",
                    "formatter": "({ value }) => value.toLocaleString('de-DE')",
                    "fontSize": 28,
                    "fontWeight": "bold"
                }
            }
        ]
    }

    return option


if __name__ == "__main__":
    scenario1 = {
        "name": "Szenario 1",
        "renovation": 55000,
        "maintenance": 45000
    }
    scenario2 = {
        "name": "Szenario 2",
        "renovation": 100000,
        "maintenance": 67250
    }
    scenario3 = {
        "name": "Szenario 3",
        "renovation": 120000,
        "maintenance": 70000
    }

    # Teste verschieden viele Szenarien:
    #  1) Nur ein Szenario
    scenarios_one = [scenario1]
    #  2) Drei Szenarien
    scenarios_three = [scenario1, scenario2, scenario3]
    #  3) Ein anderer Fall (z.B. zwei Szenarien)
    scenarios_two = [scenario1, scenario2]

    # print("=== Ein Szenario ===")
    # print(json.dumps(generate_investment_chart_options(scenarios_one), indent=2, ensure_ascii=False))
    #
    # print("\n=== Zwei Szenarien ===")
    print(json.dumps(generate_investment_chart_options(scenarios_two), indent=2, ensure_ascii=False))

    # print("\n=== Drei Szenarien ===")
    # print(json.dumps(generate_investment_chart_options(scenarios_three), indent=2, ensure_ascii=False))
