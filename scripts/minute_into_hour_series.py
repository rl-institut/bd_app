from pathlib import Path

import pandas as pd

directory = Path("building_dialouge_webapp/data/profiles")
date = "2023-01-01"  # Dummy date for timestamp column

for filename in directory:
    if filename.endswith(".csv"):
        file_path = filename

        # Read the first row to get column names
        with file_path.open(encoding="utf-8") as f:
            first_line = f.readline().strip()
            column_names = first_line.split(",")

        # Read the CSV again, skipping the first row
        df_original = pd.read_csv(file_path, skiprows=1, names=column_names)

        # Generate a timestamp column
        df_original.index = pd.date_range(start=date, periods=len(df_original), freq="min")
        """  MEAN: all timeseries containing "COP", boiler, pv, sth_heat
        SUM: heat, hotwater, load, sth_load """
        mean_profiles = ["_cop_", "_boiler_", "_PV_", "_STH_heat_"]
        sum_profiles = ["profile_heat_", "_hotwater_", "_load_"]
        for designation in mean_profiles:
            if designation in filename:
                df_resampled = df_original.resample("h").mean(numeric_only=True)
        for designation in sum_profiles:
            if designation in filename:
                df_resampled = df_original.resample("h").sum(numeric_only=True)

        # Remove the timestamp index and reset it to match the original format
        df_resampled.reset_index(drop=True)

        # Save back to CSV (preserving the original column names)
        output_path = directory / f"hourly_{filename}"
        df_resampled.to_csv(output_path, index=False)

        print(f"Processed and saved: {output_path}")  # Noqa: T201
