import os
import numpy as np
import h5py
from tqdm import tqdm


def read_data(file_path):
    with open(file_path, 'r') as f:
        lines = f.readlines()
    data = []
    for line in lines:
        row = [float(x) for x in line.strip().split() if x]
        data.append(row)
    return np.array(data)


def convert_to_hdf5(base_folder, output_folder):
    os.makedirs(output_folder, exist_ok=True)

    for folder_number in tqdm(range(26, 42), desc="Processing substances"):
        substance_folder = os.path.join(base_folder, f"Concentration{folder_number}", "1hour_interval", "Air")
        output_file = os.path.join(output_folder, f"Concentration{folder_number}.h5")

        with h5py.File(output_file, 'w') as hf:
            sorted_files = sorted([f for f in os.listdir(substance_folder) if f.endswith('.TXT')])

            for i, file in enumerate(sorted_files):
                data = read_data(os.path.join(substance_folder, file))
                hf.create_dataset(f"frame_{i:03d}", data=data, compression="gzip")
                hf[f"frame_{i:03d}"].attrs['timestamp'] = file.split('.')[0].split('Air')[1]

        print(f"Saved {output_file}")


if __name__ == "__main__":
    base_folder = r"C:\CAM_test_analysis\input"
    output_folder = r"C:\CAM_test_analysis\hdf5_data"
    convert_to_hdf5(base_folder, output_folder)