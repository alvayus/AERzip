import copy
import math
import os
import time
from bisect import bisect_left, bisect_right

import numpy as np
import matplotlib.pyplot as plt
from pyNAVIS import *


def loadCompressedAedat(directory, filePath, settings, verbose=True):
    timeIni = time.time()

    # Check the file
    if not os.path.exists(directory + filePath) and verbose:
        print("Unable to find the specified compressed aedat file")

    # Get dataset folder and file name
    splitFilePath = filePath.split('/')
    dataset = splitFilePath[0]
    fileName = splitFilePath[1]

    # Load data from compressed aedat file
    # Pack and unpack help: https://docs.python.org/3/library/struct.html
    '''unpack_param = ">B"
    if addressSize == 2:
        unpack_param = ">H"
    elif addressSize > 2:
        unpack_param = ">L"'''

    file = open(directory + filePath, "rb")

    if verbose:
        print("Loading " + fileName + " (compressed aedat file)")

    addresses = []
    timestamps = []

    # IMPORTANT: 1 byte of header
    addressSize = int.from_bytes(file.read(1), "big") + 1  # Load needed number of bytes

    address = file.read(addressSize)
    while address:
        timestamp = file.read(4)

        addresses.append(int.from_bytes(address, "big"))
        timestamps.append(int.from_bytes(timestamp, "big"))

        '''address = struct.unpack(unpack_param, address)[0]
        timestamp = struct.unpack(">L", timestamp)[0]

        addresses.append(address)
        timestamps.append(timestamp)'''

        address = file.read(addressSize)

    file.close()

    # Return the new spikes file
    spikes_file = SpikesFile(addresses, timestamps)

    # Return the modified settings
    newSettings = copy.deepcopy(settings)
    newSettings.address_size = addressSize

    timeEnd = time.time()

    if verbose:
        print("Compressed file loaded in " + '{0:.3f}'.format(timeEnd - timeIni) + " seconds")

    return [spikes_file, newSettings]


def compressAedat(eventsDir, filePath, settings, ignoreOverwrite=True, verbose=True):
    timeIni = time.time()

    # Bytes needed to address representation
    addressSize = int(round(settings.num_channels * (settings.mono_stereo + 1) *
                            (settings.on_off_both + 1) / 256))
    orgAddressSize = settings.address_size

    # Get dataset folder and file name
    splitFilePath = filePath.split('/')
    dataset = splitFilePath[0]
    fileName = splitFilePath[1]

    # Check the file and destination folder
    compressedEventsDir = eventsDir + "../compressedEvents/"

    if not ignoreOverwrite:
        if os.path.exists(compressedEventsDir + filePath):
            print("The compressed aedat file for this aedat file already exists\n"
                  "Do you want to overwrite it? Y/N")
            sumTime = time.time() - timeIni
            option = input()

            if option == "N":
                print("File compression has been cancelled")
                return
            else:
                timeIni = time.time() - sumTime

    if not os.path.exists(compressedEventsDir):
        os.mkdir(compressedEventsDir)

    if not os.path.exists(compressedEventsDir + dataset):
        os.mkdir(compressedEventsDir + dataset)

    # Load data from original aedat file
    if verbose:
        print("Loading " + fileName + " (original aedat file)")
    data = Loaders.loadAEDAT(eventsDir + filePath, settings)
    addresses = data.addresses
    timestamps = data.timestamps

    if verbose:
        print("Compressing " + fileName + " with " + str(orgAddressSize) + "-byte addresses into an aedat file with "
              + str(addressSize) + "-byte addresses")

    # Compress and save the data by discarding useless bytes
    # Pack and unpack help: https://docs.python.org/3/library/struct.html
    '''pack_param = ">B"
    if addressSize == 2:
        pack_param = ">H"
    elif addressSize > 2:
        pack_param = ">L"'''

    file = open(compressedEventsDir + filePath, "wb")

    # IMPORTANT: 1 byte of header
    file.write((addressSize - 1).to_bytes(1, "big"))  # Save needed number of bytes

    for i in range(len(addresses) - 1):
        file.write(addresses[i].to_bytes(addressSize, "big"))
        file.write(timestamps[i].to_bytes(4, "big"))
        '''address = struct.pack(pack_param, addresses[i])
        timestamp = struct.pack('>L', timestamps[i])

        file.write(address[:addressSize])
        file.write(timestamp)'''

    file.close()

    timeEnd = time.time()

    if verbose:
        print("Compression achieved in " + '{0:.3f}'.format(timeEnd - timeIni) + " seconds")
