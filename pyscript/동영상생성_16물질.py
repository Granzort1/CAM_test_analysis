import os
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from tqdm import tqdm


def create_animation(input_folder, output_file):
    frames = [plt.imread(os.path.join(input_folder, f)) for f in sorted(os.listdir(input_folder)) if f.endswith('.png')]

    if not frames:
        print(f"No PNG files found in {input_folder}. Skipping animation creation.")
        return

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
    print(f"Animation saved as '{output_file}'")


def process_all_substances():
    base_folder = r"C:\CAM_test_analysis\graph"
    output_folder = r"C:\CAM_test_analysis\animations"
    os.makedirs(output_folder, exist_ok=True)

    substances = [
        "Ethylacetate", "Benzene", "Methylacrylate", "Methyltrichlorosilane", "Ethyleneoxide",
        "Triethylamine", "Methylethylketoneperoxide", "Methylhydrazine", "Chloromethane", "Methylamine",
        "Vinylchloride", "Carbondisulfide", "Trimethylamine", "Propyleneoxide", "Methylvinylketone", "Nitrobenzene"
    ]

    for folder_number, substance_name in tqdm(enumerate(substances, start=26), total=len(substances),
                                              desc="Processing substances"):
        substance_folder = os.path.join(base_folder, f"Concentration{folder_number}")
        for data_type in ['Air', 'Soil']:
            input_folder = os.path.join(substance_folder, data_type)
            if not os.path.exists(input_folder):
                print(f"Warning: {input_folder} does not exist. Skipping.")
                continue
            output_file = os.path.join(output_folder, f"{substance_name}_{data_type}_animation.mp4")
            try:
                create_animation(input_folder, output_file)
            except Exception as e:
                print(f"Error processing {substance_name} {data_type}: {str(e)}")


if __name__ == "__main__":
    process_all_substances()