import os
import numpy as np
import matplotlib.pyplot as plt
from shapely.geometry import Polygon
import geopandas as gpd
import contextily as ctx
from matplotlib.colors import LinearSegmentedColormap, BoundaryNorm, LogNorm
from matplotlib.patches import Rectangle
import h5py
from tqdm import tqdm

def visualize_grid(data, start_x, start_y, cell_size, colors, title, data_type, global_min, global_max):
    # Data validation
    data = np.ma.masked_invalid(data)
    if np.all(data.mask):
        print(f"Skipping frame: All data is invalid")
        return None, None

    rows, cols = data.shape

    grid_cells = []
    for i in range(rows):
        for j in range(cols):
            x1, y1 = start_x + j * cell_size, start_y + (rows - i - 1) * cell_size
            x2, y2 = x1 + cell_size, y1 + cell_size
            corners = [(x1, y1), (x2, y1), (x2, y2), (x1, y2)]
            grid_cells.append(Polygon(corners))

    gdf = gpd.GeoDataFrame({
        'geometry': grid_cells,
        'concentration': data.flatten()
    }, crs='EPSG:5186')

    # Calculate min and max for this frame
    non_zero_data = data[data > 0]
    if non_zero_data.size > 0:
        frame_min = np.min(non_zero_data)
        frame_max = np.max(data)
    else:
        frame_min = frame_max = 0

    # Use global range for Soil, frame range for Air
    if data_type == 'Soil':
        min_conc, max_conc = global_min, global_max
        print(f"Using global range for Soil: {min_conc}, {max_conc}")
    else:
        min_conc, max_conc = frame_min, frame_max
        print(f"Using frame range for Air: {min_conc}, {max_conc}")

    # If both min and max are 0, set a default range
    if min_conc == max_conc == 0:
        min_conc, max_conc = 0, 1
        print("Warning: All data is zero. Using default range: 0, 1")

    fig, ax = plt.subplots(figsize=(12, 10), constrained_layout=True)

    # 데이터가 0인 부분의 마스크 생성
    zero_mask = data == 0

    if data_type == 'Soil':
        # For soil, use log scale
        norm = LogNorm(vmin=max(min_conc, 1e-10), vmax=max(max_conc, 1e-9))
    else:
        # For air, use linear scale
        concentration_bounds = np.linspace(min_conc, max_conc, len(colors) + 1)
        norm = BoundaryNorm(concentration_bounds, len(colors))

    cmap = LinearSegmentedColormap.from_list('custom', colors, N=len(colors))

    # 모든 셀 그리기 (0 포함)
    gdf.plot(ax=ax, facecolor='none', edgecolor='gray', linewidth=0.5)

    # 0이 아닌 데이터에 대해 색상 적용
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

            # Calculate global min and max for Soil data
            if data_type == 'Soil':
                global_min = np.inf
                global_max = -np.inf
                for key in group.keys():
                    data = group[key][()]
                    non_zero_data = data[data > 0]
                    if non_zero_data.size > 0:
                        global_min = min(global_min, np.min(non_zero_data))
                        global_max = max(global_max, np.max(data))

                if global_min == np.inf or global_max == -np.inf:
                    global_min, global_max = 0, 1
                    print(f"Warning: All Soil data is zero or invalid. Using default global range: 0, 1")
                elif global_min == global_max:
                    global_min, global_max = global_min * 0.9, global_max * 1.1
                    print(f"Warning: All non-zero Soil data has the same value. Adjusting range slightly.")
            else:
                global_min, global_max = None, None  # Not used for Air data

            for i, key in enumerate(tqdm(group.keys(), desc=f"Generating {data_type} images")):
                try:
                    data = group[key][()]
                    timestamp = group[key].attrs['timestamp']
                    title = f'{data_type} Concentration at {timestamp}'

                    fig, ax = visualize_grid(data, start_x, start_y, cell_size, colors, title, data_type, global_min, global_max)
                    if fig is not None:
                        plt.savefig(os.path.join(output_subfolder, f'frame_{i:03d}.png'), dpi=300, bbox_inches='tight')
                        plt.close(fig)
                except Exception as e:
                    print(f"Error processing frame {i} for {data_type}: {e}")
                    continue

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