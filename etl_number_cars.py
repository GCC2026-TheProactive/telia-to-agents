import pathlib

import geopandas
import numpy as np
import pandas as pd
from tqdm import tqdm

from constants import *
from data_manipulation_functions import extract_season, extract_month, extract_time_period
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
def read_Lappeenranta(
        *,
        month: int | None = None,
        season: str | None = None,
        crs: int | str = 3067
) -> geopandas.GeoDataFrame:
    """
    Read the Telia's dataset and extract the data corresponding to
    the area surrounding Lappeenranta.

    Parameters
    ----------
    month: int
            month of interest
    season: str
            season of interest
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
        sub_df = month_df.copy()
    elif season is not None:
        season_df = extract_season(telia_df, season)
        sub_df = season_df.copy()
    else:
        sub_df = telia_df.copy()

    print("    Extract Lappeenranta area")
    origins = add_geometry(sub_df[['location_id_origin']],
                           TELIA_TRIPS_DATA_DIRECTORY, crs)
    destinations = add_geometry(sub_df[['location_id_destination']],
                                TELIA_TRIPS_DATA_DIRECTORY, crs)
    sub_orig = geopandas.sjoin(origins, sub_area[['NAMEFIN', 'geometry']], how="inner", predicate="within")
    sub_dest = geopandas.sjoin(destinations, sub_area[['NAMEFIN', 'geometry']], how="inner", predicate="within")

    sub_telia = sub_df[(sub_df['location_id_origin'].isin(sub_orig['location_id_origin'].to_list())) |
                       (sub_df['location_id_destination'].isin(sub_dest['location_id_destination'].to_list()))]

    return sub_telia


# --------------------------------------------------------------------
def baseline_number_cars(
        *,
        population_night,
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
    population_night['initial_nb_cars'] = population_night['total_visits'] * NB_CARS_PER_PERSON

    return population_night[['initial_nb_cars', 'location_id', 'geometry']]


# --------------------------------------------------------------------
def average_number_cars(
        df: pd.DataFrame,
        *,
        population_night,
        time_period: tuple[int, int] = (0, 24),
        weekdays: bool = True,
) -> geopandas.GeoDataFrame:
    """
    Estimate the average number of cars available during the time period.

    Parameters
    ----------
    df: pd.DataFrame
            Telia's data for the surroundings of Lappeenranta with
            the associated geometry
    time_period: tuple of int
            starting hour and ending hour to extract
    weekdays: bool
            specify whether to extract the weekdays or the weekend
    crs: int or str
            the desired output CRS (default: 3067)

    Returns
    -------
    geopandas.GeoDataFrame
            distribution of cars
    """
    print("    Derive initial number of cars")
    number_cars = baseline_number_cars(population_night=population_night)

    if time_period[0] < time_period[1]:
        hours = np.arange(time_period[0], time_period[1] + 1, 1)
    else:
        hours = np.concat((np.arange(time_period[0], 24 + 1, 1),
                           np.arange(time_period[1] + 1)))
    index_nights = np.where(np.isin(hours, NIGHT_HOURS))
    hours_days = np.delete(hours, index_nights)

    print("    Extract hourly variations since 6:00")
    for hour in tqdm(range(6, max(hours_days) + 1, 1), leave=False):
        sub_df = extract_time_period(df, time_period=(hour, hour), weekdays=weekdays)
        for idx, row in number_cars.iterrows():
            cell_id = number_cars.loc[idx, 'location_id']
            exiting_cars = sub_df[(sub_df['location_id_origin'] == cell_id) &
                                  (sub_df['mode_of_transport'] == 'Road')]['trip_count'].mean()
            arriving_cars = sub_df[(sub_df['location_id_destination'] == cell_id) &
                                   (sub_df['mode_of_transport'] == 'Road')]['trip_count'].mean()
            number_cars.loc[idx, f'variation_{hour}h'] = arriving_cars - exiting_cars

    print("    Derive the hourly number of cars")
    for hour in hours_days:
        list_entries = [f'variation_{h}h' for h in range(6, hour, 1)]
        number_cars[f'nb_cars_{hour}h'] = number_cars['initial_nb_cars'] + number_cars[list_entries].sum(axis=1)

    print("    Derive the average number of cars")
    list_entries = [name for name in number_cars if 'nb_cars_' in name]
    number_cars['total_nb_cars'] = number_cars[list_entries].mean(axis=1)

    ENTRIES_CARS = ['location_id', 'initial_nb_cars'] + list_entries + ['total_nb_cars', 'geometry']

    gdf = geopandas.GeoDataFrame(number_cars[ENTRIES_CARS], geometry=number_cars['geometry'])

    return gdf


# --------------------------------------------------------------------
def average_number_car_old(
        gdf: geopandas.GeoDataFrame,
        weekdays: bool = True
) -> geopandas.GeoDataFrame:
    print("    Derive the average number of cars")
    if weekdays:
        gdf['nb_cars'] = gdf['total_visits'] * FRACTION_CARS_PER_TRIPS / AVERAGE_CAR_OCCUPANCY[0]
    else:
        gdf['nb_cars'] = gdf['total_visits'] * FRACTION_CARS_PER_TRIPS / AVERAGE_CAR_OCCUPANCY[1]

    return gdf


# --------------------------------------------------------------------
def average_number_bikes(
        gdf: geopandas.GeoDataFrame,
) -> geopandas.GeoDataFrame:
    print("    Derive the average number of bikes")
    gdf['nb_bikes'] = gdf['total_visits'] * FRACTION_BIKES_PER_TRIPS

    return gdf


# --------------------------------------------------------------------
def number_cars_Lappeenranta(
        population_night,
        *,
        time_period: tuple[int, int] = (0, 24),
        month: int | None = None,
        season: str | None = None,
        weekdays: bool = True,
        crs: int | str = 3067,
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
    print('  Read data')
    sub_telia = read_Lappeenranta(month=month, season=season, crs=crs)

    print('  Derive number of cars')
    number_cars = average_number_cars(sub_telia, population_night=population_night, time_period=time_period)

    return number_cars

# --------------------------------------------------------------------
