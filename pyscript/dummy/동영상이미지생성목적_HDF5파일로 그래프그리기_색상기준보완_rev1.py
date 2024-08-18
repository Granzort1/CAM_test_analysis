import os
import numpy as np
import matplotlib.pyplot as plt
from shapely.geometry import Polygon
import geopandas as gpd
import contextily as ctx
from matplotlib.colors import LinearSegmentedColormap, BoundaryNorm
from matplotlib.patches import Rectangle
import h5py
from tqdm import tqdm
from datetime import datetime


def get_color_ranges(substance, data_type, data):
    fixed_ranges = {
        'Ethylacetate': {
            'Air': [0, 50, 200, 1000, 5000, 20000],
            'Soil': [0, 500, 2000, 10000, 50000, 200000]
        },
        'Benzene': {
            'Air': [0, 1.6, 5, 10, 20, 40],
            'Soil': [0, 100, 500, 2000, 10000, 50000]
        },
        'Methylacrylate': {
            'Air': [0, 10, 50, 200, 1000, 5000],
            'Soil': [0, 100, 500, 2000, 10000, 50000]
        },
        'Methyltrichlorosilane': {
            'Air': [0, 0.5, 2, 10, 50, 200],
            'Soil': [0, 50, 200, 1000, 5000, 20000]
        },
        'Ethyleneoxide': {
            'Air': [0, 0.1, 0.5, 2, 10, 50],
            'Soil': [0, 10, 50, 200, 1000, 5000]
        },
        'Triethylamine': {
            'Air': [0, 1, 5, 20, 100, 500],
            'Soil': [0, 100, 500, 2000, 10000, 50000]
        },
        'Methylethylketoneperoxide': {
            'Air': [0, 0.1, 0.5, 2, 10, 50],
            'Soil': [0, 10, 50, 200, 1000, 5000]
        },
        'Methylhydrazine': {
            'Air': [0, 0.01, 0.05, 0.2, 1, 5],
            'Soil': [0, 1, 5, 20, 100, 500]
        },
        'Chloromethane': {
            'Air': [0, 50, 200, 1000, 5000, 20000],
            'Soil': [0, 500, 2000, 10000, 50000, 200000]
        },
        'Methylamine': {
            'Air': [0, 10, 50, 200, 1000, 5000],
            'Soil': [0, 100, 500, 2000, 10000, 50000]
        },
        'Vinylchloride': {
            'Air': [0, 0.1, 0.5, 2, 10, 50],
            'Soil': [0, 10, 50, 200, 1000, 5000]
        },
        'Carbondisulfide': {
            'Air': [0, 10, 50, 200, 1000, 5000],
            'Soil': [0, 100, 500, 2000, 10000, 50000]
        },
        'Trimethylamine': {
            'Air': [0, 1, 5, 20, 100, 500],
            'Soil': [0, 100, 500, 2000, 10000, 50000]
        },
        'Propyleneoxide': {
            'Air': [0, 1, 5, 20, 100, 500],
            'Soil': [0, 100, 500, 2000, 10000, 50000]
        },
        'Methylvinylketone': {
            'Air': [0, 0.5, 2, 10, 50, 200],
            'Soil': [0, 50, 200, 1000, 5000, 20000]
        },
        'Nitrobenzene': {
            'Air': [0, 1, 5, 20, 100, 500],
            'Soil': [0, 100, 500, 2000, 10000, 50000]
        }
    }
    fixed_range = fixed_ranges.get(substance, {}).get(data_type, None)
    if fixed_range is None:
        raise ValueError(f"Unsupported substance or data type: {substance}, {data_type}")

    # 0보다 큰 값만 고려
    data_positive = data[data > 0]
    if len(data_positive) > 0:
        data_min, data_max = np.min(data_positive), np.max(data_positive)
        log_min, log_max = np.log10(data_min), np.log10(data_max)
        log_range = np.logspace(log_min, log_max, num=6)
    else:
        log_range = np.linspace(1e-10, 1, num=6)  # 모든 값이 0인 경우

    # 고정 범위와 로그 범위를 결합 (0 포함)
    combined_range = np.unique(np.sort(np.concatenate([[0], fixed_range[1:], log_range])))

    # 최종적으로 6개의 범위 선택 (0 포함)
    if len(combined_range) > 6:
        indices = np.linspace(0, len(combined_range) - 1, 6).astype(int)
        final_range = combined_range[indices]
    else:
        final_range = combined_range

    return final_range.tolist()



