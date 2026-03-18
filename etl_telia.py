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
    gdf = read_shp(filename,crs=3067)
    merged = df.merge(gdf,how="inner",on="location_id")

    return merged


# --------------------------------------------------------------------
def read_parquet(path: str | pathlib.PosixPath,
             crs: int | str = 3067
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
    filename = pathlib.Path(path) / "hourly_visits_uusimaa_2025.parquet"
    df = duckdb.sql(f"""SELECT
                           *
                        FROM
                           '{filename}'
                     """).df()

    return add_geometry(df,path,crs)

# --------------------------------------------------------------------


# Paths definition
NOTEBOOK_PATH  = pathlib.Path().resolve()
DATA_DIRECTORY = NOTEBOOK_PATH / "data" / "uusimaa_telia_hourly_visits"


gdf = read_parquet(DATA_DIRECTORY, crs=3067)

