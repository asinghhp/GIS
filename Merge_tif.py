
import rasterio
from rasterio.merge import merge
import glob
import os

# Define the folder containing DSM tiles and the output file path
dsm_folder = "/GIS/lds-new-zealand-6layers-GTiff-JPEG-SHP/manawatu-whanganui_1m-dsm-2018/"  # Replace with your DSM tiles folder
output_file = "/GIS/lds-new-zealand-6layers-GTiff-JPEG-SHP/merged_dsm.tif"  # Replace with your desired output path

# List all DSM tiles in the folder (ensure all files are .tif)
dsm_tiles = glob.glob(os.path.join(dsm_folder, "*.tif"))

if len(dsm_tiles) == 0:
    raise ValueError("No DSM tiles found in the specified folder!")

# Open all DSM tiles as rasterio datasets
datasets = [rasterio.open(tile) for tile in dsm_tiles]

# Merge the DSM tiles
merged_dsm, out_transform = merge(datasets)

# Update metadata for the merged DSM
out_meta = datasets[0].meta.copy()
out_meta.update({
    "driver": "GTiff",
    "height": merged_dsm.shape[1],
    "width": merged_dsm.shape[2],
    "transform": out_transform,
    "crs": datasets[0].crs
})

# Save the merged DSM raster to a new file
with rasterio.open(output_file, "w", **out_meta) as dest:
    dest.write(merged_dsm)

# Print success message
print(f"Merged DSM saved to {output_file}")

# Close all datasets to free resources
for dataset in datasets:
    dataset.close()