def visualize_grid(data, start_x, start_y, cell_size, concentration_bounds, colors, title, data_type, substance):
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

    # concentration_bounds를 정확히 colors에 맞추어 설정
    cmap = LinearSegmentedColormap.from_list('custom', colors, N=len(concentration_bounds))
    norm = BoundaryNorm([0] + concentration_bounds, len(colors))

    fig, ax = plt.subplots(figsize=(12, 10), constrained_layout=True)
    gdf.plot(column='concentration', ax=ax, cmap=cmap, norm=norm, alpha=0.7, edgecolor='gray', linewidth=0.5)

    ctx.add_basemap(ax, crs=gdf.crs.to_string(), source=ctx.providers.OpenStreetMap.Mapnik)

    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    ax_bounds = ax.get_position()
    cax = fig.add_axes([ax_bounds.x1 - 0.35, ax_bounds.y1, 0.35, 0.02])
    cbar = plt.colorbar(sm, cax=cax, orientation='horizontal', extend='max')
    cbar.set_ticks([0] + concentration_bounds)
    cbar.set_ticklabels(['0'] + [f'{b:.2e}' for b in concentration_bounds])

    if data_type == 'Air':
        cbar.set_label(f'{substance} Concentration (μg/m³)')
    else:  # Soil
        cbar.set_label(f'{substance} Concentration (μg/kg)')

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


def generate_images_from_hdf5(hdf5_file, output_folder, start_x, start_y, cell_size, substance):
    colors = ['#FFFFFF00', '#FFFFFF', '#87CEFA', '#ADFF2F', '#FFA500', '#FF0000']

    with h5py.File(hdf5_file, 'r') as hf:
        for data_type in ['Air', 'Soil']:
            if data_type not in hf:
                print(f"Warning: {data_type} data not found in {hdf5_file}. Skipping.")
                continue

            group = hf[data_type]
            output_subfolder = os.path.join(output_folder, data_type)
            os.makedirs(output_subfolder, exist_ok=True)

            # 전체 데이터셋에 대한 농도 범위 계산
            all_data = np.array([group[key][()] for key in group.keys()])
            concentration_bounds = get_color_ranges(substance, data_type, all_data)

            for i, key in enumerate(tqdm(group.keys(), desc=f"Generating {data_type} images for {substance}")):
                data = group[key][()]
                timestamp = group[key].attrs['timestamp']

                year = int(timestamp[:4])
                month = int(timestamp[6:7])
                day = int(timestamp[9:10])
                hour = int(timestamp[11:13])
                time_obj = datetime(year, month, day, hour)
                formatted_time = time_obj.strftime("%Y-%m-%d %H:%M")

                title = f'{substance} {data_type} Concentration at {formatted_time}'

                fig, ax = visualize_grid(data, start_x, start_y, cell_size, concentration_bounds, colors, title, data_type, substance)
                plt.savefig(os.path.join(output_subfolder, f'frame_{i:03d}.png'), dpi=300)
                plt.close(fig)

def process_all_substances():
    hdf5_folder = r"C:\CAM_test_analysis\hdf5_data"
    output_base_folder = r"C:\CAM_test_analysis\graph"
    start_x = 164191
    start_y = 470659
    cell_size = 100

    substances = [
        "Ethylacetate", "Benzene", "Methylacrylate", "Methyltrichlorosilane", "Ethyleneoxide",
        "Triethylamine", "Methylethylketoneperoxide", "Methylhydrazine", "Chloromethane", "Methylamine",
        "Vinylchloride", "Carbondisulfide", "Trimethylamine", "Propyleneoxide", "Methylvinylketone", "Nitrobenzene"
    ]

    for folder_number, substance in enumerate(substances, start=26):
        hdf5_file = os.path.join(hdf5_folder, f"Concentration{folder_number}.h5")
        output_folder = os.path.join(output_base_folder, f"Concentration{folder_number}")
        generate_images_from_hdf5(hdf5_file, output_folder, start_x, start_y, cell_size, substance)

if __name__ == "__main__":
    process_all_substances()