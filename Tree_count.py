from process_tree_data import tree_data
# Input file paths
dem_path = "path_to_dem.tif"
dsm_path = "path_to_dsm.tif"
building_shp = "path_to_buildingoutlines.shp"
address_shp = "path_to_address.shp"

# Output directory
output_path = "output_directory"

# Run the function
buffer_gdf, csv_path, gpkg_path = tree_data(
    dem_path=dem_path,
    dsm_path=dsm_path,
    building_shp=building_shp,
    address_shp=address_shp,
    buffer_distance=20,
    output_path=output_path
)

print(f"Buffer GeoDataFrame:\n{buffer_gdf.head()}")
print(f"CSV saved at: {csv_path}")
print(f"GeoPackage saved at: {gpkg_path}")
