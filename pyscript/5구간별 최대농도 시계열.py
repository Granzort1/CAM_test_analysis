import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import FuncFormatter, MaxNLocator

# 테스트 폴더 경로 설정
folder_path = r'C:\CAM_test_analysis\input\Concentration31\1minute_interval\Air'

# 거리 구간 정의 (미터 단위)
distance_ranges = [(0, 500), (500, 1000), (1000, 3000), (3000, 5000), (5000, 7000)]

# 중심점 설정 (75번째와 76번째 격자 사이)
center = (75.5, 75.5)


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
        max_concentrations.append(np.max(data[mask]))
    return max_concentrations


# 결과를 저장할 리스트 초기화
results = [[] for _ in range(len(distance_ranges))]
times = []

# 모든 파일 처리
for filename in sorted(os.listdir(folder_path)):
    if filename.endswith('.TXT') and filename.startswith('Air'):
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
    plt.plot(times, results[i], label=f'{start}m-{end}m')

plt.xlabel('Time (hours)')
plt.ylabel('Maximum Concentration')
plt.title('Maximum Concentration by Distance Range Over Time')
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

plt.grid(True, linestyle='--', alpha=0.7)
plt.tight_layout()

# 그래프 저장
plt.savefig('concentration_time_series.png', dpi=300)
plt.close()

print("그래프가 'concentration_time_series.png' 파일로 저장되었습니다.")