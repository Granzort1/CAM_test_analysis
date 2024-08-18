import os
import numpy as np
import matplotlib.pyplot as plt
from shapely.geometry import Polygon
import geopandas as gpd
import contextily as ctx
from matplotlib.colors import LinearSegmentedColormap, BoundaryNorm, LogNorm
import h5py
from tqdm import tqdm
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing
import psutil
import math

def get_available_memory():
    return psutil.virtual_memory().available

def get_optimal_chunk_size(total_size, available_memory, safety_factor=0.8):
    chunk_size = int(available_memory * safety_factor / total_size)
    return max(1, chunk_size)

def get_optimal_workers():
    cpu_count = multiprocessing.cpu_count()
    available_memory = get_available_memory()
    memory_based_workers = max(1, int(available_memory / (2 * 1024 * 1024 * 1024)))  # Assuming 2GB per worker
    return min(cpu_count, memory_based_workers)

def visualize_grid(data, start_x, start_y, cell_size, colors, title, data_type, global_min, global_max):
    data = np.ma.masked_invalid(data)
    if np.all(data.mask):
        print(f"Skipping frame: All data is invalid")
        return None, None

    rows, cols = data.shape

    x = np.arange(start_x, start_x + cols * cell_size, cell_size)
    y = np.arange(start_y + rows * cell_size, start_y, -cell_size)
    xx, yy = np.meshgrid(x, y)
    grid_cells = [Polygon([(x1, y1), (x1+cell_size, y1), (x1+cell_size, y1+cell_size), (x1, y1+cell_size)])
                  for x1, y1 in zip(xx.flatten(), yy.flatten())]

    gdf = gpd.GeoDataFrame({
        'geometry': grid_cells,
        'concentration': data.flatten()
    }, crs='EPSG:5186')

    non_zero_data = data[data > 0]
    frame_min = np.min(non_zero_data) if non_zero_data.size > 0 else 0
    frame_max = np.max(data)

    if data_type == 'Soil':
        min_conc, max_conc = global_min, global_max
    else:
        min_conc, max_conc = frame_min, frame_max

    if min_conc == max_conc == 0:
        min_conc, max_conc = 0, 1

    fig, ax = plt.subplots(figsize=(12, 10), constrained_layout=True)

    zero_mask = data == 0

    if data_type == 'Soil':
        norm = LogNorm(vmin=max(min_conc, 1e-10), vmax=max(max_conc, 1e-9))
    else:
        concentration_bounds = np.linspace(min_conc, max_conc, len(colors) + 1)
        norm = BoundaryNorm(concentration_bounds, len(colors))

    cmap = LinearSegmentedColormap.from_list('custom', colors, N=len(colors))

    gdf.plot(ax=ax, facecolor='none', edgecolor='gray', linewidth=0.5)

    non_zero_data = gdf.loc[~zero_mask.flatten()]
    if not non_zero_data.empty:
        non_zero_data.plot(ax=ax, column='concentration', cmap=cmap, norm=norm, alpha=0.7,
                           edgecolor='gray', linewidth=0.5)
    else:
        print("Warning: No non-zero data to plot")

    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])

    ctx.add_basemap(ax, crs=gdf.crs.to_string(), source=ctx.providers.OpenStreetMap.Mapnik)

    cbar = fig.colorbar(sm, ax=ax, pad=0.02)
    if data_type == 'Soil':
        cbar.set_ticks(np.logspace(np.log10(max(min_conc, 1e-10)), np.log10(max(max_conc, 1e-9)), num=len(colors) + 1))
    else:
        cbar.set_ticks(np.linspace(min_conc, max_conc, num=len(colors) + 1))
    cbar.set_ticklabels([f'{b:.1e}' for b in cbar.get_ticks()])

    concentration_unit = 'μg/m³' if data_type == 'Air' else 'μg/kg'
    cbar.set_label(f'Concentration ({concentration_unit})', fontsize=10)
    cbar.ax.tick_params(labelsize=9)

    ax.set_xlabel('X Coordinate (km)')
    ax.set_ylabel('Y Coordinate (km)')
    x_ticks = np.linspace(start_x, start_x + cols * cell_size, 6)
    y_ticks = np.linspace(start_y, start_y + rows * cell_size, 6)
    ax.set_xticks(x_ticks)
    ax.set_yticks(y_ticks)
    ax.set_xticklabels([f'{x / 1000:.2f}' for x in x_ticks])
    ax.set_yticklabels([f'{y / 1000:.2f}' for y in y_ticks])
    ax.set_title(title)

    return fig, ax

