import pathlib
import numpy as np
import pandas as pd
import xarray as xr
import geopandas
import duckdb
import osmnx
from geoanalysis_functions import read_shp,read_raster
from networkx.classes.multidigraph import MultiDiGraph
import matplotlib.pyplot as plt


# Paths definition
NOTEBOOK_PATH  = pathlib.Path().resolve()
DATA_DIRECTORY = NOTEBOOK_PATH / "data"
TELIA_DATA_DIRECTORY = DATA_DIRECTORY / "telia_hourly_visits"

MUNICIPALITIES_DATA = DATA_DIRECTORY / "finland_municipalities_2021.gpkg"
POPULATION_CENSUS_2021_AT_100m = (DATA_DIRECTORY / "JRC-ESTAT_Census_Population_2021_100m" /
                                  "JRC-ESTAT_Census_Population_2021_100m.tif")

CAPITAL_AREA = ['Helsinki', 'Espoo', 'Vantaa', 'Kauniainen']
LAPPEENRANTA = ['Lappeenranta', 'Imatra', 'Lemi', 'Luumäki', 'Miehikkälä','Savitaipale','Taipalsaari']

ENTRIES_VISITS = ['visit_count','resident_visit_count','worker_visit_count',
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
    gdf = read_shp(filename,crs=crs)
    merged = df.merge(gdf,how="inner",on="location_id")

    return geopandas.GeoDataFrame(merged,geometry=merged['geometry'])


# --------------------------------------------------------------------
def read_parquet(
        filename: str | pathlib.PosixPath | pathlib.Path,
        crs: int | str = 3067
) -> geopandas.GeoDataFrame:
    """
    Read the Telia's dataset, add the geometry of the grid and return
    the data into a GeoDataFrame.

    Parameters
    ----------
    filename: str or pathlib.PosixPath or pathlib.Path
            path of the input file
    crs: int or str
            the desired output CRS (default: 3067)

    Returns
    -------
    geopandas.GeoDataFrame
            Telia's data with the associated geometry
    """
    filename = pathlib.Path(filename)
    df = duckdb.sql(f"""SELECT
                           *
                        FROM
                           '{filename}'
                     """).df()

    return add_geometry(df,TELIA_DATA_DIRECTORY,crs)

# --------------------------------------------------------------------
def read_capital_area(
        crs: int | str = 3067
) -> tuple[geopandas.GeoDataFrame,MultiDiGraph]:
    """
    Read the Telia's dataset and extract the data corresponding to
    the capital area.

    Parameters
    ----------
    crs: int or str
            the desired output CRS (default: 3067)

    Returns
    -------
    geopandas.GeoDataFrame
            Telia's data for the capital area with the associated
            geometry
    """
    municipalities = read_shp(MUNICIPALITIES_DATA)
    sub_area = municipalities[municipalities['NAMEFIN'].isin(CAPITAL_AREA)]

    print("    Read Telia visit data")
    telia_gdf = read_parquet(TELIA_DATA_DIRECTORY / "hourly_visits_uusimaa_2025.parquet", crs=crs)
    sub_gdf   = geopandas.sjoin(telia_gdf, sub_area[['NAMEFIN','geometry']], how="inner", predicate="intersects")

    # print("    Read population census 2021")
    # pop_census_2021 = read_raster(POPULATION_CENSUS_2021_AT_100m, crs=crs)
    # clipped_pop_census_2021 = pop_census_2021.rio.clip(sub_area.geometry.values,sub_area.crs)
    # clipped_pop_census_2021 = xr.where(clipped_pop_census_2021>=0, clipped_pop_census_2021, np.nan)

    print("    Read OSM data")
    try:
        graph = osmnx.io.load_graphml(DATA_DIRECTORY / "Capital_area_osm.graphml")
    except:
        graph = osmnx.graph.graph_from_polygon(sub_area.to_crs("EPSG:4326").geometry.union_all())

    return sub_gdf,graph

# --------------------------------------------------------------------
def read_Lappeenranta(
        crs: int | str = 3067
) -> tuple[geopandas.GeoDataFrame,MultiDiGraph]:
    """
    Read the Telia's dataset and extract the data corresponding to
    the area surrounding Lappeenranta.

    Parameters
    ----------
    crs: int or str
            the desired output CRS (default: 3067)

    Returns
    -------
    geopandas.GeoDataFrame
            Telia's data for the surroundings of Lappeenranta with
            the associated geometry
    """
    municipalities = read_shp(MUNICIPALITIES_DATA)
    sub_area = municipalities[municipalities['NAMEFIN'].isin(LAPPEENRANTA)]

    print("    Read Telia visit data")
    telia_gdf = read_parquet(TELIA_DATA_DIRECTORY / "hourly_visits_eKarjala_Kymenlaakso_2025.parquet", crs=crs)
    sub_gdf = geopandas.sjoin(telia_gdf, sub_area[['NAMEFIN','geometry']], how="inner", predicate="intersects")

    # print("    Read population census 2021")
    # pop_census_2021 = read_raster(POPULATION_CENSUS_2021_AT_100m, crs=crs)
    # clipped_pop_census_2021 = pop_census_2021.rio.clip(sub_area.geometry.values,sub_area.crs)
    # clipped_pop_census_2021 = xr.where(clipped_pop_census_2021 >= 0, clipped_pop_census_2021, np.nan)

    print("    Read OSM data")
    try:
        graph = osmnx.io.load_graphml(DATA_DIRECTORY / "Lappeenranta_osm.graphml")
    except:
        graph = osmnx.graph.graph_from_polygon(sub_area.to_crs("EPSG:4326").geometry.union_all())

    return sub_gdf,graph

# --------------------------------------------------------------------
def extract_season(
        gdf: geopandas.GeoDataFrame,
        season: str = 'spring'
) -> geopandas.GeoDataFrame | None:
    """
    Extract the Telia's data corresponding to the given season.

    Parameters
    ----------
    gdf: geopandas.GeoDataFrame
            Telia's data for the region of interest with
            the associated geometry
    season: str
            season of interest

    Returns
    -------
    geopandas.GeoDataFrame
            Telia's data for the season of interest
    """
    month = gdf['observation_start_date'].dt.month

    if season == 'spring':
        return gdf[month.isin([3,4,5])]
    elif season == 'summer':
        return gdf[month.isin([6,7,8])]
    elif season in ['fall','autumn']:
        return gdf[month.isin([9,10,11])]
    elif season == 'winter':
        return gdf[month.isin([12,1,2])]
    return None

# --------------------------------------------------------------------
def extract_month(
        gdf: geopandas.GeoDataFrame,
        month: int
) -> geopandas.GeoDataFrame:
    """
    Extract the Telia's data corresponding to a given month.

    Parameters
    ----------
    gdf: geopandas.GeoDataFrame
            Telia's data for the region of interest with
            the associated geometry
    month: int
            month of interest

    Returns
    -------
    geopandas.GeoDataFrame
            Telia's data for the month of interest
    """

    return gdf[gdf['observation_start_date'].dt.month == month]

# --------------------------------------------------------------------
def extract_time_period(
        gdf: geopandas.GeoDataFrame,
        time_period: tuple[int,int] = (0,24),
        weekdays: bool = True,
) -> geopandas.GeoDataFrame:
    """
    Extract the time period during the day and the week from
    the Telia data.

    Parameters
    ----------
    gdf: geopandas.GeoDataFrame
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
    hour = gdf['observation_start_date'].dt.hour

    if time_period[0] < time_period[1]:
        sub_gdf = gdf[(time_period[0] <= hour) & (hour < time_period[1])]
    elif time_period[0] > time_period[1]:
        sub_gdf = gdf[(time_period[1] <= hour) | (hour < time_period[0])]
    elif time_period[0] == time_period[1]:
        sub_gdf = gdf[(hour == time_period[0])]

    if(weekdays):
        return sub_gdf[sub_gdf['observation_start_date'].dt.weekday<=4]
    else:
        return sub_gdf[sub_gdf['observation_start_date'].dt.weekday > 4]

# --------------------------------------------------------------------
def average_population_density(
        gdf: geopandas.GeoDataFrame,
        *,
        time_period: tuple[int,int] = (0,24),
        month: int | None = None,
        season: str | None = 'spring',
        weekdays: bool = True
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
    month: int
            month of interest
    season: str
            season of interest
    weekdays: bool
            specify whether to extract the weekdays or the weekend

    Returns
    -------
    geopandas.GeoDataFrame
            subset of Telia data
    """
    print("    Extract the time period")
    duration = time_period[1]-time_period[0]
    if(month is not None):
        month_gdf = extract_month(gdf,month)
        sub_df = extract_time_period(month_gdf,time_period,weekdays)
    else:
        season_gdf = extract_season(gdf,season)
        sub_df = extract_time_period(season_gdf,time_period,weekdays)

    print('    Derive the population density')
    visits = sub_df[ENTRIES_VISITS+['geometry']]
    visits['total_visits'] = visits[ENTRIES_VISITS].sum(axis=1)
    avg_visits = visits.groupby('geometry').mean().reset_index()
    for entry in ENTRIES_VISITS+['total_visits']:
        avg_visits[entry] = avg_visits[entry]/duration

    gdf = geopandas.GeoDataFrame(avg_visits,geometry=avg_visits['geometry'])

    gdf['area_km2'] = gdf.area / 1e6
    gdf['density'] = gdf['total_visits'] / gdf['area_km2']

    return gdf

# --------------------------------------------------------------------





print('Read data')
# sub_telia = read_capital_area(crs=3067)
sub_telia,osm_graph = read_Lappeenranta(crs=3067)

print('Population density')
population_density = average_population_density(sub_telia,time_period=(4,6),season="spring")


