import pathlib
import geopandas

COLNAMES_CONVERSION = {'total_visits': 'nb_persons'}
OUTPUT_COLUMNS = ['lon_centre','lat_centre','nb_persons','geometry']

def add_coordinates(gdf):
    new_gdf = gdf.copy()
    new_gdf['lon_centre'] = new_gdf.geometry.centroid.x
    new_gdf['lat_centre'] = new_gdf.geometry.centroid.y

    return new_gdf


def extract_columns(gdf,colnames):
    new_gdf = gdf.rename(columns=COLNAMES_CONVERSION)

    return new_gdf[colnames]


def export_population_density(
        gdf: geopandas.GeoDataFrame,
        outfile: str | pathlib.PosixPath | pathlib.Path,
) -> None:
    """
    Export the population density data into an XML file.

    Parameters
    ----------
    gdf: geopandas.GeoDataFrame
            subset of Telia data
    outfile: str or pathlib.PosixPath or pathlib.Path
            path of the output file for the population density data

    Returns
    -------
    """
    # proj_gdf = gdf.to_crs("EPSG:25835")
    gdf = add_coordinates(gdf)
    out_gdf = extract_columns(gdf,OUTPUT_COLUMNS)

    out_gdf.to_file(outfile)

    return 0