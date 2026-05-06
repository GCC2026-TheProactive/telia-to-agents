import pathlib
import random

import geopandas
import numpy as np
import pandas as pd
from scipy.stats import poisson

from constants import *

COLNAMES_CONVERSION = {'total_visits': 'nb_persons',
                       'total_nb_cars': 'nb_cars'}

CAR_PASSENGERS_OPTIONS = [0, 1, 2, 3]
AVERAGE_CAR_OCCUPANCY = [1.3, 1.7]  # https://www.traficom.fi/files/media/file/HLT2021_Fact%20sheet_Eurostat.pdf
MU_CAR_OCCUPANCY = [0.56, 1.26]


def truncated_Poisson(list_x, mu, xmin=-1, xmax=1e3):
    Poisson_cars = poisson(mu)
    probas = np.zeros(len(list_x))
    i = 0
    for x in list_x:
        if (xmin < x) and (x <= xmax):
            probas[i] = Poisson_cars.pmf(x) / (Poisson_cars.cdf(xmax) - Poisson_cars.cdf(xmin))
        i += 1

    return probas


def export_cell(
        row: pd.Series,
        polygon: geopandas.GeoSeries,
        weekdays: bool = True
) -> tuple[list[float], list[float], list[str], list[int]]:
    if weekdays:
        mu_cars = AVERAGE_CAR_OCCUPANCY[0] - 1
    else:
        mu_cars = AVERAGE_CAR_OCCUPANCY[1] - 1
    X, Y, mode, n_people = [], [], [], []
    nb_persons = int(row['nb_persons'])
    nb_cars = int(row['nb_cars'])
    nb_bikes = int(row['nb_bikes'])
    geom = geopandas.GeoSeries([row['geometry']]).intersection(polygon, align=False)
    if nb_persons > 1:
        multi_positions = geom.sample_points(nb_persons)[0]
    else:
        multi_positions = geom.sample_points(nb_persons)
    positions = [point for point in multi_positions.geoms]
    random.shuffle(positions)

    nb_agents = 0
    for idx, point in zip(range(len(positions)), positions):
        if nb_agents < nb_persons:
            X.append(point.x)
            Y.append(point.y)
        if (idx < nb_cars) & (nb_agents < nb_persons):
            nb_in_car = 1 + np.random.choice(CAR_PASSENGERS_OPTIONS,
                                             p=truncated_Poisson(CAR_PASSENGERS_OPTIONS, mu_cars,
                                                                 xmax=max(CAR_PASSENGERS_OPTIONS)))
            mode.append('car')
            if nb_in_car <= nb_persons - nb_agents:
                n_people.append(nb_in_car)
                nb_agents += nb_in_car
            else:
                n_people.append(nb_persons - nb_agents)
                nb_agents += nb_persons - nb_agents
        elif (idx - nb_cars < nb_bikes) & (nb_agents < nb_persons):
            mode.append('bike')
            n_people.append(1)
            nb_agents += 1
        elif nb_agents < nb_persons:
            mode.append('walk')
            n_people.append(1)
            nb_agents += 1
        else:
            break

    if sum(n_people) != nb_persons:
        print(nb_persons, nb_cars, nb_bikes, sum(n_people), nb_persons)
        print(n_people)
    assert sum(n_people) == nb_persons, 'Wrong output number of people'

    return X, Y, mode, n_people


def export_agents(
        gdf: geopandas.GeoDataFrame,
        sub_area: geopandas.GeoDataFrame,
        outfile: str | pathlib.PosixPath | pathlib.Path,
        crs: int | str = 3067,
        weekdays: bool = True
) -> None:
    assert gdf.crs.srs == f'EPSG:{crs}', f'Expected crs EPSG:{crs}'

    poly_area = geopandas.GeoSeries(
        [sub_area.geometry.union_all()]
    )

    new_gdf = gdf.rename(columns=COLNAMES_CONVERSION)

    X, Y, mode, n_people = [], [], [], []
    for idx, row in new_gdf.iterrows():
        output_lists = export_cell(row, poly_area, weekdays)
        X += output_lists[0]
        Y += output_lists[1]
        mode += output_lists[2]
        n_people += output_lists[3]

    out_dict = {'X': X,
                'Y': Y,
                'mode': mode,
                'n_people': n_people}
    out_df = pd.DataFrame(out_dict)
    out_gdf = geopandas.GeoDataFrame(
        out_df,
        geometry=geopandas.points_from_xy(out_df['X'], out_df['Y']),
        crs=f'EPSG:{crs}')

    out_gdf.to_csv(str(outfile) + "_agents.csv")
    out_gdf.to_file(str(outfile) + "_agents.gpkg")

    return
