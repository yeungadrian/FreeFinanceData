"""
This is a boilerplate pipeline 'data_processing'
generated using Kedro 0.17.0
"""

from dotenv import load_dotenv
import numpy as np
import os
import pandas as pd
import psycopg2 as pg
from scipy.interpolate import PchipInterpolator

load_dotenv()


def interpolate_curve(curve):
    curve = curve.iloc[1:]
    curve.columns = ["tenor", "value"]
    curve.loc[:, "tenor"] = [1, 2, 3, 6, 12, 24, 36, 60, 90, 120, 240, 360]

    curve = curve.dropna()

    g = PchipInterpolator(curve["tenor"], curve["value"], extrapolate=True)
    tenors = np.linspace(0, 360, 61, endpoint=True)
    values = g(tenors)

    return tenors, values


def historical_us_treasury_curves(hello:str):

    db_name = os.getenv("DATABASE")
    host = os.getenv("HOST")
    user = os.getenv("POSTUSER")
    password = os.getenv("POSTPASSWORD")
    port = os.getenv("PORT")

    all_treasuries = pd.read_csv(
        "https://home.treasury.gov/system/files/276/yield-curve-rates-1990-2021.csv"
    )

    all_treasuries.Date = pd.to_datetime(all_treasuries.Date)

    for i in range(all_treasuries.shape[0]):
        treasury_curve = all_treasuries.iloc[i]
        old_treasury = treasury_curve.reset_index()
        curve_date = treasury_curve.Date.strftime('%Y-%m-%d')

        tenors, values = interpolate_curve(old_treasury)

        curve_data = pd.DataFrame(
            {"tenor": tenors, "value": values}
        )

        curve_data["tenor"] = curve_data["tenor"] / 12
        curve_data["value"] = curve_data["value"] / 100.0
        
        curve_values = list(
            zip(
                np.tile("us_treasury", curve_data.shape[0]),
                np.tile(curve_date, curve_data.shape[0]),
                curve_data["tenor"],
                curve_data["value"],
            )
        )

        for j in curve_values:
            query = """
                INSERT INTO curve
                (curve_name, date, tenor, value)
                VALUES (%s,%s,%s,%s)
                """

            conn = pg.connect(
                dbname=db_name, user=user, password=password, host=host, port=port,
            )

            # try to execute query
            # context manager automatically rolls back failed transactions
            try:
                cursor = conn.cursor()
                cursor.execute(query=query, vars=j)
                conn.commit()

            # ensure connection is closed
            finally:
                conn.close()
            