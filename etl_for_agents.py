import pathlib

import duckdb
import geopandas
import osmnx
import pandas as pd
from networkx.classes.multidigraph import MultiDiGraph

from export_functions import export_population_density
from geoanalysis_functions import read_shp

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


print('Read data')
# sub_telia = read_capital_area(crs=3067)
sub_telia, osm_graph = read_Lappeenranta(crs=CRS)

print('Population density')
population_density = average_population_density(sub_telia, time_period=(4, 6), season="spring", weekdays=WEEKDAYS)
population_density = average_number_car_bikes(population_density, weekdays=WEEKDAYS)

print('Export data')
export_data(population_density, osm_graph, outfile_pop_dens=OUTPUT_DIRECTORY / "Lappeenranta_population_density.csv",
            outfile_osm=OUTPUT_DIRECTORY / "Lappeenranta.osm", weekdays=WEEKDAYS)
