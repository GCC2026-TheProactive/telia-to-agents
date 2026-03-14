import pathlib
import geopandas
import rioxarray
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
