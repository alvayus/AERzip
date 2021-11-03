import gc
import os
import time
from tkinter import Tk
from tkinter.filedialog import askopenfilename

import matplotlib.pyplot as plt
from pyNAVIS import *

from compressionFunctions import decompressDataFromFile, compressDataFromFile

# TODO: Test files
# TODO: Fix and complete documentation
# TODO: Timestamps compression by adapt_timestamps function. We could save the minimum in a byte and then rescue it
# TODO: Extension header
# TODO: Insert the maximum and minimum fields in the SpikesFile object of pyNAVIS
# TODO: Insert the ordered and adapted fields in the SpikesFile object of pyNAVIS


if __name__ == '__main__':
    root = Tk()
    root.withdraw()  # we don't want a full GUI, so keep the root window from appearing

    # Find the original aedat file
    print("Select a file in events folder")
    path = askopenfilename(parent=root)

    if path:
        split_path = path.split("/")
        len_split_path = len(split_path)
    else:
        raise ValueError("Not file selected. Select a new file")

    if split_path[len_split_path - 3] != "events":
        raise ValueError("Wrong folder. You must select a original aedat file in events folder")

    directory = "/".join(split_path[0:len_split_path - 2])
    dataset = split_path[len_split_path - 2]
    file = split_path[len_split_path - 1]

    split_file = file.split(".")
    len_split_file = len(split_file)

    if file.split(".")[len_split_file - 1] != "aedat":
        raise ValueError("This file is not an aedat file")

    # Define source settings
    jAER_settings = MainSettings(num_channels=64, mono_stereo=1, on_off_both=1, address_size=4, ts_tick=1,
                                 bin_size=10000)
    MatLab_settings = MainSettings(num_channels=64, mono_stereo=1, on_off_both=1, address_size=2, ts_tick=0.2,
                                   bin_size=10000)
    MatLab_settings_mono = MainSettings(num_channels=64, mono_stereo=0, on_off_both=1, address_size=2, ts_tick=0.2,
                                        bin_size=10000)
    MatLab_settings_32ch_mono = MainSettings(num_channels=32, mono_stereo=0, on_off_both=1, address_size=2, ts_tick=0.2,
                                             bin_size=10000)

    print("\nCurrently these are the predefined settings:\n\n"
          "1) jAER_settings (num_channels=64, mono_stereo=1, address_size=4)\n"
          "2) MatLab_settings (num_channels=64, mono_stereo=1, address_size=2)\n"
          "3) MatLab_settings_mono (num_channels=64, mono_stereo=0, address_size=2)\n"
          "4) MatLab_settings_32ch_mono (num_channels=64, mono_stereo=0, address_size=2)\n")

    number = int(input("Enter your option: "))

    if number == 1:
        settings = jAER_settings
    elif number == 2:
        settings = MatLab_settings
    elif number == 3:
        settings = MatLab_settings_mono
    elif number == 4:
        settings = MatLab_settings_32ch_mono
    else:
        settings = None

    # Compress data
    compressDataFromFile(directory, directory + "/../compressedEvents", dataset, file, settings,
                         compressor="ZSTD", ignore_overwriting=False)

    # --- COMPRESSED DATA ---
    start_time = time.time()
    # Decompress the compressed aedat file
    spikes_file, new_settings = decompressDataFromFile(directory + "/../compressedEvents",
                                                       dataset, file, settings, compressor="ZSTD")
    gc.collect()  # Cleaning memory

    end_time = time.time()
    print("Total time: " + '{0:.3f}'.format(end_time - start_time) + " seconds")

    # Plots
    print("\nShowing compressed file plots...")
    start_time = time.time()

    Plots.spikegram(spikes_file, new_settings, verbose=True)
    gc.collect()  # Cleaning memory
    Plots.sonogram(spikes_file, new_settings, verbose=True)
    gc.collect()  # Cleaning memory
    Plots.histogram(spikes_file, new_settings, verbose=True)
    gc.collect()  # Cleaning memory
    Plots.average_activity(spikes_file, new_settings, verbose=True)
    gc.collect()  # Cleaning memory
    Plots.difference_between_LR(spikes_file, new_settings, verbose=True)
    gc.collect()

    plt.show()

    end_time = time.time()
    print("Plots generation took " + '{0:.3f}'.format(end_time - start_time) + " seconds")

    gc.collect()

    # --- ORIGINAL DATA ---
    # Load the original aedat file. Prints added to show loading time
    start_time = time.time()
    print("\nLoading " + "/" + dataset + "/" + file + " (original aedat file)")
    spikes_file = Loaders.loadAEDAT(directory + "/" + dataset + "/" + file, settings)
    end_time = time.time()
    print("Original file loaded in " + '{0:.3f}'.format(end_time - start_time) + " seconds")
    gc.collect()  # Cleaning memory

    # Plots
    print("\nShowing original file plots...")
    start_time = time.time()

    spk_fig = Plots.spikegram(spikes_file, settings, verbose=True)
    gc.collect()  # Cleaning memory
    sng_fig = Plots.sonogram(spikes_file, settings, verbose=True)
    gc.collect()  # Cleaning memory
    _, hst_fig = Plots.histogram(spikes_file, settings, verbose=True)
    gc.collect()  # Cleaning memory
    _, _, avg_fig = Plots.average_activity(spikes_file, settings, verbose=True)
    gc.collect()  # Cleaning memory
    dlr_fig = Plots.difference_between_LR(spikes_file, settings, verbose=True)

    plt.show()

    end_time = time.time()
    print("Plots visualization took " + '{0:.3f}'.format(end_time - start_time) + " seconds")

    # Generate the plots PDF
    print("\nGenerating original file plots...")
    start_time = time.time()

    report_directory = directory + "/../reports/"

    if not os.path.exists(report_directory + dataset + "/"):
        os.makedirs(report_directory + dataset + "/")

    ReportFunctions.PDF_report(path, settings, report_directory + dataset + "/" + file + ".pdf",
                               plots=["Spikegram", "Sonogram", "Histogram",
                                      "Average activity", "Difference between L/R"])

    end_time = time.time()
    print("Plots generation took " + '{0:.3f}'.format(end_time - start_time) + " seconds")

