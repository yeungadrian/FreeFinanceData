"""
This is a boilerplate pipeline 'data_processing'
generated using Kedro 0.17.0
"""

import pandas as pd
import psycopg2 as pg
from dotenv import load_dotenv
import os
import requests

load_dotenv()

import asyncio


def background(f):
    def wrapped(*args, **kwargs):
        return asyncio.get_event_loop().run_in_executor(None, f, *args, **kwargs)

    return wrapped


@background
def load_kline_data(symbol, columns):
    kline_url = (
        f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval=1m&limit=1"
    )
    r = requests.get(url=kline_url)
    data = r.json()
    df = pd.DataFrame(data[0][:-1]).transpose()

    df.columns = columns
    df["StartTime"] = pd.to_datetime(df["StartTime"], utc=True, unit="ms").dt.strftime(
        "%Y-%m-%d %H:%M:%S"
    )
    (df["EndTime"],) = pd.to_datetime(df["EndTime"], utc=True, unit="ms").dt.strftime(
        "%Y-%m-%d %H:%M:%S"
    )
    df[
        [
            "Open",
            "High",
            "Low",
            "Close",
            "Volume",
            "QuoteVolume",
            "BuyBaseVolume",
            "BuyQuoteVolume",
        ]
    ] = df[
        [
            "Open",
            "High",
            "Low",
            "Close",
            "Volume",
            "QuoteVolume",
            "BuyBaseVolume",
            "BuyQuoteVolume",
        ]
    ].apply(
        pd.to_numeric
    )
    df.insert(loc=0, column="Symbol", value=symbol)
    data = tuple(df.loc[0])

    db_name = os.getenv("DATABASE")
    host = os.getenv("HOST")
    user = os.getenv("POSTUSER")
    password = os.getenv("POSTPASSWORD")
    port = os.getenv("PORT")

    conn = pg.connect(
        dbname=db_name, user=user, password=password, host=host, port=port,
    )

    query = """
        INSERT INTO kline
        (symbol, starttime, open, high, low, close, volume, endtime, quotevolume, numtrades, buybasevolume, buyquotevolume)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """

    # try to execute query
    # context manager automatically rolls back failed transactions
    try:
        cursor = conn.cursor()
        cursor.execute(query=query, vars=data)
        conn.commit()

    # ensure connection is closed
    finally:
        conn.close()


def load_timeseries(hello: str):
    """Preprocesses the data for shuttles.

    Args:
        shuttles: Raw data.
    Returns:
        Preprocessed data, with `price` converted to a float and `d_check_complete`,
        `moon_clearance_complete` converted to boolean.
    """
    columns = [
        "StartTime",
        "Open",
        "High",
        "Low",
        "Close",
        "Volume",
        "EndTime",
        "QuoteVolume",
        "NumTrades",
        "BuyBaseVolume",
        "BuyQuoteVolume",
    ]

    symbol_list = [
        "BTCUSDT",
        "ETHUSDT",
        "BNBUSDT",
        "BCCUSDT",
        "NEOUSDT",
        "LTCUSDT",
        "QTUMUSDT",
        "ADAUSDT",
        "XRPUSDT",
        "EOSUSDT",
        "TUSDUSDT",
        "IOTAUSDT",
        "XLMUSDT",
        "ONTUSDT",
        "TRXUSDT",
        "ETCUSDT",
        "ICXUSDT",
        "VENUSDT",
        "NULSUSDT",
        "VETUSDT",
    ]

    for symbol in symbol_list:
        load_kline_data(symbol, columns)

    return "Loaded Some Data"