def process_frame(args):
    key, data, timestamp, start_x, start_y, cell_size, colors, data_type, global_min, global_max, output_path = args
    title = f'{data_type} Concentration at {timestamp}'
    fig, ax = visualize_grid(data, start_x, start_y, cell_size, colors, title, data_type, global_min, global_max)
    if fig is not None:
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close(fig)
    return key

def generate_images_from_hdf5(hdf5_file, output_folder, start_x, start_y, cell_size):
    colors = ['#FFFFFF', '#87CEFA', '#ADFF2F', '#FFFF00', '#FFA500', '#FF0000']

    with h5py.File(hdf5_file, 'r') as hf:
        for data_type in ['Air', 'Soil']:
            if data_type not in hf:
                print(f"Warning: {data_type} data not found in {hdf5_file}. Skipping.")
                continue

            group = hf[data_type]
            output_subfolder = os.path.join(output_folder, data_type)
            os.makedirs(output_subfolder, exist_ok=True)

            if data_type == 'Soil':
                non_zero_data = [group[key][()] for key in group.keys() if np.any(group[key][()] > 0)]
                if non_zero_data:
                    global_min = min(np.min(arr[arr > 0]) for arr in non_zero_data)
                    global_max = max(np.max(arr) for arr in non_zero_data)
                else:
                    global_min, global_max = 0, 1
                if global_min == global_max:
                    global_min, global_max = global_min * 0.9, global_max * 1.1
            else:
                global_min, global_max = None, None

            args_list = [
                (key, group[key][()], group[key].attrs['timestamp'], start_x, start_y, cell_size, colors, data_type, global_min, global_max,
                 os.path.join(output_subfolder, f'frame_{i:03d}.png'))
                for i, key in enumerate(group.keys())
            ]

            total_frames = len(args_list)
            chunk_size = get_optimal_chunk_size(total_frames, get_available_memory())
            num_workers = get_optimal_workers()

            print(f"Processing {data_type} data with {num_workers} workers and chunk size of {chunk_size}")

            for i in range(0, total_frames, chunk_size):
                chunk = args_list[i:i+chunk_size]
                with ProcessPoolExecutor(max_workers=num_workers) as executor:
                    futures = [executor.submit(process_frame, args) for args in chunk]
                    for future in tqdm(as_completed(futures), total=len(futures), desc=f"Generating {data_type} images (chunk {i//chunk_size + 1}/{math.ceil(total_frames/chunk_size)})"):
                        try:
                            future.result()
                        except Exception as e:
                            print(f"Error processing frame: {e}")

def process_all_substances():
    hdf5_folder = r"C:\CAM_test_analysis\hdf5_data"
    output_base_folder = r"C:\CAM_test_analysis\graph"
    start_x = 164191
    start_y = 470659
    cell_size = 100

    for folder_number in range(26, 42):
        hdf5_file = os.path.join(hdf5_folder, f"Concentration{folder_number}.h5")
        output_folder = os.path.join(output_base_folder, f"Concentration{folder_number}")
        try:
            generate_images_from_hdf5(hdf5_file, output_folder, start_x, start_y, cell_size)
        except Exception as e:
            print(f"Error processing Concentration{folder_number}.h5: {e}")
            continue

if __name__ == "__main__":
    process_all_substances()