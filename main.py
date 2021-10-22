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

    # Load the compressed aedat file
    [compressedSpikes_File, newSettings] = loadCompressedAedat(directory + "../compressedEvents/", filePath, settings)

    # Adapt the compressed aedat file
    Functions.check_SpikesFile(compressedSpikes_File, newSettings)
    compressedSpikes_File.timestamps = Functions.adapt_timestamps(compressedSpikes_File.timestamps, newSettings)

    # Plots
    print("Showing compressed file plots...")
    timeIni = time.time()

    Plots.spikegram(compressedSpikes_File, newSettings)
    Plots.sonogram(compressedSpikes_File, newSettings)
    Plots.histogram(compressedSpikes_File, newSettings)
    Plots.average_activity(compressedSpikes_File, newSettings)
    Plots.difference_between_LR(compressedSpikes_File, newSettings)

    timeEnd = time.time()
    print("The generation of the plots generation took " + '{0:.3f}'.format(timeEnd - timeIni) + " seconds")

    plt.show()

    # --- ORIGINAL DATA ---
    # Load the original aedat file
    timeIni = time.time()
    spikes_info = Loaders.loadAEDAT(directory + filePath, settings)
    timeEnd = time.time()
    print("Load original aedat file has took: " + str(timeEnd - timeIni))

    # Adapt the original aedat file
    Functions.check_SpikesFile(spikes_info, settings)
    spikes_info.timestamps = Functions.adapt_timestamps(spikes_info.timestamps, settings)

    # Plots
    print("Showing original file plots...")
    timeIni = time.time()

    Plots.spikegram(spikes_info, settings)
    Plots.sonogram(spikes_info, settings)
    Plots.histogram(spikes_info, settings)
    Plots.average_activity(spikes_info, settings)
    Plots.difference_between_LR(spikes_info, settings)

    timeEnd = time.time()
    print("The generation of the plots generation took " + '{0:.3f}'.format(timeEnd - timeIni) + " seconds")

    plt.show()
