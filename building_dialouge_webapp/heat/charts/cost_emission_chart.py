import json


def create_echarts_cost_emission(title, unit, data):
    def get_item_properties(item_name):
        if item_name in ["Instandhaltung", "Heute"]:
            return {"color": "#dcdcdb", "label_color": "BLACK"}
        elif item_name == "Szenario 1":
            return {"color": "#1b9e77", "label_color": "white"}
        elif item_name == "Szenario 2":
            return {"color": "#7570b3", "label_color": "white"}
        elif item_name == "Szenario 3":
            return {"color": "#ff9900", "label_color": "white"}
        else:
            return {"color": "#cccccc", "label_color": "white"}

    # Sort data to ensure "Instandhaltung" or "Heute" is on top
    order = {"Instandhaltung": 1, "Heute": 1, "Szenario 1": 2, "Szenario 2": 3, "Szenario 3": 4}
    sorted_data = sorted(data, key=lambda x: order.get(x["name"], 5))

    # Reverse the sorted data to match the ECharts ordering (bottom to top)
    sorted_data.reverse()

    # Prepare yAxis categories and series data
    y_axis_categories = [item["name"] for item in sorted_data]
    series_data = [
        {
            "value": item["value"],
            "itemStyle": {"color": get_item_properties(item["name"])["color"]},
            "label": {"color": get_item_properties(item["name"])["label_color"]},
        }
        for item in sorted_data
    ]

    font_size = 28 if len(data) == 4 else 34
    grid_left = "35%" if title == "Emissionen" else "25%"

    # Construct the ECharts option
    option = {
        "grid": {
            "left": grid_left,
            "right": "4%",
            "bottom": "3%",
            "height": 200,
            "containLabel": True,
        },
        "xAxis": {
            "type": "value",
            "axisLabel": {"show": False},
            "splitLine": {"show": True},
            "min": 0,
            "max": max(item["value"] for item in data) * 1.1,  # Add 10% padding
            "interval": 20000,
        },
        "yAxis": {
            "type": "category",
            "data": y_axis_categories,
            "axisLine": {"show": False},
            "axisLabel": {"show": True, "fontSize": 28},
            "axisTick": {"show": False},
        },
        "title": {
            "text": title,
            "left": "0%",
            "top": "80%",
            "textStyle": {"fontWeight": "bold", "fontSize": 60, "color": "#6e6e6e"},
        },
        "series": [
            {
                "data": series_data,
                "type": "bar",
                "label": {
                    "show": True,
                    "position": "right",
                    "formatter": f"({{ value }}) => `${{value.toLocaleString('de-DE')}} {unit}`",
                    "fontSize": font_size,
                    "fontWeight": "bold",
                    "align": "right",
                    "offset": [-20, 0],
                },
            },
        ],
    }
    return option


costs_data = [
    {"name": "Instandhaltung", "value": 50000},
    {"name": "Szenario 1", "value": 82000},
    {"name": "Szenario 2", "value": 140000},
    {"name": "Szenario 3", "value": 142000},
]
emission_data = [
    {"name": "Heute", "value": 26},
    {"name": "Szenario 1", "value": 12},
    {"name": "Szenario 2", "value": 7},
    {"name": "Szenario 3", "value": 15},
]

costs_chart = create_echarts_cost_emission(title="Kosten", unit="€", data=costs_data)
print(json.dumps(costs_chart, indent=2, ensure_ascii=False))
emission_chart = create_echarts_cost_emission(title="Emissionen", unit="t/a", data=emission_data)
print(json.dumps(emission_chart, indent=2, ensure_ascii=False))
