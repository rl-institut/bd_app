import json


def generate_echarts_option(scenarios):
    default_colors = {
        "Heute": "#dcdcdb",
        "Szenario 1": "#1b9e77",
        "Szenario 2": "#7570b3",
    }

    default_label_colors = {
        "Heute": "black",
        "Szenario 1": "white",
        "Szenario 2": "white",
    }

    y_axis_data = [s["name"] for s in reversed(scenarios)]

    series_data = []
    for s in reversed(scenarios):
        name = s["name"]
        value = s["value"]

        color = s.get("color", default_colors.get(name, "#666666"))
        label_color = s.get("labelColor", default_label_colors.get(name, "white"))

        series_data.append(
            {
                "value": value,
                "itemStyle": {
                    "color": color,
                },
                "label": {
                    "color": label_color,
                },
            },
        )

    font_size = 24 if len(scenarios) == 4 else (40 if len(scenarios) == 2 else 34)

    option = {
        "grid": {
            "left": "20%",
            "right": "4%",
            "bottom": "3%",
            "height": 200,
            "containLabel": True,
        },
        "xAxis": {
            "type": "value",
            "axisLabel": {
                "show": True,
                "fontSize": 26,
                "color": "#b3b4b2",
            },
            "splitLine": {
                "show": True,
            },
        },
        "yAxis": {
            "type": "category",
            "data": y_axis_data,
            "axisLine": {
                "show": False,
            },
            "axisLabel": {
                "show": True,
                "fontSize": 28,
            },
            "axisTick": {
                "show": False,
            },
        },
        "title": {
            "text": "Heizenergieverbrauch in kWh/(m²*a) (Endenergie)",
            "left": "0%",
            "top": "55%",
            "textStyle": {
                "fontWeight": "normal",
                "fontSize": 34,
                "color": "#6e6e6e",
            },
        },
        "series": [
            {
                "type": "bar",
                "data": series_data,
                "label": {
                    "show": True,
                    "position": "right",
                    "fontSize": font_size,
                    "fontWeight": "bold",
                    "align": "right",
                    "offset": [-20, 0],
                },
            },
        ],
    }

    return option


# Beispiele:
# 1) Nur ein Szenario
single_scenario_option = generate_echarts_option(
    [
        {"name": "Heute", "value": 230},
        {"name": "Szenario 1", "value": 130},
    ],
)
print(json.dumps(single_scenario_option, indent=2, ensure_ascii=False))

# 2) Zwei Szenarien
# two_scenarios_option = generate_echarts_option(
#     [
#         {"name": "Heute", "value": 230},
#         {"name": "Szenario 1", "value": 130},
#         {"name": "Szenario 2", "value": 47}
#     ]
# )
# print(json.dumps(two_scenarios_option, indent=2, ensure_ascii=False))

# 3) Drei Szenarien
# three_scenarios_option = generate_echarts_option(
#     [
#          {"name": "Heute", "value": 230},
#          {"name": "Szenario 1", "value": 130},
#          {"name": "Szenario 2", "value": 47},
#          {"name": "Szenario 3", "value": 87}
#      ]
# )
# print(json.dumps(three_scenarios_option, indent=2, ensure_ascii=False))
