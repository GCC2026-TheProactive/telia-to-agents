import pandas as pd

SEASON_TO_MONTHS = {
    'spring': [3, 4, 5],
    'summer': [6, 7, 8],
    'fall': [9, 10, 11],
    'autumn': [9, 10, 11],
    'winter': [12, 1, 2]
}


# --------------------------------------------------------------------
def extract_season(
        df: pd.DataFrame,
        season: str = 'spring'
) -> pd.DataFrame:
    """
    Extract the Telia's data corresponding to the given season.

    Parameters
    ----------
    df: pd.DataFrame
            Telia's data for the region of interest with
            the associated geometry
    season: str
            season of interest

    Returns
    -------
    pd.DataFrame
            Telia's data for the season of interest
    """
    month = df['observation_start_datetime'].dt.month

    return df[month.isin(SEASON_TO_MONTHS[season])]


# --------------------------------------------------------------------
def extract_month(
        df: pd.DataFrame,
        month: int
) -> pd.DataFrame:
    """
    Extract the Telia's data corresponding to a given month.

    Parameters
    ----------
    df: pd.DataFrame
            Telia's data for the region of interest with
            the associated geometry
    month: int
            month of interest

    Returns
    -------
    pd.DataFrame
            Telia's data for the month of interest
    """

    return df[df['observation_start_datetime'].dt.month == month]


# --------------------------------------------------------------------
def extract_time_period(
        df: pd.DataFrame,
        time_period: tuple[int, int] = (0, 24),
        weekdays: bool = True,
) -> pd.DataFrame:
    """
    Extract the time period during the day and the week from
    the Telia data.

    Parameters
    ----------
    df: pd.DataFrame
            Telia's data for the region of interest with
            the associated geometry
    time_period: tuple of int
            starting hour and ending hour to extract
    weekdays: bool
            specify whether to extract the weekdays or the weekend

    Returns
    -------
    pd.DataFrame
            Telia's data for the time period of interest
    """
    hour = df['observation_start_datetime'].dt.hour

    if time_period[0] < time_period[1]:
        sub_df = df[(time_period[0] <= hour) & (hour < time_period[1])]
    elif time_period[0] > time_period[1]:
        sub_df = df[(time_period[1] <= hour) | (hour < time_period[0])]
    elif time_period[0] == time_period[1]:
        sub_df = df[(hour == time_period[0])]

    if weekdays:
        return sub_df[sub_df['observation_start_datetime'].dt.weekday <= 4]
    else:
        return sub_df[sub_df['observation_start_datetime'].dt.weekday > 4]

# --------------------------------------------------------------------
