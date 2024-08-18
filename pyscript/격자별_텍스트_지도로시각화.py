import os
import numpy as np
import matplotlib.pyplot as plt
from shapely.geometry import Polygon
import geopandas as gpd
import contextily as ctx
from matplotlib.colors import LinearSegmentedColormap, BoundaryNorm
from matplotlib.patches import Rectangle
from matplotlib.animation import FuncAnimation
import matplotlib.animation as animation
from matplotlib.colors import ListedColormap


# 테스트 폴더 경로 설정
test_folder = r"C:\CAM_test_analysis\input\Concentration31\1hour_interval\Air"

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

def visualize_grid(data, start_x, start_y, cell_size=100):
    rows, cols = data.shape

    # 격자 생성
    grid_cells = []
    for i in range(rows):
        for j in range(cols):
            x1, y1 = start_x + j * cell_size, start_y + (rows - i - 1) * cell_size
            x2, y2 = x1 + cell_size, y1 + cell_size
            corners = [(x1, y1), (x2, y1), (x2, y2), (x1, y2)]
            grid_cells.append(Polygon(corners))

    # GeoDataFrame 생성
    gdf = gpd.GeoDataFrame({
        'geometry': grid_cells,
        'concentration': data.flatten()
    }, crs='EPSG:5186')

    # 시각화
    fig, ax = plt.subplots(figsize=(10, 10), constrained_layout=True)
    gdf.plot(column='concentration', ax=ax, cmap=cmap, norm=norm, alpha=0.7, edgecolor='gray', linewidth=0.5)

    # 축 비율을 1:1로 설정
    #ax.set_aspect('equal')

    # 배경 지도 추가 (EPSG:5186으로 재투영)
    ctx.add_basemap(ax, crs=gdf.crs.to_string(), source=ctx.providers.OpenStreetMap.Mapnik)
    # 배경 지도 추가 (EPSG:5186으로 재투영)

    # 범례 추가 (지도 내부 오른쪽 위에 위치)
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])

    # 범례의 위치와 크기 설정
    ax_bounds = ax.get_position()
    cax = fig.add_axes([ax_bounds.x1 - 0.35, ax_bounds.y1, 0.35, 0.02])  # 위치와 크기 조정
    cbar = plt.colorbar(sm, cax=cax, orientation='horizontal')
    cbar.set_ticks(concentration_bounds)
    cbar.set_ticklabels([f'{b/1000:.1e}' for b in concentration_bounds])  # 1/1000배로 조정
    cbar.set_label('Concentration (μg/m³)')  # 단위 추가

    # 범례에 투명도 적용
    for i, color in enumerate(colors):
        cax.add_patch(Rectangle((i / n_bins, 0), 1 / n_bins, 1, facecolor=color, alpha=0.7, edgecolor='none'))

    # 축 레이블 설정 (km 단위)
    ax.set_xlabel('X Coordinate (km)')
    ax.set_ylabel('Y Coordinate (km)')

    # 축 눈금 설정 (km 단위)
    x_ticks = np.linspace(start_x, start_x + cols * cell_size, 6)
    y_ticks = np.linspace(start_y, start_y + rows * cell_size, 6)
    ax.set_xticks(x_ticks)
    ax.set_yticks(y_ticks)
    ax.set_xticklabels([f'{x / 1000:.2f}' for x in x_ticks])
    ax.set_yticklabels([f'{y / 1000:.2f}' for y in y_ticks])

    #ax.set_ylim(start_y - cell_size * 5, start_y + rows * cell_size + cell_size * 15)

    return fig, ax

def print_color_ranges(concentration_bounds, colors):
    print("Color ranges:")
    for i in range(len(colors)):
        if i == 0:
            print(f"{colors[i]}: 0 - {concentration_bounds[i+1]/1000:.2e} μg/m³")
        elif i == len(colors) - 1:
            print(f"{colors[i]}: > {concentration_bounds[i]/1000:.2e} μg/m³")
        else:
            print(f"{colors[i]}: {concentration_bounds[i]/1000:.2e} - {concentration_bounds[i+1]/1000:.2e} μg/m³")

