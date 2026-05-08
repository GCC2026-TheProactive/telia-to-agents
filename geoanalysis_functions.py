import pathlib

import duckdb
import geopandas
import pandas as pd
import rioxarray
import shapely
import xarray


# --------------------------------------------------------------------
def read_shp(filename: str | pathlib.PosixPath | pathlib.Path,
             crs: int | str = None
             ) -> geopandas.GeoDataFrame:
    """
    Read a shp file into a GeoDataFrame, reproject it to the desired CRS and return it.

    Parameters
    ----------
    filename: str or pathlib.PosixPath or pathlib.Path
            path or url of the input file
    crs: int or str
            the desired output CRS (default: 4326)

    Returns
    -------
    geopandas.GeoDataFrame
            reprojected data
    """
    gdf = geopandas.read_file(filename)
    if crs is None:
        return gdf
    try:
        return gdf.to_crs(f"EPSG:{crs}")
    except:
        return gdf.to_crs(crs)


# --------------------------------------------------------------------
def read_parquet(
        filename: str | pathlib.PosixPath | pathlib.Path
) -> pd.DataFrame:
    """
    Read the Telia's dataset and return the data into a DataFrame.

    Parameters
    ----------
    filename: str or pathlib.PosixPath or pathlib.Path
            path of the input file

    Returns
    -------
    pd.DataFrame
            Telia's data
    """
    filename = pathlib.Path(filename)
    df = duckdb.sql(f"""SELECT
                           *
                        FROM
                           '{filename}'
                     """).df()

    return df


# --------------------------------------------------------------------
