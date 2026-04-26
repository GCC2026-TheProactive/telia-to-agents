import pandas as pd

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

    if season == 'spring':
        return df[month.isin([3, 4, 5])]
    elif season == 'summer':
        return df[month.isin([6, 7, 8])]
    elif season in ['fall', 'autumn']:
        return df[month.isin([9, 10, 11])]
    elif season == 'winter':
        return df[month.isin([12, 1, 2])]


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
