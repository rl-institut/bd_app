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

    title_top = "0%"
    rotate = 0
    if title == "CO2-Kosten in € pro Jahr":
        rotate = 45
        title_top = "0%"

    return {
        "grid": {
            "containLabel": True,
        },
        "xAxis": {
            "type": "value",
            "axisLabel": {
                "show": True,
                "color": "#b3b4b2",
                "rotate": rotate,
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
                    "fontWeight": "bold",
                    "align": "right",
                    "offset": [-20, 0],
                },
            },
        ],
    }
