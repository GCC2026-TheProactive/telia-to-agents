import pathlib
import pandas as pd
import geopandas
import duckdb
from geoanalysis_functions import read_shp


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

    return add_geometry(df,path,crs)

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
def extract_time_period(gdf: geopandas.GeoDataFrame,
            time_period: tuple[int] = (0,24)
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
        return gdf[(time_period[0] <= hour) & (hour < time_period[1])]
    elif time_period[0] > time_period[1]:
        return gdf[(time_period[1] <= hour) | (hour < time_period[0])]
    elif time_period[0] > time_period[1]:
        return gdf[(hour == time_period[0])]

# --------------------------------------------------------------------
def average_population_density(gdf: geopandas.GeoDataFrame,
            time_period: tuple[int] = (0,24),
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
    season_gdf = extract_season(gdf,season)
    sub_df = extract_time_period(season_gdf,time_period)

    visits = sub_df[['visit_count','resident_visit_count','worker_visit_count',
                     'non_resident_non_worker_visit_count','geometry']]
    visits['total_visits'] = visits[['visit_count','resident_visit_count','worker_visit_count',
                     'non_resident_non_worker_visit_count']].sum(axis=1)
    avg_visits = visits.groupby('geometry').mean().reset_index()

    return geopandas.GeoDataFrame(avg_visits,geometry=avg_visits['geometry'])

# --------------------------------------------------------------------


# Paths definition
NOTEBOOK_PATH  = pathlib.Path().resolve()
DATA_DIRECTORY = NOTEBOOK_PATH / "data"
TELIA_DATA_DIRECTORY = DATA_DIRECTORY / "uusimaa_telia_hourly_visits"

CAPITAL_AREA = ['Helsinki','Espoo','Vantaa','Kauniainen']
municipalities = read_shp(DATA_DIRECTORY / "finland_municipalities_2021.gpkg")
capital_area = municipalities[municipalities['NAMEFIN'].isin(CAPITAL_AREA)]


telia_gdf = read_parquet(TELIA_DATA_DIRECTORY / "hourly_visits_uusimaa_2025.parquet", crs=3067)


sub_telia = geopandas.sjoin(telia_gdf,capital_area,how="inner",predicate="intersects")
avg_visits = average_population_density(sub_telia,(4,6),"summer")

avg_visits.plot(column = 'total_visits')
plt.show()