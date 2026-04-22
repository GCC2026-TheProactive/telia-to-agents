import pathlib

import duckdb
import geopandas
import pandas as pd
from networkx.classes.multidigraph import MultiDiGraph

from geoanalysis_functions import read_shp

# Paths definition
NOTEBOOK_PATH = pathlib.Path().resolve()
DATA_DIRECTORY = NOTEBOOK_PATH / "data"
TELIA_DATA_DIRECTORY = DATA_DIRECTORY / "telia_trips"
OUTPUT_DIRECTORY = DATA_DIRECTORY / "output"

CRS = 25835

MUNICIPALITIES_DATA = DATA_DIRECTORY / "finland_municipalities_2021.gpkg"

LAPPEENRANTA = ['Lappeenranta', 'Imatra', 'Lemi', 'Luumäki', 'Miehikkälä', 'Savitaipale', 'Taipalsaari']


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
    merged = df.merge(gdf, how="inner", left_on=df.columns[0],
                      right_on="location_id")

    return geopandas.GeoDataFrame(merged, geometry=merged['geometry'])


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

    return df


# --------------------------------------------------------------------
def read_Lappeenranta(
        crs: int | str = 3067
) -> tuple[geopandas.GeoDataFrame, MultiDiGraph]:
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
    MultiDiGraph
            OpenStreetMap graph for the area covered by the return Telia data
    """
    municipalities = read_shp(MUNICIPALITIES_DATA, crs=crs)
    sub_area = municipalities[municipalities['NAMEFIN'].isin(LAPPEENRANTA)]

    print("    Read Telia trip data")
    telia_gdf = read_parquet(TELIA_DATA_DIRECTORY / "trips_grid_hourly_ekarjala_2025.parquet", crs=crs)
    origins = add_geometry(telia_gdf[['location_id_origin']],
                           TELIA_DATA_DIRECTORY, crs)
    destinations = add_geometry(telia_gdf[['location_id_destination']],
                                TELIA_DATA_DIRECTORY, crs)

    sub_orig = geopandas.sjoin(origins, sub_area[['NAMEFIN', 'geometry']],
                               how="inner",
                               predicate="intersects")
    sub_dest = geopandas.sjoin(destinations, sub_area[['NAMEFIN', 'geometry']],
                               how="inner",
                               predicate="intersects")

    sub_telia = telia_gdf[(telia_gdf['location_id_origin'].isin(sub_orig['location_id_origin'].to_list())) |
                          (telia_gdf['location_id_destination'].isin(sub_dest['location_id_destination'].to_list()))]

    return sub_telia


# --------------------------------------------------------------------

print('Read data')
sub_telia = read_Lappeenranta(crs=CRS)
