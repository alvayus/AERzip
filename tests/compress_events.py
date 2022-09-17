import gc
import os
import time
from tkinter import Tk
from tkinter.filedialog import askopenfilename

import matplotlib.pyplot as plt
from pyNAVIS import *

# TODO: Test files
# TODO: Fix and complete documentation and images (remove prunedBytes)
# TODO: Writing in AEDAT 4.0?
# TODO: Add a bytesToPrunedBytes function
from AERzip.compressionFunctions import compressDataFromStoredFile, decompressDataFromFile

if __name__ == '__main__':
    root = Tk()
    root.withdraw()  # we don't want a full GUI, so keep the root window from appearing

    # Select a file
    print("Select an AEDAT file in events folder")
    path = askopenfilename(parent=root)

    # Until file is selected
    while not path:
        print("Not file selected. Select a new AEDAT file")
        path = askopenfilename(parent=root)

    ext = os.path.splitext(path)[1]
    file = os.path.basename(path)
    dir_path = os.path.dirname(path)
    dataset = os.path.basename(dir_path)
    main_folder = os.path.basename(os.path.dirname(dir_path))

    # Until file is an original AEDAT file (in events folder)
    while not main_folder == "events" or dataset == "events" or not ext == ".aedat":
        if main_folder != "events":
            print("Wrong folder. You must select an original AEDAT file contained in events folder with the following"
                  "path: '../events/dataset/file.aedat'")

        if ext != ".aedat":
            print("This file is not an AEDAT file. You must select a file with extension '.aedat'")

        path = askopenfilename(parent=root)

        '''# Until file is selected again
        while not path:
            print("Not file selected. Select a new AEDAT file")
            path = askopenfilename(parent=root)'''

        if not path:
            raise Exception("No file has been selected.")

        ext = os.path.splitext(path)[1]
        file = os.path.basename(path)
        dir_path = os.path.dirname(path)
        dataset = os.path.basename(dir_path)
        main_folder = os.path.basename(os.path.dirname(dir_path))

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

    while not number or not 1 <= number <= 4:
        number = int(input("This is not a number or not a number in the range 1-4. \nPlease, enter your option again: "))

    settings = None
    if number == 1:
        settings = jAER_settings
    elif number == 2:
        settings = MatLab_settings
    elif number == 3:
        settings = MatLab_settings_mono
    elif number == 4:
        settings = MatLab_settings_32ch_mono

    # Compress data
    print("\nCurrently these are the possible compressors:\n\n"
          "1) ZSTD (Best speed, good compression)\n"
          "2) LZMA (Worst speed, best compression)\n"
          "3) LZ4 (Good speed, good compression)\n")

    compressors = ["ZSTD", "LZMA", "LZ4"]

    number = int(input("Enter your option: "))
    while not number or not 1 <= number <= 4:
        number = input("This is not a number or not a number in the range 1-3. \nPlease, enter your option again: ")

    compressor = compressors[number - 1]

    _, dst_path = compressDataFromStoredFile(path, settings, compressor=compressor, ignore_overwriting=False)

    # --- COMPRESSED DATA ---
    start_time = time.time()

    # Decompress the compressed aedat file
    spikes_file, new_settings = decompressDataFromFile(dst_path, settings)
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
    print("\nLoading " + "/" + main_folder + "/" + dataset + "/" + file + " (original aedat file)")
    spikes_file = Loaders.loadAEDAT(path, settings)
    end_time = time.time()
    print("Original file loaded in " + '{0:.3f}'.format(end_time - start_time) + " seconds")
    gc.collect()  # Cleaning memory

    # Plots
    print("\nShowing original file plots...")
    start_time = time.time()

    Plots.spikegram(spikes_file, settings, verbose=True)
    gc.collect()  # Cleaning memory
    Plots.sonogram(spikes_file, settings, verbose=True)
    gc.collect()  # Cleaning memory
    Plots.histogram(spikes_file, settings, verbose=True)
    gc.collect()  # Cleaning memory
    Plots.average_activity(spikes_file, settings, verbose=True)
    gc.collect()  # Cleaning memory
    Plots.difference_between_LR(spikes_file, settings, verbose=True)

    plt.show()

    end_time = time.time()
    print("Plots visualization took " + '{0:.3f}'.format(end_time - start_time) + " seconds")

    # --- REPORTS ---
    print("\nGenerating original file plots...")
    start_time = time.time()

    report_directory = os.path.dirname(dir_path) + "/../reports/"

    if not os.path.exists(report_directory + dataset + "/"):
        os.makedirs(report_directory + dataset + "/")

    ReportFunctions.PDF_report(path, settings, report_directory + dataset + "/" + file + ".pdf",
                               plots=["Spikegram", "Sonogram", "Histogram",
                                      "Average activity", "Difference between L/R"])

    end_time = time.time()
    print("Plots generation took " + '{0:.3f}'.format(end_time - start_time) + " seconds")