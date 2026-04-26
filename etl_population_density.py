import pathlib

import geopandas
import osmnx
import pandas as pd
from networkx.classes.multidigraph import MultiDiGraph

from constants import *
from geoanalysis_functions import read_shp, read_parquet
from data_manipulation_functions import extract_season, extract_month

ENTRIES_VISITS = ['visit_count', 'resident_visit_count', 'worker_visit_count',
                  'non_resident_non_worker_visit_count']


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
    gdf = read_shp(filename, crs=crs)
    merged = df.merge(gdf, how="inner", on="location_id")

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
    geopandas.GeoDataFrame
            Telia's data for the time period of interest
    """
    hour = df['observation_start_datetime'].dt.hour

    if time_period[0] < time_period[1]:
        sub_gdf = df[(time_period[0] <= hour) & (hour < time_period[1])]
    elif time_period[0] > time_period[1]:
        sub_gdf = df[(time_period[1] <= hour) | (hour < time_period[0])]
    elif time_period[0] == time_period[1]:
        sub_gdf = df[(hour == time_period[0])]

    if weekdays:
        return sub_gdf[sub_gdf['observation_start_datetime'].dt.weekday <= 4]
    else:
        return sub_gdf[sub_gdf['observation_start_datetime'].dt.weekday > 4]


# --------------------------------------------------------------------
def read_capital_area(
        *,
        time_period: tuple[int, int] = (0, 24),
        month: int | None = None,
        season: str | None = None,
        weekdays: bool = True,
        crs: int | str = 3067,
        download_osm: bool = False
) -> tuple[geopandas.GeoDataFrame, MultiDiGraph]:
    """
    Read the Telia's dataset and extract the data corresponding to
    the capital area.

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
    download_osm: bool
            specify whether to download the OSM data (default: False)

    Returns
    -------
    geopandas.GeoDataFrame
            Telia's data for the capital area with the associated
            geometry
    MultiDiGraph
            OpenStreetMap graph for the area covered by the return Telia data
    """
    municipalities = read_shp(MUNICIPALITIES_DATA, crs=crs)
    sub_area = municipalities[municipalities['NAMEFIN'].isin(CAPITAL_AREA)]

    print("    Read Telia visit data")
    telia_df = read_parquet(TELIA_VISITS_DATA_DIRECTORY / "hourly_visits_uusimaa_2025.parquet")
    telia_df = telia_df.rename(columns={"observation_start_date": "observation_start_datetime"})
    telia_df = telia_df.rename(columns={"observation_end_date": "observation_end_datetime"})

    print("    Extract the time period")
    if month is not None:
        month_df = extract_month(telia_df, month)
        sub_df = extract_time_period(month_df, time_period, weekdays)
    elif season is not None:
        season_df = extract_season(telia_df, season)
        sub_df = extract_time_period(season_df, time_period, weekdays)
    else:
        sub_df = telia_df.copy()

    print("    Extract the sub area")
    sub_gdf = add_geometry(sub_df, TELIA_VISITS_DATA_DIRECTORY, crs)
    sub_telia = geopandas.sjoin(sub_gdf, sub_area[['NAMEFIN', 'geometry']], how="inner", predicate="intersects")

    if download_osm:
        print("    Download OSM data")
        osmnx.settings.all_oneway = True
        graph = osmnx.graph.graph_from_polygon(sub_area.to_crs("EPSG:4326").geometry.union_all(), simplify=False)
        osmnx.io.save_graphml(graph, filepath=OUTPUT_DIRECTORY / "Capital_area_osm.graphml")
        osmnx.io.save_graph_geopackage(graph, filepath=OUTPUT_DIRECTORY / "Capital_area_osm.gpkg")
    else:
        graph = None

    return sub_telia, graph


# --------------------------------------------------------------------
def read_Lappeenranta(
        *,
        time_period: tuple[int, int] = (0, 24),
        month: int | None = None,
        season: str | None = None,
        weekdays: bool = True,
        crs: int | str = 3067,
        download_osm: bool = False
) -> tuple[geopandas.GeoDataFrame, MultiDiGraph]:
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
    download_osm: bool
            specify whether to download the OSM data (default: False)

    Returns
    -------
    geopandas.GeoDataFrame
            Telia's data for the surroundings of Lappeenranta with
            the associated geometry
    MultiDiGraph
            OpenStreetMap graph for the area covered by the return Telia data
    """
    municipalities = read_shp(MUNICIPALITIES_DATA, crs=crs)
    sub_area = municipalities[municipalities['NAMEFIN'].isin(LAPPEENRANTA)]

    print("    Read Telia visit data")
    telia_df = read_parquet(TELIA_VISITS_DATA_DIRECTORY / "hourly_visits_eKarjala_Kymenlaakso_2025.parquet")
    telia_df = telia_df.rename(columns={"observation_start_date": "observation_start_datetime"})
    telia_df = telia_df.rename(columns={"observation_end_date": "observation_end_datetime"})

    print("    Extract the time period")
    if month is not None:
        month_df = extract_month(telia_df, month)
        sub_df = extract_time_period(month_df, time_period, weekdays)
    elif season is not None:
        season_df = extract_season(telia_df, season)
        sub_df = extract_time_period(season_df, time_period, weekdays)
    else:
        sub_df = telia_df.copy()

    print("    Extract the sub area")
    sub_gdf = add_geometry(sub_df, TELIA_VISITS_DATA_DIRECTORY, crs)
    sub_telia = geopandas.sjoin(sub_gdf, sub_area[['NAMEFIN', 'geometry']], how="inner", predicate="intersects")

    if download_osm:
        print("    Download OSM data")
        osmnx.settings.all_oneway = True
        graph = osmnx.graph.graph_from_polygon(sub_area.to_crs("EPSG:4326").geometry.union_all(), simplify=False)
        osmnx.io.save_graphml(graph, filepath=OUTPUT_DIRECTORY / "Lappeenranta_osm.graphml")
        osmnx.io.save_graph_geopackage(graph, filepath=OUTPUT_DIRECTORY / "Lappeenranta_osm.gpkg")
    else:
        graph = None

    return sub_telia, graph


