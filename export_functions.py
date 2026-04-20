import pathlib

import geopandas
import pandas as pd

COLNAMES_CONVERSION = {'total_visits': 'nb_persons'}
OUTPUT_COLUMNS = ['lon_centre', 'lat_centre', 'nb_persons', 'geometry']

AVERAGE_CAR_OCCUPANCY = [1.3,1.7]  # https://www.traficom.fi/files/media/file/HLT2021_Fact%20sheet_Eurostat.pdf

def export_cell(row: pd.Series) -> tuple[list[float], list[float], list[str], list[int]]:
    X, Y, mode, n_people = [], [], [], []
    nb_persons = int(row['total_visits'])
    geom = row['geometry']
    multi_positions = geopandas.GeoSeries([geom]).sample_points(nb_persons)[0]
    positions = [point for point in multi_positions.geoms]

    for point in positions:
        X.append(point.x)
        Y.append(point.y)
        mode.append('walk')
        n_people.append(1)

    assert sum(n_people) == nb_persons, 'Wrong output number of people'

    return X, Y, mode, n_people


def export_population_density(
        gdf: geopandas.GeoDataFrame,
        outfile: str | pathlib.PosixPath | pathlib.Path,
        crs: int | str = 3067
) -> None:
    assert gdf.crs.srs == f'EPSG:{crs}', f'Expected crs EPSG:{crs}'

    X, Y, mode, n_people = [], [], [], []
    for idx, row in gdf.iterrows():
        output_lists = export_cell(row)
        X += output_lists[0]
        Y += output_lists[1]
        mode += output_lists[2]
        n_people += output_lists[3]

    dict = {'X': X,
            'Y': Y,
            'mode': mode,
            'n_people': n_people}
    out_gdf = pd.DataFrame(dict)

    out_gdf.to_csv(outfile)

    return 0
