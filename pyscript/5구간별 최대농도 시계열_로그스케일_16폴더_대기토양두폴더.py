import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
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


def process_folder(folder_path, output_path, folder_num, substance_name, medium):
    # 결과를 저장할 리스트 초기화
    results = [[] for _ in range(len(distance_ranges))]
    times = []

    # 모든 파일 처리
    for filename in sorted(os.listdir(folder_path)):
        if filename.endswith('.TXT') and filename.startswith(medium):
            # 파일 이름에서 시간 추출
            minutes = int(filename.split()[1].split('min')[0])
            times.append(minutes)

            # 파일 읽기
            file_path = os.path.join(folder_path, filename)
            data = read_file(file_path)

            # 최대 농도 계산
            max_concentrations = get_max_concentrations(data, distance_ranges)

            # 결과 저장
            for i, concentration in enumerate(max_concentrations):
                results[i].append(concentration)

    # 그래프 그리기
    plt.figure(figsize=(12, 6))
    for i, (start, end) in enumerate(distance_ranges):
        valid_data = [(t, r) for t, r in zip(times, results[i]) if not np.isnan(r)]
        if valid_data:
            plot_times, plot_results = zip(*valid_data)
            plt.plot(plot_times, plot_results, label=f'{start}m-{end}m')

    plt.xlabel('Time (hours)')
    plt.ylabel('Maximum Concentration')
    plt.title(f'Maximum {medium} Concentration of {substance_name} by Distance Range Over Time')
    plt.legend()

    # x축 설정
    max_time = max(times)
    plt.xlim(0, max_time)

    def format_time(x, pos):
        hours = int(x // 60)
        minutes = int(x % 60)
        return f'{hours:02d}:{minutes:02d}'

    plt.gca().xaxis.set_major_formatter(FuncFormatter(format_time))
    plt.gca().xaxis.set_major_locator(MaxNLocator(nbins=10))  # 최대 10개의 주요 틱 표시
    plt.yscale('log')  # y축을 로그 스케일로 설정

    plt.grid(True, linestyle='--', alpha=0.7)
    plt.tight_layout()

    # 그래프 저장 (간략한 파일명 사용)
    output_file = os.path.join(output_path, f'{folder_num}_{medium}.png')
    plt.savefig(output_file, dpi=300)
    plt.close()

    print(f"그래프가 '{output_file}' 파일로 저장되었습니다.")


# 모든 폴더에 대해 처리
for i in range(26, 42):
    folder_name = f'Concentration{i}'
    for medium in ['Air', 'Soil']:
        folder_path = os.path.join(base_input_path, folder_name, '1minute_interval', medium)

        if os.path.exists(folder_path):
            substance_index = i - 26
            if substance_index < len(substances):
                substance_name = substances[substance_index]
            else:
                substance_name = f"Unknown Substance {i}"

            process_folder(folder_path, output_path, i, substance_name, medium)
        else:
            print(f"폴더가 존재하지 않습니다: {folder_path}")

print("모든 그래프 생성이 완료되었습니다.")