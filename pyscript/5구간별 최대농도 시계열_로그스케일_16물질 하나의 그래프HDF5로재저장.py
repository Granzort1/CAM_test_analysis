import os
import numpy as np
import h5py

# 기본 경로 설정
base_input_path = r'C:\CAM_test_analysis\input'
output_path = r'C:\CAM_test_analysis\output'
hdf5_file = os.path.join(output_path, 'concentration_data.h5')

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


def process_and_save_to_hdf5():
    with h5py.File(hdf5_file, 'w') as f:
        for medium in ['Air', 'Soil']:
            medium_group = f.create_group(medium)

            for i, substance_name in enumerate(substances, start=26):
                substance_group = medium_group.create_group(substance_name)
                folder_name = f'Concentration{i}'

                if medium == 'Air':
                    folder_path = os.path.join(base_input_path, folder_name, '1minute_interval', 'Air1')
                else:
                    folder_path = os.path.join(base_input_path, folder_name, '1minute_interval', 'Soil')

                if os.path.exists(folder_path):
                    times = []
                    results = [[] for _ in range(len(distance_ranges))]

                    for filename in sorted(os.listdir(folder_path)):
                        if filename.endswith('.TXT'):
                            minutes = int(filename.split()[1].split('min')[0])
                            times.append(minutes)

                            file_path = os.path.join(folder_path, filename)
                            data = read_file(file_path)
                            max_concentrations = get_max_concentrations(data, distance_ranges)

                            for i, concentration in enumerate(max_concentrations):
                                results[i].append(concentration)

                    substance_group.create_dataset('times', data=times)
                    for i, (start, end) in enumerate(distance_ranges):
                        substance_group.create_dataset(f'{start}m-{end}m', data=results[i])
                else:
                    print(f"폴더가 존재하지 않습니다: {folder_path}")


if __name__ == "__main__":
    print("HDF5 파일 생성 중...")
    process_and_save_to_hdf5()
    print(f"HDF5 파일이 '{hdf5_file}'에 생성되었습니다.")