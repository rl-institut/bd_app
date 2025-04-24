def generate_grouped_echarts_option(scenarios, title, series_names):
    default_colors = ["#b3de69", "#fb8072"]  # electricity and heating colors

    # Sorting
    order = {"Ausgangszustand": 1, "Szenario 1": 2, "Szenario 2": 3, "Szenario 3": 4}
    sorted_scenarios = sorted(scenarios, key=lambda x: order.get(x["name"], 5))

    y_axis_data = [s["name"] for s in reversed(sorted_scenarios)]

    # Prepare data for each series
    values_1 = [s["value"][0] for s in reversed(sorted_scenarios)]
    values_2 = [s["value"][1] for s in reversed(sorted_scenarios)]

    series = [
        {
            "name": series_names[0],
            "type": "bar",
            "data": values_1,
            "itemStyle": {"color": default_colors[0]},
            "label": {
                "show": True,
                "position": "right",
                "fontWeight": "bold",
            },
        },
        {
            "name": series_names[1],
            "type": "bar",
            "data": values_2,
            "itemStyle": {"color": default_colors[1]},
            "label": {
                "show": True,
                "position": "right",
                "fontWeight": "bold",
            },
        },
    ]

    return {
        "tooltip": {"trigger": "axis", "axisPointer": {"type": "shadow"}},
        "legend": {"data": series_names},
        "grid": {"containLabel": True},
        "xAxis": {
            "type": "value",
            "axisLabel": {"color": "#b3b4b2"},
            "splitLine": {"show": True},
        },
        "yAxis": {
            "type": "category",
            "data": y_axis_data,
            "axisLine": {"show": False},
            "axisLabel": {"show": True},
            "axisTick": {"show": False},
        },
        "series": series,
    }
