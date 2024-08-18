import os
import numpy as np
import matplotlib.pyplot as plt
from shapely.geometry import Polygon
import geopandas as gpd
import contextily as ctx
from matplotlib.colors import LinearSegmentedColormap, BoundaryNorm
from matplotlib.patches import Rectangle

def read_data(file_path):
    with open(file_path, 'r') as f:
        lines = f.readlines()
    data = []
    for line in lines:
        row = [float(x) for x in line.strip().split() if x]
        data.append(row)
    return np.array(data)

def find_concentration_range(folder_path):
    all_data = []
    for file in os.listdir(folder_path):
        if file.endswith('.TXT'):
            data = read_data(os.path.join(folder_path, file))
            all_data.extend(data.flatten())
    all_data = np.array(all_data)
    non_zero_data = all_data[all_data > 0]
    percentiles = np.percentile(non_zero_data, [20, 40, 60, 80])
    return [0] + list(percentiles) + [np.max(all_data)]

def visualize_grid(data, start_x, start_y, cell_size, concentration_bounds, colors):
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

    n_bins = len(colors)
    cmap = LinearSegmentedColormap.from_list('custom', colors, N=n_bins)
    norm = BoundaryNorm(concentration_bounds, cmap.N)

    fig, ax = plt.subplots(figsize=(10, 10), constrained_layout=True)
    gdf.plot(column='concentration', ax=ax, cmap=cmap, norm=norm, alpha=0.7, edgecolor='gray', linewidth=0.5)

    ctx.add_basemap(ax, crs=gdf.crs.to_string(), source=ctx.providers.OpenStreetMap.Mapnik)

    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    ax_bounds = ax.get_position()
    cax = fig.add_axes([ax_bounds.x1 - 0.35, ax_bounds.y1, 0.35, 0.02])
    cbar = plt.colorbar(sm, cax=cax, orientation='horizontal')
    cbar.set_ticks(concentration_bounds)
    cbar.set_ticklabels([f'{b/1000:.1e}' for b in concentration_bounds])
    cbar.set_label('Concentration (μg/m³)')

    for i, color in enumerate(colors):
        cax.add_patch(Rectangle((i / n_bins, 0), 1 / n_bins, 1, facecolor=color, alpha=0.7, edgecolor='none'))

    ax.set_xlabel('X Coordinate (km)')
    ax.set_ylabel('Y Coordinate (km)')
    x_ticks = np.linspace(start_x, start_x + cols * cell_size, 6)
    y_ticks = np.linspace(start_y, start_y + rows * cell_size, 6)
    ax.set_xticks(x_ticks)
    ax.set_yticks(y_ticks)
    ax.set_xticklabels([f'{x / 1000:.2f}' for x in x_ticks])
    ax.set_yticklabels([f'{y / 1000:.2f}' for y in y_ticks])

    return fig, ax

def generate_images(substance_folder, substance_number, start_x, start_y, cell_size):
    concentration_bounds = find_concentration_range(substance_folder)
    colors = ['#FFFFFF', '#87CEFA', '#ADFF2F', '#FFFF00', '#FFA500', '#FF0000']

    sorted_files = sorted([f for f in os.listdir(substance_folder) if f.endswith('.TXT')])

    output_folder = os.path.join(r'C:\CAM_test_analysis\graph', f'Concentration{substance_number}')
    os.makedirs(output_folder, exist_ok=True)

    for i, file in enumerate(sorted_files):
        data = read_data(os.path.join(substance_folder, file))
        fig, ax = visualize_grid(data, start_x, start_y, cell_size, concentration_bounds, colors)
        title = file.split('.')[0].split('Air')[1]
        ax.set_title(f'Concentration{substance_number} at {title}')
        plt.savefig(os.path.join(output_folder, f'frame_{i:03d}.png'), dpi=300)
        plt.close(fig)

    print(f"Concentration{substance_number}에 대한 이미지 생성이 완료되었습니다.")

def process_all_substances():
    base_folder = r"C:\CAM_test_analysis\input"
    start_x = 164191
    start_y = 470659
    cell_size = 100

    # 테스트를 위해 첫 번째 물질(Concentration26)만 처리
    test_folder_number = 26
    test_folder = os.path.join(base_folder, f"Concentration{test_folder_number}", "1hour_interval", "Air")
    generate_images(test_folder, test_folder_number, start_x, start_y, cell_size)

    # 주석 처리된 전체 물질 처리 코드
    """
    for folder_number in range(26, 42):
        substance_folder = os.path.join(base_folder, f"Concentration{folder_number}", "1hour_interval", "Air")
        generate_images(substance_folder, folder_number, start_x, start_y, cell_size)
    """

if __name__ == "__main__":
    process_all_substances()