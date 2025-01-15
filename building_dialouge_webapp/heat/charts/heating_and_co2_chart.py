import json

def generate_echarts_option(scenarios, title):
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

    order = {"Heute": 1, "Szenario 1": 2, "Szenario 2": 3, "Szenario 3": 4}
    sorted_scenarios = sorted(scenarios, key=lambda x: order.get(x["name"], 5))

    y_axis_data = [s["name"] for s in reversed(sorted_scenarios)]

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

    title_top = "55%"
    grid_height = 200
    rotate = 0
    font_size = 24 if len(scenarios) == 4 else (44 if len(scenarios) == 2 else 34)
    if title == "CO2-Kosten in € pro Jahr":
        rotate = 45
        grid_height = 250
        title_top = "50%"

    option = {
        "grid": {
            "left": "20%",
            "right": "4%",
            "bottom": "3%",
            "height": grid_height,
            "containLabel": True,
        },
        "xAxis": {
            "type": "value",
            "axisLabel": {
                "show": True,
                "fontSize": 26,
                "color": "#b3b4b2",
                "rotate": rotate
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
            "text": title,
            "left": "0%",
            "top": title_top,
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


# Beispiele heating_consumption:
# 1) Nur ein Szenario
single_scenario_option = generate_echarts_option(
    [
        {"name": "Heute", "value": 230},
        {"name": "Szenario 1", "value": 130},
    ]
,"Heizenergieverbrauch in kWh/(m²*a) (Endenergie)")
print(json.dumps(single_scenario_option, indent=2, ensure_ascii=False))

#2) Zwei Szenarien
# two_scenarios_option = generate_echarts_option(
#     [
#         {"name": "Heute", "value": 230},
#         {"name": "Szenario 1", "value": 130},
#         {"name": "Szenario 2", "value": 47}
#     ]
# ,"Heizenergieverbrauch in kWh/(m²*a) (Endenergie)")
# print(json.dumps(two_scenarios_option, indent=2, ensure_ascii=False))

# 3) Drei Szenarien
# three_scenarios_option = generate_echarts_option(
#     [
#          {"name": "Heute", "value": 230},
#          {"name": "Szenario 1", "value": 130},
#          {"name": "Szenario 2", "value": 47},
#          {"name": "Szenario 3", "value": 87}
#      ]
# ,"Heizenergieverbrauch in kWh/(m²*a) (Endenergie)")
# print(json.dumps(three_scenarios_option, indent=2, ensure_ascii=False))
# Beispiele CO2-Kosten:
single_scenario_option = generate_echarts_option(
    [
        {"name": "Heute", "value": 2600},
        {"name": "Szenario 1", "value": 1200},
    ]
,"CO2-Kosten in € pro Jahr")
print(json.dumps(single_scenario_option, indent=2, ensure_ascii=False))
# two_scenarios_option = generate_echarts_option(
#     [
#         {"name": "Heute", "value": 2600},
#         {"name": "Szenario 1", "value": 1200},
#         {"name": "Szenario 2", "value": 700},
#     ]
# ,"CO2-Kosten in € pro Jahr")
# print(json.dumps(two_scenarios_option, indent=2, ensure_ascii=False))
# three_scenarios_option = generate_echarts_option(
#     [
#          {"name": "Heute", "value": 2600},
#          {"name": "Szenario 1", "value": 1200},
#          {"name": "Szenario 2", "value": 700},
#          {"name": "Szenario 3", "value": 900}
#      ]
# ,"CO2-Kosten in € pro Jahr")
# print(json.dumps(three_scenarios_option, indent=2, ensure_ascii=False))
