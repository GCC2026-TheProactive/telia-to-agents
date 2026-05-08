import pathlib

import geopandas
import osmnx
from networkx.classes.multidigraph import MultiDiGraph

from constants import *
from etl_number_cars import average_number_bikes, number_cars_Lappeenranta
from etl_population_density import population_density_Lappeenranta
from export_functions import export_agents
from geoanalysis_functions import read_shp

ENTRIES_VISITS = ['visit_count', 'resident_visit_count', 'worker_visit_count',
                  'non_resident_non_worker_visit_count']


# --------------------------------------------------------------------
def merge_datasets(
        visits: geopandas.GeoDataFrame,
        cars: geopandas.GeoDataFrame
) -> geopandas.GeoDataFrame:
    visits_with_cars = visits.merge(cars, how="inner", on=["location_id", "geometry"])
    out_visits = average_number_bikes(visits_with_cars)

    return out_visits


# --------------------------------------------------------------------
def export_data(
        gdf: geopandas.GeoDataFrame,
        graph: MultiDiGraph | None,
        sub_area: geopandas.GeoDataFrame,
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
    sub_area: geopandas.GeoDataFrame
            municipalities to extract, with geometry
    outfile_pop_dens: str or pathlib.PosixPath or pathlib.Path
            path of the output file for the population density data
    outfile_osm: str or pathlib.PosixPath or pathlib.Path
            path of the output file for the OpenStreetMap data
    weekdays: bool
            specify whether to extract the weekdays or the weekend

    Returns
    -------
    """
    print("    Export population density and cars distribution")
    gdf.to_csv(str(outfile_pop_dens) + "_population+cars.csv")
    gdf.to_file(str(outfile_pop_dens) + "_population+cars.gpkg")

    print("    Export agents")
    export_agents(gdf, sub_area, outfile_pop_dens, CRS, weekdays)

    if graph is not None:
        print("    Export OSM data")
        osmnx.settings.all_oneway = True
        projected_graph = osmnx.projection.project_graph(graph, to_crs=f"EPSG:{CRS}")
        osmnx.io.save_graph_xml(projected_graph, filepath=outfile_osm)

    return


# --------------------------------------------------------------------

time_period = (9, 16)
month = None
season = 'spring'

municipalities = read_shp(MUNICIPALITIES_DATA, crs=CRS)
municipalities = municipalities[municipalities['NAMEFIN'].isin(SOUTH_KARELIA)]

print('Population density')
population_density, osm_graph = population_density_Lappeenranta(municipalities,
                                                                time_period=time_period, month=month, season=season,
                                                                weekdays=WEEKDAYS, crs=CRS, download_osm=DOWNLOAD_OSM)

print('Population density by night')
population_night = population_density_Lappeenranta(municipalities,
                                                   time_period=(22,6), month=month, season=season,
                                                   weekdays=WEEKDAYS, crs=CRS)[0]

print('Distribution of cars')
number_cars = number_cars_Lappeenranta(municipalities,
                                       population_night=population_night,
                                       time_period=time_period, month=month, season=season,
                                       weekdays=WEEKDAYS, crs=CRS)

print("Combine the population density and number of cars")
population_with_cars = merge_datasets(population_density, number_cars)

print('Export data')
export_data(population_with_cars, osm_graph, municipalities, outfile_pop_dens=OUTPUT_DIRECTORY / "South_Karelia",
            outfile_osm=OUTPUT_DIRECTORY / "South_Karelia.osm", weekdays=WEEKDAYS)
