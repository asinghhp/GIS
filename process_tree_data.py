import geopandas as gpd
import pandas as pd
import rasterio
from scipy.ndimage import gaussian_filter
from skimage.feature import peak_local_max


def tree_data(dem_path, dsm_path, building_shp, address_shp, buffer_distance=20, output_path="output"):
    """
    Process tree canopy data and generate tree counts near addresses.

    Parameters:
        dem_path (str): Path to the DEM file.
        dsm_path (str): Path to the DSM file.
        building_shp (str): Path to the building outlines shapefile.
        address_shp (str): Path to the address shapefile.
        buffer_distance (int): Buffer distance (in meters) around addresses. Default is 20.
        output_path (str): Output directory path for the results.

    Returns:
        buffer_gdf (GeoDataFrame): GeoDataFrame of buffers with tree counts.
        csv_path (str): Path to the saved CSV file with tree counts.
        gpkg_path (str): Path to the saved GeoPackage file with buffers and tree counts.
    """
    # Create paths for outputs
    chm_path = f"{output_path}/chm.tif"
    smoothed_chm_path = f"{output_path}/smoothed_chm.tif"
    tree_tops_path = f"{output_path}/tree_tops.shp"
    filtered_tree_tops_path = f"{output_path}/filtered_tree_tops.shp"
    buffer_gpkg_path = f"{output_path}/buffer_with_tree_counts.gpkg"
    buffer_csv_path = f"{output_path}/buffer_with_tree_counts.csv"

    # Step 1: Create CHM (Canopy Height Model)
    with rasterio.open(dem_path) as dem, rasterio.open(dsm_path) as dsm:
        assert dem.shape == dsm.shape, "DEM and DSM dimensions must match!"
        dem_data = dem.read(1)
        dsm_data = dsm.read(1)
        profile = dem.profile
        crs = dem.crs

        # Subtract DEM from DSM to create CHM
        chm_data = dsm_data - dem_data

        # Save CHM
        profile.update(dtype='float32', count=1)
        with rasterio.open(chm_path, 'w', **profile) as dst:
            dst.write(chm_data, 1)

    # Step 2: Smooth the CHM
    sigma = 2
    with rasterio.open(chm_path) as chm:
        chm_data = chm.read(1)
        affine = chm.transform
        smoothed_chm = gaussian_filter(chm_data, sigma=sigma, mode='constant', cval=0)
        smoothed_chm[chm_data == 0] = 0

        # Save smoothed CHM
        with rasterio.open(smoothed_chm_path, 'w', **profile) as dst:
            dst.write(smoothed_chm, 1)

    # Step 3: Detect Local Maxima (Tree Tops)
    coordinates = peak_local_max(smoothed_chm, min_distance=3, threshold_abs=1)
    X, Y = coordinates[:, 1], coordinates[:, 0]
    xs, ys = affine * (X, Y)  # Convert pixel indices to spatial coordinates

    # Create GeoDataFrame for tree tops
    tree_tops = pd.DataFrame({'X': xs, 'Y': ys})
    tree_gdf = gpd.GeoDataFrame(tree_tops, geometry=gpd.points_from_xy(tree_tops.X, tree_tops.Y), crs=crs)
    tree_gdf.to_file(tree_tops_path, driver="ESRI Shapefile")

    # Step 4: Remove Points Overlapping Buildings
    buildings_gdf = gpd.read_file(building_shp).to_crs(crs)
    tree_gdf_filtered = tree_gdf.overlay(buildings_gdf, how='difference')
    tree_gdf_filtered.to_file(filtered_tree_tops_path, driver="ESRI Shapefile")

    # Step 5: Create Buffers Around Addresses
    addresses_gdf = gpd.read_file(address_shp).to_crs(crs)
    buffer_gdf = addresses_gdf.copy()
    buffer_gdf['geometry'] = buffer_gdf.geometry.buffer(buffer_distance)

    # Step 6: Count Trees Within Buffers
    buffer_gdf['tree_count'] = buffer_gdf.geometry.apply(
        lambda geom: tree_gdf_filtered[tree_gdf_filtered.geometry.within(geom)].shape[0]
    )

    # Save Results
    buffer_gdf.to_file(buffer_gpkg_path, driver="GPKG")
    buffer_gdf.drop(columns='geometry').to_csv(buffer_csv_path, index=False)

    return buffer_gdf, buffer_csv_path, buffer_gpkg_path
