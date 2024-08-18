import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter, MaxNLocator

# 기본 경로 설정
base_input_path = r'C:\CAM_test_analysis\input'
output_path = r'C:\CAM_test_analysis\output'

# 거리 구간 정의 (미터 단위)
distance_ranges = [(0, 500), (500, 1000), (1000, 3000), (3000, 5000), (5000, 7000)]

# 중심점 설정 (75번째와 76번째 격자 사이)
center = (75.5, 75.5)

# 물질 목록
substances = [
    "Ethylacetate", "Benzene", "Methylacrylate", "Methyltrichlorosilane", "Ethyleneoxide",
    "Triethylamine", "Methylethylketoneperoxide", "Methylhydrazine", "Chloromethane", "Methylamine",
    "Vinylchloride", "Carbondisulfide", "Trimethylamine", "Propyleneoxide", "Methylvinylketone", "Nitrobenzene"
]


def calculate_distance(x, y, center):
    """격자 위치로부터 중심까지의 거리 계산"""
    return np.sqrt((x - center[0]) ** 2 + (y - center[1]) ** 2) * 100  # 100m per grid


def read_file(file_path):
    """텍스트 파일을 읽어 numpy 배열로 변환"""
    with open(file_path, 'r') as f:
        lines = f.readlines()
    data = [line.strip().split() for line in lines]
    return np.array(data, dtype=float)


def get_max_concentrations(data, distance_ranges):
    """각 거리 구간별 최대 농도 계산"""
    max_concentrations = []
    for start, end in distance_ranges:
        mask = (calculate_distance(*np.indices(data.shape), center) >= start) & \
               (calculate_distance(*np.indices(data.shape), center) < end)
        masked_data = data[mask]
        masked_data = masked_data[masked_data > 0]  # 0 제외
        if masked_data.size > 0:
            max_concentrations.append(np.max(masked_data))
        else:
            max_concentrations.append(np.nan)  # 모든 값이 0이면 NaN 추가
    return max_concentrations


def process_substance(folder_path, substance_name):
    results = [[] for _ in range(len(distance_ranges))]
    times = []

    for filename in sorted(os.listdir(folder_path)):
        if filename.endswith('.TXT'):
            minutes = int(filename.split()[1].split('min')[0])
            times.append(minutes)

            file_path = os.path.join(folder_path, filename)
            data = read_file(file_path)

            max_concentrations = get_max_concentrations(data, distance_ranges)

            for i, concentration in enumerate(max_concentrations):
                results[i].append(concentration)

    return times, results


def plot_substances(substances_data, output_path, medium, distance_range):
    plt.figure(figsize=(12, 8))

    for substance_name, (times, results) in substances_data.items():
        range_index = distance_ranges.index(distance_range)
        valid_data = [(t, r) for t, r in zip(times, results[range_index]) if not np.isnan(r)]
        if valid_data:
            plot_times, plot_results = zip(*valid_data)
            plt.plot(plot_times, plot_results, label=substance_name)

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


# 메인 프로세스
for medium in ['Air', 'Soil']:
    for distance_range in distance_ranges:
        substances_data = {}

        for i, substance_name in enumerate(substances, start=26):
            folder_name = f'Concentration{i}'
            if medium == 'Air':
                folder_path = os.path.join(base_input_path, folder_name, '1minute_interval', 'Air1')
            else:
                folder_path = os.path.join(base_input_path, folder_name, '1minute_interval', 'Soil')

            if os.path.exists(folder_path):
                times, results = process_substance(folder_path, substance_name)
                substances_data[substance_name] = (times, results)
            else:
                print(f"폴더가 존재하지 않습니다: {folder_path}")

        plot_substances(substances_data, output_path, medium, distance_range)

print("모든 그래프 생성이 완료되었습니다.")