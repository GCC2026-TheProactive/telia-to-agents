import pathlib

# Path definitions
NOTEBOOK_PATH = pathlib.Path().resolve()
DATA_DIRECTORY = NOTEBOOK_PATH / "data"
TELIA_VISITS_DATA_DIRECTORY = DATA_DIRECTORY / "telia_hourly_visits"
TELIA_TRIPS_DATA_DIRECTORY = DATA_DIRECTORY / "telia_trips"
OUTPUT_DIRECTORY = DATA_DIRECTORY / "output"

# Input file path definitions
MUNICIPALITIES_DATA = DATA_DIRECTORY / "finland_municipalities_2021.gpkg"
POPULATION_CENSUS_2021_AT_100m = (DATA_DIRECTORY / "JRC-ESTAT_Census_Population_2021_100m" /
                                  "JRC-ESTAT_Census_Population_2021_100m.tif")

CRS = 25835
WEEKDAYS = True
DOWNLOAD_OSM = False
FRACTION_CARS_PER_TRIPS = 0.59
FRACTION_BIKES_PER_TRIPS = 0.16
AVERAGE_CAR_OCCUPANCY = [1.3, 1.7]


CAPITAL_AREA = ['Helsinki', 'Espoo', 'Vantaa', 'Kauniainen']
LAPPEENRANTA = ['Lappeenranta', 'Imatra', 'Lemi', 'Luumäki', 'Miehikkälä', 'Savitaipale', 'Taipalsaari']