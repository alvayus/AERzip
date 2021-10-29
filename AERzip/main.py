import gc
import time
from tkinter import Tk
from tkinter.filedialog import askopenfilename

import matplotlib.pyplot as plt
from pyNAVIS import *

from compressFunctions import decompressDataFromFile, compressDataFromFile

if __name__ == '__main__':
    # Define source settings
    jAER_settings = MainSettings(num_channels=64, mono_stereo=1, on_off_both=1, address_size=4, ts_tick=1,
                                 bin_size=10000)
    MatLab_settings = MainSettings(num_channels=64, mono_stereo=1, on_off_both=1, address_size=2, ts_tick=0.2,
                                   bin_size=10000)
    MatLab_settings_mono = MainSettings(num_channels=64, mono_stereo=0, on_off_both=1, address_size=2, ts_tick=0.2,
                                        bin_size=10000)
    MatLab_settings_32ch_mono = MainSettings(num_channels=32, mono_stereo=0, on_off_both=1, address_size=2, ts_tick=0.2,
                                        bin_size=10000)

    settings = jAER_settings

    # Find the original aedat file
    print("Select a file in events folder")
    Tk().withdraw()  # we don't want a full GUI, so keep the root window from appearing
    path = askopenfilename()

    if path:
        split_path = path.split("/")
    else:
        raise ValueError("Not file selected. Select a new file")

    len_split_path = len(split_path)
    directory = "/".join(split_path[0:len_split_path - 2])
    dataset = split_path[len_split_path - 2]
    file = split_path[len_split_path - 1]

    # Compress data
    compressDataFromFile(directory, directory + "/../compressedEvents", dataset, file, settings,
                         compressor="ZSTD", ignore_overwriting=False)

    # --- COMPRESSED DATA ---
    start_time = time.time()
    # Decompress the compressed aedat file
    raw_data, new_settings = decompressDataFromFile(directory + "/../compressedEvents",
                                                    dataset, file, settings)
    gc.collect()  # Cleaning memory

    # Check increasing timestamp order in the original aedat file
    _, order_is_ok, all_in_range = Functions.check_SpikesFile(raw_data, settings)
    if not all_in_range:
        raise ValueError("Addresses are not in range. Could be due to bad decoding")
    if not order_is_ok:
        Functions.order_SpikesFile(raw_data, settings)

    # Adapting timestamps
    raw_data.timestamps = Functions.adapt_timestamps(raw_data.timestamps, settings)

    end_time = time.time()
    print(end_time - start_time)

    # Plots
    print("Showing compressed file plots...")
    start_time = time.time()

    Plots.spikegram(raw_data, new_settings, verbose=True)
    gc.collect()  # Cleaning memory
    Plots.sonogram(raw_data, new_settings, verbose=True)
    gc.collect()  # Cleaning memory
    Plots.histogram(raw_data, new_settings, verbose=True)
    gc.collect()  # Cleaning memory
    Plots.average_activity(raw_data, new_settings, verbose=True)
    gc.collect()  # Cleaning memory
    # Plots.difference_between_LR(raw_data, new_settings, verbose=True)

    end_time = time.time()
    print("Plots generation took " + '{0:.3f}'.format(end_time - start_time) + " seconds")

    plt.show()
    gc.collect()  # Cleaning memory

    # --- ORIGINAL DATA ---
    # Load the original aedat file. Prints added to show loading time
    start_time = time.time()
    spikes_info = Loaders.loadAEDAT(directory + "/" + dataset + "/" + file, settings)
    end_time = time.time()
    print("Load original aedat file has took: " + '{0:.3f}'.format(end_time - start_time) + " seconds")
    gc.collect()  # Cleaning memory

    # Check increasing timestamp order in the original aedat file
    _, order_is_ok, all_in_range = Functions.check_SpikesFile(raw_data, settings)
    if not all_in_range:
        raise ValueError("Addresses are not in range. Could be due to bad decoding")
    if not order_is_ok:
        Functions.order_SpikesFile(spikes_info, settings)

    # Adapting timestamps
    spikes_info.timestamps = Functions.adapt_timestamps(spikes_info.timestamps, settings)

    # Plots
    print("Showing original file plots...")
    start_time = time.time()

    Plots.spikegram(spikes_info, settings, verbose=True)
    gc.collect()  # Cleaning memory
    Plots.sonogram(spikes_info, settings, verbose=True)
    gc.collect()  # Cleaning memory
    Plots.histogram(spikes_info, settings, verbose=True)
    gc.collect()  # Cleaning memory
    Plots.average_activity(spikes_info, settings, verbose=True)
    gc.collect()  # Cleaning memory
    # Plots.difference_between_LR(spikes_info, settings, verbose=True)

    end_time = time.time()
    print("Plots generation took " + '{0:.3f}'.format(end_time - start_time) + " seconds")

    plt.show()
