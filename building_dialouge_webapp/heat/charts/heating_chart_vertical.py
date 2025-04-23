def generate_vertical_echarts_option(months, scenarios, title, y_axis_label="Wert"):
    """
    Generates a vertical grouped bar chart for multiple scenarios across months.

    :param months: List of month labels (e.g., ["Jan", "Feb", ..., "Dez"])
    :param scenarios: List of scenario dicts:
                      [
                        {"name": "Szenario 1", "values": [..], "color": "#aabbcc"},
                        {"name": "Szenario 2", "values": [..], "color": "#ddeeff"},
                      ]
    :param title: Chart title.
    :param y_axis_label: Label for y-axis (e.g., "Heizwärmebedarf in kWh")
    """
    series = [
        {
            "name": scenario["name"],
            "type": "bar",
            "data": scenario["values"],
            "itemStyle": {
                "color": scenario.get("color", "#999999"),
            },
            "label": {
                "show": False,
            },
            "barGap": 0,
            "barCategoryGap": "30%",  # spacing between grouped bars
        }
        for scenario in scenarios
    ]

    return {
        "legend": {
            "data": [s["name"] for s in scenarios],
            "top": "0%",
        },
        "tooltip": {
            "trigger": "axis",
            "axisPointer": {"type": "shadow"},
        },
        "xAxis": {
            "type": "category",
            "data": months,
            "axisLabel": {
                "color": "#6e6e6e",
            },
        },
        "yAxis": {
            "type": "value",
            "name": y_axis_label,
            "axisLabel": {
                "color": "#b3b4b2",
            },
            "splitLine": {
                "lineStyle": {"color": "#f0f0f0"},
            },
        },
        "title": {
            "text": title,
            "left": "0%",
            "top": "5%",
            "textStyle": {
                "fontWeight": "normal",
                "color": "#6e6e6e",
            },
        },
        "grid": {
            "containLabel": True,
            "top": "15%",
        },
        "series": series,
    }