# --------------------------------------------------------------------
def average_population_density(
        gdf: geopandas.GeoDataFrame,
        time_period: tuple[int, int] = (0, 24),
) -> geopandas.GeoDataFrame:
    """
    Extract the subset of the Telia data of interest.

    Parameters
    ----------
    gdf: geopandas.GeoDataFrame
            Telia's data for the region of interest with
            the associated geometry
    time_period: tuple of int
            starting hour and ending hour to extract

    Returns
    -------
    geopandas.GeoDataFrame
            subset of Telia data
    """
    duration = time_period[1] - time_period[0]

    print('    Derive the population density')
    visits = gdf[ENTRIES_VISITS + ['geometry']]
    visits['total_visits'] = visits[ENTRIES_VISITS].sum(axis=1)
    avg_visits = visits.groupby('geometry').mean().reset_index()
    for entry in ENTRIES_VISITS + ['total_visits']:
        avg_visits[entry] = avg_visits[entry] / duration

    new_gdf = geopandas.GeoDataFrame(avg_visits, geometry=avg_visits['geometry'])

    new_gdf['area_km2'] = new_gdf.area / 1e6
    new_gdf['density'] = new_gdf['total_visits'] / new_gdf['area_km2']

    return new_gdf


# --------------------------------------------------------------------
def population_density_Lappeenranta(
        *,
        time_period: tuple[int, int] = (4, 6),
        month: int | None = None,
        season: str | None = None,
        weekdays: bool = True,
        crs: int | str = 3067,
        download_osm: bool = False
) -> tuple[geopandas.GeoDataFrame, MultiDiGraph]:
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
    download_osm: bool
            specify whether to download the OSM data (default: False)

    Returns
    -------
    geopandas.GeoDataFrame
            Telia's data for the surroundings of Lappeenranta with
            the associated geometry
    MultiDiGraph
            OpenStreetMap graph for the area covered by the return Telia data
    """
    print('  Read data')
    sub_telia, osm_graph = read_Lappeenranta(time_period=time_period, month=month, season=season, weekdays=weekdays,
                                             crs=crs, download_osm=download_osm)

    print('  Derive population density')
    population_density = average_population_density(sub_telia, time_period=time_period)

    return population_density, osm_graph

# --------------------------------------------------------------------
