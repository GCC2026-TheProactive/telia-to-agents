import pathlib
import geopandas

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
    return 0