import gc
import time
from tkinter.filedialog import askopenfilename

from pyNAVIS import *
import matplotlib.pyplot as plt
from tkinter import Tk

from compressFunctions import compressAedat, loadCompressedAedat

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
    splitPath = askopenfilename().split("/")

    lenSplitPath = len(splitPath)
    directory = "/".join(splitPath[0:lenSplitPath-2]) + "/"
    filePath = "/".join(splitPath[lenSplitPath-2:lenSplitPath])

    # --- COMPRESSED DATA ---
    # Compress the original aedat file
    compressAedat(directory, filePath, settings, False)
    gc.collect()  # Cleaning memory

    # Load the compressed aedat file
    [compressedSpikes_File, newSettings] = loadCompressedAedat(directory + "../compressedEvents/", filePath, settings)
    gc.collect()  # Cleaning memory

    # Adapt the compressed aedat file
    Functions.check_SpikesFile(compressedSpikes_File, newSettings)
    compressedSpikes_File.timestamps = Functions.adapt_timestamps(compressedSpikes_File.timestamps, newSettings)

    # Plots
    print("Showing compressed file plots...")
    timeIni = time.time()

    # TODO: Optimize plots for compressed files
    Plots.spikegram(compressedSpikes_File, newSettings, verbose=True)
    gc.collect()  # Cleaning memory
    Plots.sonogram(compressedSpikes_File, newSettings, verbose=True)
    gc.collect()  # Cleaning memory
    Plots.histogram(compressedSpikes_File, newSettings, verbose=True)
    gc.collect()  # Cleaning memory
    Plots.average_activity(compressedSpikes_File, newSettings, verbose=True)
    gc.collect()  # Cleaning memory
    Plots.difference_between_LR(compressedSpikes_File, newSettings, verbose=True)

    timeEnd = time.time()
    print("Plots generation took " + '{0:.3f}'.format(timeEnd - timeIni) + " seconds")

    plt.show()
    gc.collect()  # Cleaning memory

    # --- ORIGINAL DATA ---
    # Load the original aedat file. Prints added to show loading time
    timeIni = time.time()
    spikes_info = Loaders.loadAEDAT(directory + filePath, settings)
    timeEnd = time.time()
    print("Load original aedat file has took: " + str(timeEnd - timeIni))
    gc.collect()  # Cleaning memory

    # Adapt the original aedat file
    Functions.check_SpikesFile(spikes_info, settings)
    spikes_info.timestamps = Functions.adapt_timestamps(spikes_info.timestamps, settings)

    # Plots
    print("Showing original file plots...")
    timeIni = time.time()

    Plots.spikegram(spikes_info, settings, verbose=True)
    gc.collect()  # Cleaning memory
    Plots.sonogram(spikes_info, settings, verbose=True)
    gc.collect()  # Cleaning memory
    Plots.histogram(spikes_info, settings, verbose=True)
    gc.collect()  # Cleaning memory
    Plots.average_activity(spikes_info, settings, verbose=True)
    gc.collect()  # Cleaning memory
    Plots.difference_between_LR(spikes_info, settings, verbose=True)

    timeEnd = time.time()
    print("Plots generation took " + '{0:.3f}'.format(timeEnd - timeIni) + " seconds")

    plt.show()
