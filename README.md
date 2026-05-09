# telia-to-agents

ETL pipeline which transform Telia data into agents to be imported into our evacuation
simulations (https://github.com/GCC2026-TheProactive/java-matsim-setup).

## Telia data

The Telia data consist in two datasets which consist of a grid with cells of size between
250m in the densest areas and 8km in the most rural areas. Both datasets cover the full
2025 year, with an hourly sampling in time.

## Requirements

The project is based on Python 3.12 and the required packages are compiled in
`environment.yml`. We recommand to use conda:

    $ conda env create -f environment.yml

## Main components

The ETL pipeline is divided into three parts. First, the population density is derived
using the Telia "visits" dataset. Second, the number of cars is estimated using the
Telia "trips" dataset. Finally, the outputs are combined and the agents are computed.

### Population density

* Read the Telia data
* Extract a given month or season (e.g. January, spring)
* Extract all the rows corresponding to a given time range (e.g. 15:00-17:00)
* Add the geometry information to the Telia data and extract the area or municipalities
of interest
* Compute the average number of visits in each cell over the time range

The different steps are included in `etl_population_density.py`

### Number of cars

### Creation of the agents

## Run
