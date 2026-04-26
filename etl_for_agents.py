import pathlib

import geopandas
import osmnx
from networkx.classes.multidigraph import MultiDiGraph

from constants import *
from etl_population_density import population_density_Lappeenranta
from etl_telia_travel import average_number_car, average_number_bikes, number_cars_Lappeenranta
from export_functions import export_population_density

ENTRIES_VISITS = ['visit_count', 'resident_visit_count', 'worker_visit_count',
                  'non_resident_non_worker_visit_count']


# --------------------------------------------------------------------
def merge_datasets(
        visits: geopandas.GeoDataFrame,
        cars: geopandas.GeoDataFrame | None = None,
        weekdays: bool = True
) -> geopandas.GeoDataFrame:
    print("Combine the population density and number of cars")
    visits_with_cars = average_number_car(visits, weekdays=weekdays)
    out_visits = average_number_bikes(visits_with_cars)

    return out_visits


# --------------------------------------------------------------------
def export_data(
        gdf: geopandas.GeoDataFrame,
        graph: MultiDiGraph | None,
        outfile_pop_dens: str | pathlib.PosixPath | pathlib.Path,
        outfile_osm: str | pathlib.PosixPath | pathlib.Path,
        weekdays: bool = True
) -> None:
    """
    Export the population density and OpenStreetMap datasets.

    Parameters
    ----------
    gdf: geopandas.GeoDataFrame
            subset of Telia data
    graph: MultiDiGraph
            OpenStreetMap graph for the area covered by the return Telia data
    outfile_pop_dens: str or pathlib.PosixPath or pathlib.Path
            path of the output file for the population density data
    outfile_osm: str or pathlib.PosixPath or pathlib.Path
            path of the output file for the OpenStreetMap data
    weekdays: bool
            specify whether to extract the weekdays or the weekend

    Returns
    -------
    """
    print("    Export population density")
    export_population_density(gdf, outfile_pop_dens, CRS)

    if graph is not None:
        print("    Export OSM data")
        osmnx.settings.all_oneway = True
        projected_graph = osmnx.projection.project_graph(graph, to_crs=f"EPSG:{CRS}")
        osmnx.io.save_graph_xml(projected_graph, filepath=outfile_osm)

    return


# --------------------------------------------------------------------

print('Population density')
population_density, osm_graph = population_density_Lappeenranta(weekdays=WEEKDAYS, crs=CRS, download_osm=DOWNLOAD_OSM)
print('Distribution of cars')
number_cars = number_cars_Lappeenranta(weekdays=WEEKDAYS, crs=CRS)
population_density = merge_datasets(population_density, number_cars, weekdays=WEEKDAYS)

print('Export data')
export_data(population_density, osm_graph, outfile_pop_dens=OUTPUT_DIRECTORY / "Lappeenranta_population_density.csv",
            outfile_osm=OUTPUT_DIRECTORY / "Lappeenranta.osm", weekdays=WEEKDAYS)
