import pathlib
import numpy as np
import pandas as pd
import xarray as xr
import geopandas
import duckdb
from geoanalysis_functions import read_shp,read_raster
import matplotlib.pyplot as plt


# Paths definition
NOTEBOOK_PATH  = pathlib.Path().resolve()
DATA_DIRECTORY = NOTEBOOK_PATH / "data"
TELIA_DATA_DIRECTORY = DATA_DIRECTORY / "telia_hourly_visits"

CAPITAL_AREA = ['Helsinki', 'Espoo', 'Vantaa', 'Kauniainen']
LAPPEENRANTA = ['Lappeenranta', 'Imatra', 'Lemi', 'Luumäki', 'Miehikkälä','Savitaipale','Taipalsaari']

ENTRIES_VISITS = ['visit_count','resident_visit_count','worker_visit_count',
                  'non_resident_non_worker_visit_count']

# --------------------------------------------------------------------
def add_geometry(df: pd.DataFrame,
             path: str | pathlib.PosixPath,
             crs: int | str = 3067
             ) -> geopandas.GeoDataFrame:
    """
    Add the geometry to the Telia's data based on the associated grid.

    Parameters
    ----------
    df: pd.DataFrame
            Telia's dataset
    filename: str or pathlib.PosixPath
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
def read_parquet(filename: str | pathlib.PosixPath,
             crs: int | str = 3067
             ) -> geopandas.GeoDataFrame:
    """
    Read the Telia's dataset, add the geometry of the grid and return
    the data into a GeoDataFrame.

    Parameters
    ----------
    filename: str or pathlib.PosixPath
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
def read_capital_area(crs: int | str = 3067
             ) -> geopandas.GeoDataFrame:
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
            Telia's data for the capital area with the associated geometry
    """
    municipalities = read_shp(DATA_DIRECTORY / "finland_municipalities_2021.gpkg")
    sub_area = municipalities[municipalities['NAMEFIN'].isin(CAPITAL_AREA)]

    telia_gdf = read_parquet(TELIA_DATA_DIRECTORY / "hourly_visits_uusimaa_2025.parquet", crs=crs)
    sub_telia = geopandas.sjoin(telia_gdf, sub_area[['NAMEFIN','geometry']], how="inner", predicate="intersects")

    pop_census_2021 = read_raster(DATA_DIRECTORY / "JRC-ESTAT_Census_Population_2021_100m" /
                                              "JRC-ESTAT_Census_Population_2021_100m.tif", crs=crs)
    clipped_pop_census_2021 = pop_census_2021.rio.clip(sub_area.geometry,sub_area.crs)
    clipped_pop_census_2021 = xr.where(clipped_pop_census_2021>=0, clipped_pop_census_2021, np.nan)

    return sub_telia,clipped_pop_census_2021

# --------------------------------------------------------------------
def read_Lappeenranta(crs: int | str = 3067
             ) -> geopandas.GeoDataFrame:
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
            Telia's data for the capital area with the associated geometry
    """
    municipalities = read_shp(DATA_DIRECTORY / "finland_municipalities_2021.gpkg")
    sub_area = municipalities[municipalities['NAMEFIN'].isin(LAPPEENRANTA)]

    telia_gdf = read_parquet(TELIA_DATA_DIRECTORY / "hourly_visits_eKarjala_Kymenlaakso_2025.parquet", crs=crs)
    sub_telia = geopandas.sjoin(telia_gdf, sub_area[['NAMEFIN','geometry']], how="inner", predicate="intersects")

    pop_census_2021 = read_raster(DATA_DIRECTORY / "JRC-ESTAT_Census_Population_2021_100m" /
                                              "JRC-ESTAT_Census_Population_2021_100m.tif", crs=crs)
    clipped_pop_census_2021 = pop_census_2021.rio.clip(sub_area.geometry.values,sub_area.crs)
    clipped_pop_census_2021 = xr.where(clipped_pop_census_2021 >= 0, clipped_pop_census_2021, np.nan)

    return sub_telia,clipped_pop_census_2021

# --------------------------------------------------------------------
def extract_season(gdf: geopandas.GeoDataFrame,
            season: str = 'spring'
            ) -> geopandas.GeoDataFrame:
    """
    Read the Telia's dataset, add the geometry of the grid and return
    the data into a GeoDataFrame.

    Parameters
    ----------
    filename: str or pathlib.PosixPath
            path of the data directory
    crs: int or str
            the desired output CRS (default: 4326)

    Returns
    -------
    geopandas.GeoDataFrame
            Telia's data with the associated geometry
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

# --------------------------------------------------------------------
def extract_month(gdf: geopandas.GeoDataFrame,
            month: int
            ) -> geopandas.GeoDataFrame:
    """
    Read the Telia's dataset, add the geometry of the grid and return
    the data into a GeoDataFrame.

    Parameters
    ----------
    filename: str or pathlib.PosixPath
            path of the data directory
    crs: int or str
            the desired output CRS (default: 4326)

    Returns
    -------
    geopandas.GeoDataFrame
            Telia's data with the associated geometry
    """

    return gdf[gdf['observation_start_date'].dt.month == month]

# --------------------------------------------------------------------
def extract_time_period(gdf: geopandas.GeoDataFrame,
            time_period: tuple[int] = (0,24),
            weekdays: bool = True,
            ) -> geopandas.GeoDataFrame:
    """
    Read the Telia's dataset, add the geometry of the grid and return
    the data into a GeoDataFrame.

    Parameters
    ----------
    filename: str or pathlib.PosixPath
            path of the data directory
    crs: int or str
            the desired output CRS (default: 4326)

    Returns
    -------
    geopandas.GeoDataFrame
            Telia's data with the associated geometry
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
def average_population_density(gdf: geopandas.GeoDataFrame,
            *,
            time_period: tuple[int] = (0,24),
            month: int | None = None,
            season: str | None = 'spring',
            weekdays: bool = True
            ) -> geopandas.GeoDataFrame:
    """
    Read the Telia's dataset, add the geometry of the grid and return
    the data into a GeoDataFrame.

    Parameters
    ----------
    filename: str or pathlib.PosixPath
            path of the data directory
    crs: int or str
            the desired output CRS (default: 4326)

    Returns
    -------
    geopandas.GeoDataFrame
            Telia's data with the associated geometry
    """
    duration = time_period[1]-time_period[0]
    if(month is not None):
        print('month')
        month_gdf = extract_month(gdf,month)
        sub_df = extract_time_period(month_gdf,time_period,weekdays)
    else:
        print('season')
        season_gdf = extract_season(gdf,season)
        sub_df = extract_time_period(season_gdf,time_period,weekdays)

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






# sub_telia = read_capital_area(crs=3067)
sub_telia,pop_census_2021 = read_Lappeenranta(crs=3067)

avg_visits = average_population_density(sub_telia,time_period=(4,6),month=6,season="summer")


