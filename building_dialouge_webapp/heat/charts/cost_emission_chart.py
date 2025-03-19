EXAMPLE_COST_DATA = [
    {"name": "Instandhaltung", "value": 50000},
    {"name": "Szenario 1", "value": 82000},
    {"name": "Szenario 2", "value": 140000},
    {"name": "Szenario 3", "value": 142000},
]
EXAMPLE_EMISSION_DATA = [
    {"name": "Heute", "value": 26},
    {"name": "Szenario 1", "value": 12},
    {"name": "Szenario 2", "value": 7},
    {"name": "Szenario 3", "value": 15},
]


def create_echarts_cost_emission(title, unit, data):
    def get_item_properties(item_name):
        if item_name in ["Instandhaltung", "Heute"]:
            return {"color": "#dcdcdb", "label_color": "BLACK"}
        if item_name == "Szenario 1":
            return {"color": "#1b9e77", "label_color": "white"}
        if item_name == "Szenario 2":
            return {"color": "#7570b3", "label_color": "white"}
        if item_name == "Szenario 3":
            return {"color": "#ff9900", "label_color": "white"}
        return {"color": "#cccccc", "label_color": "white"}

    # Sort data to ensure "Instandhaltung" or "Heute" is on top
    order = {
        "Instandhaltung": 1,
        "Heute": 1,
        "Szenario 1": 2,
        "Szenario 2": 3,
        "Szenario 3": 4,
    }
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

    # font_size = 28 if len(data) == 4 else 34  # noqa: ERA001
    grid_left = "15%" if title == "Emissionen" else "5%"

    # Construct the ECharts option
    return {
        "grid": {
            "left": grid_left,
            "right": "0%",
            "top": "0%",
            "bottom": "0%",
            "containLabel": True,
        },
        "xAxis": {
            "type": "value",
            "axisLabel": {"show": False},
            "splitLine": {"show": False},
        },
        "yAxis": {
            "type": "category",
            "data": y_axis_categories,
            "axisLine": {"show": False},
            "axisLabel": {"show": True},
            "axisTick": {"show": False},
        },
        "series": [
            {
                "data": series_data,
                "type": "bar",
                "label": {
                    "show": True,
                    "position": "right",
                    # "formatter": f"({{ value }}) => `${{value.toLocaleString('de-DE')}} {unit}`",    # noqa: ERA001
                    # "fontSize": font_size,    # noqa: ERA001
                    "fontWeight": "bold",
                    "align": "right",
                    "offset": [-10, 0],
                },
            },
        ],
    }