def update(frame):
    ax.clear()
    file = sorted_files[frame]
    data = read_data(os.path.join(test_folder, file))
    gdf = gpd.GeoDataFrame({
        'geometry': grid_cells,
        'concentration': data.flatten()
    }, crs='EPSG:5186')
    gdf.plot(column='concentration', ax=ax, cmap=cmap, norm=norm, alpha=0.7, edgecolor='gray', linewidth=0.8)
    ctx.add_basemap(ax, crs=gdf.crs.to_string(), source=ctx.providers.OpenStreetMap.Mapnik)

    # 축 설정
    ax.set_xlabel('X Coordinate (km)')
    ax.set_ylabel('Y Coordinate (km)')
    ax.set_xticks(x_ticks)
    ax.set_yticks(y_ticks)
    ax.set_xticklabels([f'{x / 1000:.2f}' for x in x_ticks])
    ax.set_yticklabels([f'{y / 1000:.2f}' for y in y_ticks])
    ax.set_ylim(start_y - cell_size * 5, start_y + rows * cell_size + cell_size * 15)

    # 제목 추가 (파일 이름에서 날짜와 시간 추출)
    title = file.split('.')[0].split('Air')[1]
    ax.set_title(f'Concentration at {title}')

    return ax

# 메인 코드
if __name__ == "__main__":
    # 좌표 입력 받기
    start_x = float(164191)
    start_y = float(470659)
    cell_size = 100

    # 농도 범위 찾기
    concentration_bounds = find_concentration_range(test_folder)

    # 파일 목록 가져오기 및 정렬
    sorted_files = sorted([f for f in os.listdir(test_folder) if f.endswith('.TXT')])

    if not sorted_files:
        print("폴더에 텍스트 파일이 없습니다.")
    else:
        # 첫 번째 파일로 초기 설정
        first_file = os.path.join(test_folder, sorted_files[0])
        data = read_data(first_file)
        rows, cols = data.shape

        # 격자 생성 (한 번만 생성)
        grid_cells = []
        for i in range(rows):
            for j in range(cols):
                x1, y1 = start_x + j * cell_size, start_y + i * cell_size
                x2, y2 = x1 + cell_size, y1 + cell_size
                corners = [(x1, y1), (x2, y1), (x2, y2), (x1, y2)]
                grid_cells.append(Polygon(corners))

        # 색상 매핑 설정
        colors = ['#FFFFFF', '#87CEFA', '#ADFF2F', '#FFFF00', '#FFA500', '#FF0000']

        print_color_ranges(concentration_bounds, colors)

        n_bins = len(colors)
        cmap = LinearSegmentedColormap.from_list('custom', colors, N=n_bins)
        norm = BoundaryNorm(concentration_bounds, cmap.N)

        # 축 눈금 설정
        x_ticks = np.linspace(start_x, start_x + cols * cell_size, 6)
        y_ticks = np.linspace(start_y, start_y + rows * cell_size, 6)

        # 각 시간에 대한 이미지 저장
        os.makedirs('frames', exist_ok=True)
        for i, file in enumerate(sorted_files):
            data = read_data(os.path.join(test_folder, file))
            fig, ax = visualize_grid(data, start_x, start_y)
            title = file.split('.')[0].split('Air')[1]
            ax.set_title(f'Concentration at {title}')
            plt.savefig(f'frames/frame_{i:03d}.png', dpi=600)
            plt.close(fig)

        # 동영상 생성
        frames = [plt.imread(f'frames/frame_{i:03d}.png') for i in range(len(sorted_files))]
        fig, ax = plt.subplots(figsize=(10, 10))
        im = ax.imshow(frames[0])
        plt.axis('off')

        def animate(i):
            im.set_array(frames[i])
            return [im]

        anim = animation.FuncAnimation(fig, animate, frames=len(frames), interval=500, blit=True)

        # 동영상으로 저장
        Writer = animation.writers['ffmpeg']
        writer = Writer(fps=2, metadata=dict(artist='Me'), bitrate=1800)
        anim.save('concentration_animation.mp4', writer=writer)

        print("애니메이션이 'concentration_animation.mp4' 파일로 저장되었습니다.")

        print("시각화가 완료되었습니다.")