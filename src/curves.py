import logging
import os

import numpy as np
import pandas as pd
import psycopg2 as pg
from dotenv import load_dotenv
from scipy.interpolate import PchipInterpolator

load_dotenv()


def interpolate_curve(curve, curve_date):
    curve = curve.iloc[1:].copy()
    curve.columns = ["maturity", "value"]
    curve["tenor"] = [1, 2, 3, 6, 12, 24, 36, 60, 90, 120, 240, 360]

    curve = curve.dropna()

    g = PchipInterpolator(curve["tenor"], curve["value"], extrapolate=True)
    tenors = np.linspace(0, 360, 31, endpoint=True)
    values = g(tenors)

    curve_data = pd.DataFrame({"tenor": tenors, "value": values})

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

    return curve_values


def insert_curve(values):
    db_name = os.getenv("DATABASE")
    host = os.getenv("HOST")
    user = os.getenv("POSTUSER")
    password = os.getenv("POSTPASSWORD")
    port = os.getenv("PORT")

    query = """
        INSERT INTO curve
        (curve_name, date, tenor, value)
        VALUES (%s,%s,%s,%s)
        """

    conn = pg.connect(
        dbname=db_name,
        user=user,
        password=password,
        host=host,
        port=port,
    )

    # try to execute query
    # context manager automatically rolls back failed transactions
    try:
        cursor = conn.cursor()
        cursor.execute(query=query, vars=values)
        conn.commit()

    # ensure connection is closed
    finally:
        conn.close()


def load_curves(mapping):
    last_business_day = pd.Timestamp.today() - pd.offsets.BMonthEnd(1)
    current_year = last_business_day.year
    current_month = last_business_day.month

    hist_treasury = pd.read_csv(
        mapping["treasury"]["old"].replace("2021", str(current_year - 1))
    )

    hist_treasury["Date"] = pd.to_datetime(hist_treasury["Date"])

    latest_treasury = [hist_treasury]
    for i in range(1, current_month + 1):
        month = str(i)
        if len(month) == 1:
            month = "0" + month
        url = mapping["treasury"]["daily"].replace(
            "202207", str(current_year) + month
        )
        treasury = pd.read_csv(url)
        treasury["Date"] = pd.to_datetime(treasury["Date"])
        latest_treasury.append(treasury)

    all_treasuries = pd.concat(latest_treasury).reset_index(drop=True)

    return all_treasuries


def historical_us_treasury(mapping):

    all_treasuries = load_curves(mapping)

    for i in range(all_treasuries.shape[0]):
        treasury = all_treasuries.iloc[i]
        treasury = treasury.reset_index()
        curve_date = all_treasuries.Date.iloc[i].strftime("%Y-%m-%d")

        curve_values = interpolate_curve(treasury, curve_date)
        logging.info("Inserting US treasury for %s", curve_date)
        for j in curve_values:
            insert_curve(j)


def daily_us_treasury(mapping):

    last_business_day = (
        pd.Timestamp.today() - pd.offsets.BMonthEnd(1)
    ).strftime("%Y-%m-%d")

    all_treasuries = load_curves(mapping)

    curve = (
        all_treasuries.loc[all_treasuries.Date == last_business_day]
        .transpose()
        .reset_index()
    )
    curve_date = last_business_day

    curve_values = interpolate_curve(curve, curve_date)

    logging.info("Inserting US treasury for %s", curve_date)

    for j in curve_values:
        insert_curve(j)
