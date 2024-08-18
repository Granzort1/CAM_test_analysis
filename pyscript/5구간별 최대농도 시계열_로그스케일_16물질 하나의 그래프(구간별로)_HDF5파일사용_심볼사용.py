import os
import numpy as np
import h5py
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter, MaxNLocator
from cycler import cycler

# 기본 경로 설정
output_path = r'C:\CAM_test_analysis\output'
hdf5_file = os.path.join(output_path, 'concentration_data.h5')

# 거리 구간 정의 (미터 단위)
distance_ranges = [(0, 500), (500, 1000), (1000, 3000), (3000, 5000), (5000, 7000)]

# 물질 목록
substances = [
    "Ethylacetate", "Benzene", "Methylacrylate", "Methyltrichlorosilane", "Ethyleneoxide",
    "Triethylamine", "Methylethylketoneperoxide", "Methylhydrazine", "Chloromethane", "Methylamine",
    "Vinylchloride", "Carbondisulfide", "Trimethylamine", "Propyleneoxide", "Methylvinylketone", "Nitrobenzene"
]


def plot_substances_from_hdf5(output_path, medium, distance_range):
    plt.figure(figsize=(12, 8))

    # 색상, 선 스타일, 마커 스타일 설정
    colors = plt.cm.tab20(np.linspace(0, 1, len(substances)))
    line_styles = ['-', '--', '-.', ':']
    marker_styles = ['o', 's', '^', 'D', 'v', '<', '>', 'p', '*', 'h', 'H', '+', 'x', 'd', '|', '_']
    plt.rc('axes', prop_cycle=(cycler(color=colors) +
                               cycler(linestyle=line_styles * 4) +
                               cycler(marker=marker_styles)))

    max_concentrations = {}
    plot_data = {}

    with h5py.File(hdf5_file, 'r') as f:
        medium_group = f[medium]
        range_key = f'{distance_range[0]}m-{distance_range[1]}m'

        for substance_name in substances:
            substance_group = medium_group[substance_name]
            times = substance_group['times'][:]
            concentrations = substance_group[range_key][:]

            valid_data = [(t, c) for t, c in zip(times, concentrations) if not np.isnan(c)]
            if valid_data:
                plot_times, plot_results = zip(*valid_data)
                plot_data[substance_name] = (plot_times, plot_results)
                max_concentrations[substance_name] = max(plot_results)

    # Sort substances by maximum concentration for this specific distance range
    sorted_substances = sorted(max_concentrations, key=max_concentrations.get, reverse=True)

    # Plot data in order of maximum concentration
    for substance_name in sorted_substances:
        plot_times, plot_results = plot_data[substance_name]
        plt.plot(plot_times, plot_results, label=f"{substance_name} (Max: {max_concentrations[substance_name]:.2e})",
                 alpha=0.7, linewidth=1.5, markersize=4, markevery=0.1)

    plt.xlabel('Time After Model Start (HH:MM)')
    plt.ylabel('Maximum Concentration (ug/m³)')
    title = f'Maximum {medium} Concentration for {distance_range[0]}m-{distance_range[1]}m Range'
    if medium == 'Air':
        title += ' (0-10m height)'
    plt.title(title)
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.yscale('log')
    plt.grid(True, linestyle='--', alpha=0.7)

    def format_time(x, pos):
        hours = int(x // 60)
        minutes = int(x % 60)
        return f'{hours:02d}:{minutes:02d}'

    plt.gca().xaxis.set_major_formatter(FuncFormatter(format_time))
    plt.gca().xaxis.set_major_locator(MaxNLocator(nbins=10))

    plt.tight_layout()

    output_file = os.path.join(output_path, f'{medium}_{distance_range[0]}m-{distance_range[1]}m.png')
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"그래프가 '{output_file}' 파일로 저장되었습니다.")


if __name__ == "__main__":
    if not os.path.exists(hdf5_file):
        print(f"Error: HDF5 파일 '{hdf5_file}'이 존재하지 않습니다.")
        print("먼저 HDF5 파일 생성 스크립트를 실행해주세요.")
    else:
        print("그래프 생성 중...")
        for medium in ['Air', 'Soil']:
            for distance_range in distance_ranges:
                plot_substances_from_hdf5(output_path, medium, distance_range)
        print("모든 그래프 생성이 완료되었습니다.")