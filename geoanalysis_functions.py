import pathlib
import shapely
import xarray
import geopandas
import rioxarray
# --------------------------------------------------------------------
def geometry2gdf(geom: shapely.geometry.collection.GeometryCollection,
                 crs: int | str = 4326
                 ) -> geopandas.GeoDataFrame:
    """
    Convert a collection of geometry(ies) into a GeoDataFrame.

    Parameters
    ----------
    geom: shapely.geometry.collection.GeometryCollection
            a collection of geometry(ies)
    crs: int or str
            the desired output CRS (default: 4326)

    Returns
    -------
    geopandas.GeoDataFrame
    associated GeoDataFrame
    """
    try:
        return geopandas.GeoDataFrame({'geometry': geom},crs=f"ESPG:{crs}")
    except:
        return geopandas.GeoDataFrame({'geometry': geom},crs=crs)


# --------------------------------------------------------------------
def read_shp(filename: str | pathlib.Path(),
             crs: int | str = 4326
             ) -> geopandas.GeoDataFrame:
    """
    Read a file into a GeoDataFrame, reproject it to the desired CRS and return it.

    Parameters
    ----------
    filename: str or pathlib.Path()
            path or url of the input file
    crs: int or str
            the desired output CRS (default: 4326)

    Returns
    -------
    geopandas.GeoDataFrame
            reprojected data
    """
    gdf = geopandas.read_file(filename)
    try:
        return gdf.to_crs(f"ESPG:{crs}")
    except:
        return gdf.to_crs(crs)


# --------------------------------------------------------------------
def read_raster(filename: str | pathlib.Path(),
                crs: int | str = 4326
                ) -> xarray.core.dataarray.DataArray:
    """
    Read a raster file, reproject it to the desired CRS and return it.

    Parameters
    ----------
    filename: str or pathlib.Path()
            path or url of the input file
    crs: int or str
            the desired output CRS (default: 4326)

    Returns
    -------
    xarray.core.dataarray.DataArray
            reprojected raster data
    """
    data = rioxarray.open_rasterio(filename)
    try:
        return data.rio.reproject(f"ESPG:{crs}")
    except:
        return data.rio.reproject(crs)


# --------------------------------------------------------------------
def extract_area(data: geopandas.GeoDataFrame | xarray.core.dataarray.DataArray,
                 area : shapely.geometry.collection.GeometryCollection | None
                 ) -> geopandas.GeoDataFrame | xarray.core.dataarray.DataArray:
    """
    Given a collection of geometry(ies), extract the associated data or clip the raster.

    Parameters
    ----------
    data: geopandas.GeoDataFrame or xarray.core.dataarray.DataArray
            original data
    area: shapely.geometry.collection.GeometryCollection
            a collection of geometry(ies)

    Returns
    -------
    geopandas.GeoDataFrame or xarray.core.dataarray.DataArray
            sub dataset or clipped raster
    """
    try:
        gdf_area = geometry2gdf(area, data.crs.to_epsg())
        sub_data = data.join(gdf_area,rsuffix='_area')
        return sub_data
    except:
        gdf_area = geometry2gdf(area, data.rio.crs.to_epsg())
        sub_data = data.rio.clip(gdf_area.geometry,gdf_area.crs)
        return sub_data


# --------------------------------------------------------------------


