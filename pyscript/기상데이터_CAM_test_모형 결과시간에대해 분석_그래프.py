import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter, MaxNLocator
from matplotlib.dates import DateFormatter, HourLocator

# 기본 경로 설정
input_path = r'C:\CAM_test_analysis\input'
output_path = r'C:\CAM_test_analysis\output'
excel_file = os.path.join(input_path, 'met_data.xlsx')

# 데이터 읽기
df = pd.read_excel(excel_file, header=0)

# 시간 컬럼 생성 (사고 이후 시간)
df['time'] = pd.to_datetime(df.index, unit='h')

# 기온을 켈빈에서 섭씨로 변환
df['temp_celsius'] = df['temp'] - 273.15

# 풍속과 풍향 계산
df['wind_speed'] = np.sqrt(df['windX'] ** 2 + df['windY'] ** 2)
df['wind_direction'] = (np.arctan2(-df['windX'], -df['windY']) * 180 / np.pi + 360) % 360

def plot_temp_humidity(df, output_path):
    fig, ax1 = plt.subplots(figsize=(12, 8))
    ax1_twin = ax1.twinx()

    ax1.plot(df['time'], df['temp_celsius'], color='red', label='Temperature')
    ax1_twin.plot(df['time'], df['rh'], color='blue', label='Relative Humidity')

    ax1.set_ylabel('Temperature (°C)', color='red')
    ax1_twin.set_ylabel('Relative Humidity (%)', color='blue')

    ax1.tick_params(axis='y', colors='red')
    ax1_twin.tick_params(axis='y', colors='blue')

    plt.title('Temperature and Relative Humidity')

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax1_twin.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')

    ax1.set_xlabel('Time After Incident (HH:MM)')
    ax1.xaxis.set_major_formatter(DateFormatter('%H:%M'))
    ax1.xaxis.set_major_locator(HourLocator(interval=2))

    plt.grid(True, linestyle='--', alpha=0.7)
    fig.tight_layout(pad=2.0)  # 여백 추가

    output_file = os.path.join(output_path, 'temp_humidity.png')
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"온도 및 습도 그래프가 '{output_file}' 파일로 저장되었습니다.")

def plot_wind(df, output_path):
    fig, ax1 = plt.subplots(figsize=(12, 8))
    ax1_twin = ax1.twinx()

    ax1.plot(df['time'], df['wind_speed'], color='green', label='Wind Speed')
    ax1_twin.plot(df['time'], df['wind_direction'], color='purple', label='Wind Direction')

    ax1.set_ylabel('Wind Speed (m/s)', color='green')
    ax1_twin.set_ylabel('Wind Direction (degrees)', color='purple')

    ax1.tick_params(axis='y', colors='green')
    ax1_twin.tick_params(axis='y', colors='purple')

    plt.title('Wind Speed and Direction')

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax1_twin.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')

    ax1.set_xlabel('Time After Incident (HH:MM)')
    ax1.xaxis.set_major_formatter(DateFormatter('%H:%M'))
    ax1.xaxis.set_major_locator(HourLocator(interval=2))

    plt.grid(True, linestyle='--', alpha=0.7)
    fig.tight_layout(pad=2.0)  # 여백 추가

    output_file = os.path.join(output_path, 'wind_data.png')
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"풍속 및 풍향 그래프가 '{output_file}' 파일로 저장되었습니다.")

if __name__ == "__main__":
    if not os.path.exists(excel_file):
        print(f"Error: Excel 파일 '{excel_file}'이 존재하지 않습니다.")
    else:
        print("그래프 생성 중...")
        plot_temp_humidity(df, output_path)
        plot_wind(df, output_path)
        print("모든 그래프 생성이 완료되었습니다.")