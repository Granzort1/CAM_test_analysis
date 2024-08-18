import os
import matplotlib.pyplot as plt
import matplotlib.animation as animation

def create_animation(input_folder, output_file):
    frames = [plt.imread(os.path.join(input_folder, f)) for f in sorted(os.listdir(input_folder)) if f.endswith('.png')]
    fig, ax = plt.subplots(figsize=(10, 10))
    im = ax.imshow(frames[0])
    plt.axis('off')

    def animate(i):
        im.set_array(frames[i])
        return [im]

    anim = animation.FuncAnimation(fig, animate, frames=len(frames), interval=500, blit=True)

    Writer = animation.writers['ffmpeg']
    writer = Writer(fps=2, metadata=dict(artist='Me'), bitrate=1800)
    anim.save(output_file, writer=writer)

    plt.close(fig)
    print(f"애니메이션이 '{output_file}' 파일로 저장되었습니다.")

def process_all_substances():
    base_folder = r"C:\CAM_test_analysis\graph"
    output_folder = r"C:\CAM_test_analysis\animations"
    os.makedirs(output_folder, exist_ok=True)

    # 테스트를 위해 첫 번째 물질(Concentration26)만 처리
    substance_folder = os.path.join(base_folder, "Concentration26")
    for data_type in ['Air', 'Soil']:
        input_folder = os.path.join(substance_folder, data_type)
        if not os.path.exists(input_folder):
            print(f"Warning: {input_folder} does not exist. Skipping.")
            continue
        output_file = os.path.join(output_folder, f"Concentration26_{data_type}_animation.mp4")
        create_animation(input_folder, output_file)

    # 주석 처리된 전체 물질 처리 코드
    """
    for folder_number in range(26, 42):
        substance_folder = os.path.join(base_folder, f"Concentration{folder_number}")
        for data_type in ['Air', 'Soil']:
            input_folder = os.path.join(substance_folder, data_type)
            if not os.path.exists(input_folder):
                print(f"Warning: {input_folder} does not exist. Skipping.")
                continue
            output_file = os.path.join(output_folder, f"Concentration{folder_number}_{data_type}_animation.mp4")
            create_animation(input_folder, output_file)
    """

if __name__ == "__main__":
    process_all_substances()