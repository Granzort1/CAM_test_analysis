import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import FuncFormatter, MaxNLocator
from adjustText import adjust_text
import h5py

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


def process_hdf5_data(hdf5_file, output_path, substance_name, medium):
    with h5py.File(hdf5_file, 'r') as f:
        substance_group = f[medium][substance_name]
        times = substance_group['times'][:]
        results = [substance_group[f'{start}m-{end}m'][:] for start, end in distance_ranges]

    # 토양 데이터인 경우 단위 변환 (ug/m³ to ug/kg)
    if medium == 'Soil':
        results = [np.array(r) * 1000 for r in results]  # 1 m³ of soil ≈ 1000 kg

    # 그래프 그리기
    plt.figure(figsize=(8, 6))
    colors = plt.cm.rainbow(np.linspace(0, 1, len(distance_ranges)))
    texts = []
    for i, ((start, end), color) in enumerate(zip(distance_ranges, colors)):
        valid_data = [(t, r) for t, r in zip(times, results[i]) if not np.isnan(r)]
        if valid_data:
            plot_times, plot_results = zip(*valid_data)
            plt.plot(plot_times, plot_results, label=f'{start}m-{end}m', color=color)

            # 전체 시간 동안의 최대값 계산 및 표시
            max_value = max(plot_results)
            max_time = plot_times[plot_results.index(max_value)]
            texts.append(plt.text(max_time, max_value, f'Max: {max_value:.2e}', color=color))

    # x축 레이블 수정
    plt.xlabel('Time After Model Start (HH:MM)')

    # y축 레이블 수정 (매체에 따라 다른 단위 사용)
    if medium == 'Air':
        plt.ylabel('Maximum Concentration (ug/m³)')
    else:
        plt.ylabel('Maximum Concentration (ug/kg)')

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

    # 텍스트 위치 조정
    adjust_text(texts)

    plt.tight_layout()

    # 그래프 저장 (간략한 파일명 사용)
    output_file = os.path.join(output_path, f'{substances.index(substance_name) + 26}_{medium}.png')
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"그래프가 '{output_file}' 파일로 저장되었습니다.")


# 모든 물질에 대해 처리
for substance_name in substances:
    for medium in ['Air', 'Soil']:
        process_hdf5_data(hdf5_file, output_path, substance_name, medium)

print("모든 그래프 생성이 완료되었습니다.")