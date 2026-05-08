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
