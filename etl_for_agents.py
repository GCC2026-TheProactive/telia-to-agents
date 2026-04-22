import pathlib

import geopandas
import osmnx
from networkx.classes.multidigraph import MultiDiGraph

from etl_population_density import population_density_Lappeenranta
from etl_telia_travel import average_number_car_bikes
from export_functions import export_population_density

# Paths definition
NOTEBOOK_PATH = pathlib.Path().resolve()
DATA_DIRECTORY = NOTEBOOK_PATH / "data"
TELIA_DATA_DIRECTORY = DATA_DIRECTORY / "telia_hourly_visits"
OUTPUT_DIRECTORY = DATA_DIRECTORY / "output"

CRS = 25835
WEEKDAYS = True
FRACTION_CARS = 0.59
FRACTION_BIKES = 0.16
AVERAGE_CAR_OCCUPANCY = [1.3, 1.7]

MUNICIPALITIES_DATA = DATA_DIRECTORY / "finland_municipalities_2021.gpkg"
POPULATION_CENSUS_2021_AT_100m = (DATA_DIRECTORY / "JRC-ESTAT_Census_Population_2021_100m" /
                                  "JRC-ESTAT_Census_Population_2021_100m.tif")

CAPITAL_AREA = ['Helsinki', 'Espoo', 'Vantaa', 'Kauniainen']
LAPPEENRANTA = ['Lappeenranta', 'Imatra', 'Lemi', 'Luumäki', 'Miehikkälä', 'Savitaipale', 'Taipalsaari']

ENTRIES_VISITS = ['visit_count', 'resident_visit_count', 'worker_visit_count',
                  'non_resident_non_worker_visit_count']


# --------------------------------------------------------------------
def merge_datasets(
        visits: geopandas.GeoDataFrame,
        cars: geopandas.GeoDataFrame | None = None,
        weekdays: bool = True
) -> geopandas.GeoDataFrame:
    print("Combine the population density and number of cars")
    # gdf['nb_bikes'] = gdf['total_visits'] * FRACTION_BIKES
    new_gdf = average_number_car_bikes(visits, weekdays=weekdays)

    return new_gdf


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
population_density, osm_graph = population_density_Lappeenranta()
population_density = merge_datasets(population_density, weekdays=WEEKDAYS)

print('Export data')
export_data(population_density, osm_graph, outfile_pop_dens=OUTPUT_DIRECTORY / "Lappeenranta_population_density.csv",
            outfile_osm=OUTPUT_DIRECTORY / "Lappeenranta.osm", weekdays=WEEKDAYS)
