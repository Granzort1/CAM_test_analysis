import os
from generate_images import generate_images
from create_animation import create_animation

def main():
    # 설정
    test_folder = r"C:\CAM_test_analysis\input\Concentration31\1hour_interval\Air"
    start_x = 164191
    start_y = 470659
    cell_size = 100
    output_file = 'concentration_animation.mp4'

    # 이미지 생성
    generate_images(test_folder, start_x, start_y, cell_size)

    # 동영상 생성
    create_animation(output_file)

    print("모든 작업이 완료되었습니다.")

if __name__ == "__main__":
    main()