from typing import Optional, Tuple, TypeVar, Union

import pandas as pd

PandasTime = TypeVar("PandasTime", Union[pd.Timedelta, pd.Timestamp])


def round_td(td: PandasTime, freq: str, method: Optional[str]) -> PandasTime:
    """
    Rounds up / down / off a pd.Timedelta

        :param td: timedelta object
        :param freq: offset alias / frequency string
        (see https://pandas.pydata.org/pandas-docs/stable/user_guide/timeseries.html)
        :param method (up = round up, down = round down, others = round off)
    """

    rounded = td.round(freq=freq)
    span = pd.Timedelta(freq)

    if rounded < td and method == "up":
        rounded = (td + span).round(freq=freq)
    elif rounded > td and method == "down":
        rounded = (td - span).round(freq=freq)

    return rounded


def parse_td(td_str: str) -> pd.Timedelta:
    ts = pd.Timestamp(td_str)
    return round_td(ts - ts.round("D"))


def parse_period(period_strs: str) -> Tuple[pd.Timedelta, pd.Timedelta]:
    start_str, end_str = [
        period_str.strip() for period_str in period_strs.split("to")
    ][:2]
