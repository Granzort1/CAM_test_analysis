import os
import re
import numpy as np
from datetime import datetime

# 테스트 폴더 경로 설정
test_folder = r"C:\CAM_test_analysis\input\Concentration31\1hour_interval\Air"

def parse_filename(filename):
    # 파일명에서 날짜와 시간 추출을 위한 정규표현식
    pattern = r'Air(\d{4})Y\s*(\d{1,2})M\s*(\d{1,2})D\s*(\d{1,2})H\.TXT'
    match = re.match(pattern, filename)
    if match:
        year, month, day, hour = map(int, match.groups())
        return datetime(year, month, day, hour)
    return None

# 폴더 내 텍스트 파일 목록 가져오기
files = [f for f in os.listdir(test_folder) if f.endswith('.TXT')]

# 파일명으로부터 날짜/시간 파싱 및 정렬
file_datetimes = [(f, parse_filename(f)) for f in files]
file_datetimes = [(f, dt) for f, dt in file_datetimes if dt is not None]
file_datetimes.sort(key=lambda x: x[1])  # 날짜/시간으로 정렬

if not file_datetimes:
    print("올바른 형식의 파일이 없습니다.")
else:
    print(f"총 {len(file_datetimes)}개의 유효한 파일을 찾았습니다.")

    # 결과 요약을 위한 변수들
    correct_structure = 0
    correct_data_count = 0
    all_numeric = 0

    # 각 파일을 처리
    for i, (file, file_datetime) in enumerate(file_datetimes, 1):
        file_path = os.path.join(test_folder, file)
        print(f"\n처리 중인 파일 ({i}/{len(file_datetimes)}): {file}")
        print(f"파일 날짜/시간: {file_datetime}")

        # 파일 읽기
        with open(file_path, 'r') as f:
            lines = f.readlines()

        # 데이터 처리
        data = []
        for line in lines:
            row = line.strip().split()
            row = [float(x) for x in row if x]  # 빈 문자열 제거
            data.append(row)

        # numpy 배열로 변환
        data_array = np.array(data)

        # 데이터 구조 확인
        shape = data_array.shape
        print(f"데이터 형태: {shape}")

        if shape == (150, 150):
            print("데이터 구조가 올바릅니다 (150x150).")
            correct_structure += 1
        else:
            print("데이터 구조가 올바르지 않습니다.")

        # 총 데이터 수 확인
        total_elements = data_array.size
        print(f"총 데이터 수: {total_elements}")

        if total_elements == 22500:
            print("총 데이터 수가 올바릅니다 (22500개).")
            correct_data_count += 1
        else:
            print("총 데이터 수가 올바르지 않습니다.")

        # 모든 값이 숫자인지 확인
        if np.issubdtype(data_array.dtype, np.number):
            print("모든 값이 숫자입니다.")
            all_numeric += 1
        else:
            print("숫자가 아닌 값이 포함되어 있습니다.")

        # 데이터 범위 확인
        min_value = np.min(data_array)
        max_value = np.max(data_array)
        print(f"데이터 범위: {min_value} ~ {max_value}")

    # 결과 요약 출력
    print("\n처리 결과 요약:")
    print(f"총 파일 수: {len(file_datetimes)}")
    print(f"올바른 구조(150x150)를 가진 파일 수: {correct_structure}")
    print(f"올바른 데이터 수(22500개)를 가진 파일 수: {correct_data_count}")
    print(f"모든 값이 숫자인 파일 수: {all_numeric}")
    print(f"시간 범위: {file_datetimes[0][1]} ~ {file_datetimes[-1][1]}")

print("모든 파일 처리가 완료되었습니다.")