import pathlib

import geopandas
import numpy as np
import pandas as pd
from tqdm import tqdm

from constants import *
from data_manipulation_functions import extract_season, extract_month
from etl_population_density import population_density_Lappeenranta
from geoanalysis_functions import read_shp, read_parquet


# --------------------------------------------------------------------
def add_geometry(
        df: pd.DataFrame,
        path: str | pathlib.PosixPath | pathlib.Path,
        crs: int | str = 3067
) -> geopandas.GeoDataFrame:
    """
    Add the geometry to the Telia's data based on the associated grid.

    Parameters
    ----------
    df: pd.DataFrame
            Telia's dataset
    path: str or pathlib.PosixPath or pathlib.Path
            path of the data directory
    crs: int or str
            the desired output CRS (default: 3067)

    Returns
    -------
    geopandas.GeoDataFrame
            Telia's data with the associated geometry
    """
    filename = pathlib.Path(path) / "finland_telia_grid_EPSG3067.gpkg"
    grid = read_shp(filename, crs=crs)
    merged = df.merge(grid, how="inner", left_on=df.columns[0],
                      right_on="location_id")

    return geopandas.GeoDataFrame(merged, geometry=merged['geometry'])


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
def read_Lappeenranta(
        *,
        time_period: tuple[int, int] = (0, 24),
        month: int | None = None,
        season: str | None = None,
        weekdays: bool = True,
        crs: int | str = 3067
) -> geopandas.GeoDataFrame:
    """
    Read the Telia's dataset and extract the data corresponding to
    the area surrounding Lappeenranta.

    Parameters
    ----------
    time_period: tuple of int
            starting hour and ending hour to extract
    month: int
            month of interest
    season: str
            season of interest
    weekdays: bool
            specify whether to extract the weekdays or the weekend
    crs: int or str
            the desired output CRS (default: 3067)

    Returns
    -------
    geopandas.GeoDataFrame
            Telia's data for the surroundings of Lappeenranta with
            the associated geometry
    """
    municipalities = read_shp(MUNICIPALITIES_DATA, crs=crs)
    sub_area = municipalities[municipalities['NAMEFIN'].isin(LAPPEENRANTA)]

    print("    Read Telia trip data")
    telia_df = read_parquet(TELIA_TRIPS_DATA_DIRECTORY / "trips_grid_hourly_ekarjala_2025.parquet")
    telia_df = telia_df.rename(columns={"observation_start_date": "observation_start_datetime"})
    telia_df = telia_df.rename(columns={"observation_end_date": "observation_end_datetime"})

    print("    Extract the time period")
    if month is not None:
        month_df = extract_month(telia_df, month)
        sub_df = extract_time_period(month_df, time_period, weekdays)
        sub_df = month_df.copy()
    elif season is not None:
        season_df = extract_season(telia_df, season)
        sub_df = extract_time_period(season_df, time_period, weekdays)
        sub_df = season_df.copy()
    else:
        sub_df = telia_df.copy()

    print("    Extract Lappeenranta area")
    origins = add_geometry(sub_df[['location_id_origin']],
                           TELIA_TRIPS_DATA_DIRECTORY, crs)
    destinations = add_geometry(sub_df[['location_id_destination']],
                                TELIA_TRIPS_DATA_DIRECTORY, crs)
    sub_orig = geopandas.sjoin(origins, sub_area[['NAMEFIN', 'geometry']], how="inner", predicate="intersects")
    sub_dest = geopandas.sjoin(destinations, sub_area[['NAMEFIN', 'geometry']], how="inner", predicate="intersects")

    sub_telia = sub_df[(sub_df['location_id_origin'].isin(sub_orig['location_id_origin'].to_list())) |
                       (sub_df['location_id_destination'].isin(sub_dest['location_id_destination'].to_list()))]

    return sub_telia


# --------------------------------------------------------------------
def average_number_car(
        gdf: geopandas.GeoDataFrame,
        weekdays: bool = True
) -> geopandas.GeoDataFrame:
    print("    Derive the average number of cars")
    if weekdays:
        gdf['nb_cars'] = gdf['total_visits'] * FRACTION_CARS_PER_TRIPS / AVERAGE_CAR_OCCUPANCY[0]
    else:
        gdf['nb_cars'] = gdf['total_visits'] * FRACTION_BIKES_PER_TRIPS / AVERAGE_CAR_OCCUPANCY[1]

    return gdf


# --------------------------------------------------------------------
def average_number_bikes(
        gdf: geopandas.GeoDataFrame,
) -> geopandas.GeoDataFrame:
    print("    Derive the average number of bikes")
    gdf['nb_bikes'] = gdf['total_visits'] * FRACTION_BIKES

    return gdf


# --------------------------------------------------------------------
def baseline_number_cars(
        *,
        weekdays: bool = True,
        crs: int | str = 3067,
) -> geopandas.GeoDataFrame:
    """
    Derive the initial number of cars based on the population density at night
    (from 22 to 6) multiplied by the average number of cars per person.

    Parameters
    ----------
    weekdays: bool
            specify whether to extract the weekdays or the weekend
    crs: int or str
            the desired output CRS (default: 3067)

    Returns
    -------
    geopandas.GeoDataFrame
            distribution of cars by night (used as baseline)
    """
    night_population = population_density_Lappeenranta(time_period=(22, 6),
                                                       weekdays=weekdays, crs=crs)[0]
    night_population['initial_nb_cars'] = night_population['total_visits'] * NB_CARS_PER_PERSON

    return night_population[['initial_nb_cars', 'location_id', 'geometry']]


# --------------------------------------------------------------------
def number_cars_Lappeenranta(
        *,
        weekdays: bool = True,
        crs: int | str = 3067,
) -> geopandas.GeoDataFrame:
    """
    Read the Telia's dataset and extract the data corresponding to
    the area surrounding Lappeenranta.

    Parameters
    ----------
    weekdays: bool
            specify whether to extract the weekdays or the weekend
    crs: int or str
            the desired output CRS (default: 3067)

    Returns
    -------
    geopandas.GeoDataFrame
            Telia's data for the surroundings of Lappeenranta with
            the associated geometry
    MultiDiGraph
            OpenStreetMap graph for the area covered by the return Telia data
    """
    print('Read data')
    sub_telia = read_Lappeenranta(time_period=(4, 6), season="spring", weekdays=weekdays, crs=crs)

    # print('  Derive population density')
    # population_density = average_population_density(sub_telia, time_period=(4, 6))

    return sub_telia

# --------------------------------------------------------------------
