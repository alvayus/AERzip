import gc
import time
from tkinter import Tk
from tkinter.filedialog import askopenfilename

import matplotlib.pyplot as plt
import numpy as np
from pyNAVIS import *

from compressFunctions import decompressDataFromFile, compressDataFromFile

if __name__ == '__main__':
    # Define source settings
    jAER_settings = MainSettings(num_channels=64, mono_stereo=1, on_off_both=1, address_size=4, ts_tick=1,
                                 bin_size=10000)
    MatLab_settings = MainSettings(num_channels=64, mono_stereo=1, on_off_both=1, address_size=2, ts_tick=0.2,
                                   bin_size=10000)

    settings = jAER_settings

    # Find the original aedat file
    print("Select a file in events folder")
    Tk().withdraw()  # we don't want a full GUI, so keep the root window from appearing
    split_path = askopenfilename().split("/")

    len_split_path = len(split_path)
    directory = "/".join(split_path[0:len_split_path - 2])
    dataset = split_path[len_split_path - 2]
    file = split_path[len_split_path - 1]

    # Compress data
    compressDataFromFile(directory, directory + "/../compressedEvents", dataset, file, settings,
                         compressor="ZSTD", ignore_overwriting=False)

    '''# --- COMPRESSED DATA ---
    start_time = time.time()
    # Decompress the compressed aedat file
    compressed_spikes_file, new_settings = decompressDataFromFile(directory + "/../compressedEvents",
                                                                  dataset, file, settings)
    gc.collect()  # Cleaning memory

    # Check the compressed aedat file
    spikes_file_is_ok = Functions.check_SpikesFile(compressed_spikes_file, new_settings)
    
    end_time = time.time()
    print(end_time - start_time)

    # Plots
    print("Showing compressed file plots...")
    start_time = time.time()

    Plots.spikegram(compressed_spikes_file, new_settings, verbose=True)
    gc.collect()  # Cleaning memory
    Plots.sonogram(compressed_spikes_file, new_settings, ordered=spikes_file_is_ok, verbose=True)
    gc.collect()  # Cleaning memory
    Plots.histogram(compressed_spikes_file, new_settings, verbose=True)
    gc.collect()  # Cleaning memory
    Plots.average_activity(compressed_spikes_file, new_settings, verbose=True)
    gc.collect()  # Cleaning memory
    Plots.difference_between_LR(compressed_spikes_file, new_settings, verbose=True)

    end_time = time.time()
    print("Plots generation took " + '{0:.3f}'.format(end_time - start_time) + " seconds")

    plt.show()
    gc.collect()  # Cleaning memory'''

    # --- ORIGINAL DATA ---
    # Load the original aedat file. Prints added to show loading time
    start_time = time.time()
    spikes_info = Loaders.loadAEDAT(directory + "/" + dataset + "/" + file,
                                    settings.address_size, settings.timestamp_size)
    end_time = time.time()
    print("Load original aedat file has took: " + '{0:.3f}'.format(end_time - start_time) + " seconds")
    gc.collect()  # Cleaning memory

    # Check the original aedat file
    order_is_ok = Functions.check_SpikesFile(spikes_info, settings)
    if not order_is_ok:
        Functions.order_SpikesFile(spikes_info)

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
    Plots.difference_between_LR(spikes_info, settings, verbose=True)

    end_time = time.time()
    print("Plots generation took " + '{0:.3f}'.format(end_time - start_time) + " seconds")

    start_time = time.time()
    plt.show()
    end_time = time.time()
    print("It took " + '{0:.3f}'.format(end_time - start_time) + " seconds to display the plots.")