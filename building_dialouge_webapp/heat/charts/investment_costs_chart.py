def generate_investment_chart_options(scenarios):
    y_axis_data = []
    renovation_data = []
    maintenance_data = []

    for scenario in reversed(scenarios):
        y_axis_data.append(scenario["name"])

        renovation_data.append(
            {
                "value": scenario["renovation"],
                "itemStyle": {
                    "color": "#80b1d3",
                },
            },
        )

        maintenance_data.append(
            {
                "value": scenario["maintenance"],
                "itemStyle": {
                    "color": "#fdb462",
                },
            },
        )

    return {
        "grid": {
            "containLabel": True,
        },
        "xAxis": {
            "type": "value",
            "axisLabel": {
                "show": True,
                "color": "#b3b4b2",
                "rotate": 45,
            },
            "splitLine": {
                "show": True,
            },
        },
        "yAxis": {
            "type": "category",
            "data": y_axis_data,
            "axisLine": {"show": False},
            "axisLabel": {
                "show": True,
            },
            "axisTick": {"show": False},
        },
        "title": {
            "text": "Zusammensetzung der Investitionskosten in €",
            "textStyle": {
                "fontWeight": "normal",
                "color": "#6e6e6e",
            },
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
                    "fontWeight": "bold",
                },
            },
            {
                "name": "Instandhaltungskosten",
                "type": "bar",
                "stack": "total",
                "data": maintenance_data,
                "label": {
                    "show": True,
                    "position": "insideRight",
                    "fontWeight": "bold",
                },
            },
        ],
    }
