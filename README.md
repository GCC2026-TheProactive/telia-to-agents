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

In addition to the agents, the pipeline also extract the route network from OpenStreetMap
for the area or municipalities of interest.

### Population density

The different steps are included in `etl_population_density.py` and summarized below:

* Read the Telia "visits" data
* Extract a given month or season (e.g. January, spring)
* Extract all the rows corresponding to a given time range (e.g. 15:00-17:00)
* Add the geometry information to the Telia data and extract the area or municipalities
of interest
* Compute the average number of visits in each cell over the time range

### Number of cars

The different steps are included in `etl_number_cars.py` and summarized below:

* Read the Telia "trips" data
* Extract a given month or season (e.g. January, spring)
* Extract all the rows corresponding to a given time range (e.g. 15:00-17:00)
* Add the geometry information to the Telia data for the origin and destination cells
* Extract the rows for which the origin or destination are withing the area or
municipalities of interest
* Estimate the initial number of cars from the population density at night(22:00-6:00),
using an average of 0.6 cars per person 
* Compute the average number of cars entering and leaving each cell since 6:00, and
derive the average number of cars at a given time.

### Creation of the agents

The agents are produced cell by cell. The different steps are included in `etl_functions.py`
and summarized below:

* N positions are randomly selected within the intersection of the cell and the limits of
the area of interest, where N is the number of persons in the cell.
* Each agent is randomly assigned one of the N positions.
* We first create the "car" agents, with a driver and X passengers. The number of passengers
follow a Poisson's distribution, with an average of 0.3 passenger per car.
* The remaining persons not assigned to a "car" agent are assigned to individual "walk"
agents.
* We ensure that the total number of persons associated to the agents is the same as
the number of persons in the cell.
* After making sure that the agents are projected to the correct CRS, they are exported
* into a .csv file.

## Run
