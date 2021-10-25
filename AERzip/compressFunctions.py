import copy
import os
import sys
import time

import lz4.frame
import zstandard
from pyNAVIS import *

# TODO: Fix variable names


def loadCompressedAedat(directory, filePath, settings, verbose=True):
    # --- Check the filePath ---
    if not os.path.exists(directory + filePath) and verbose:
        print("Unable to find the specified compressed aedat file. Aborting...")
        sys.exit(1)

    # --- Get dataset folder and file name ---
    splitFilePath = filePath.split('/')
    dataset = splitFilePath[0]
    fileName = splitFilePath[1]

    # --- Load data from compressed aedat file ---
    timeIni = time.time()
    if verbose:
        print("Loading " + fileName + " (compressed aedat file)")

    file = open(directory + filePath, "rb")
    filedata = file.read()  # Read all the file
    compressor = filedata[0:4].decode("utf-8").strip()
    addressSize = filedata[4] + 1
    compressedData = filedata[5:]
    file.close()

    timeEnd = time.time()
    if verbose:
        print("Compressed file loaded in " + '{0:.3f}'.format(timeEnd - timeIni) + " seconds")
        print("Decompressing " + fileName + " with " + str(addressSize) + "-byte addresses through " +
              compressor + " decompressor")
    timeIni = time.time()

    # --- Decompress data ---
    if compressor == "ZSTD":
        dctx = zstandard.ZstdDecompressor()
        decompressedData = dctx.decompress(compressedData)
    elif compressor == "LZ4":
        decompressedData = lz4.frame.decompress(compressedData)
    else:
        print("Unable to perform " + compressor + " decompression. Aborting...")
        sys.exit(1)

    bytesPerSpike = addressSize + 4
    numSpikes = len(decompressedData) / bytesPerSpike
    if not numSpikes.is_integer():
        print("Spikes are not a whole number. Something went wrong. Aborting...")
        sys.exit(1)
    else:
        numSpikes = int(numSpikes)

    addresses = []
    timestamps = []

    for i in range(numSpikes):
        index = i * bytesPerSpike
        addresses.append(decompressedData[index:(index + addressSize)])
        timestamps.append(decompressedData[(index + addressSize):(index + bytesPerSpike)])

    # Return the new spikes file
    addresses = [int.from_bytes(x, "big") for x in addresses]  # Bytes to ints
    timestamps = [int.from_bytes(x, "big") for x in timestamps]  # Bytes to ints
    spikes_file = SpikesFile(addresses, timestamps)

    # Return the modified settings
    newSettings = copy.deepcopy(settings)
    newSettings.address_size = addressSize

    timeEnd = time.time()
    if verbose:
        print("Decompression achieved in " + '{0:.3f}'.format(timeEnd - timeIni) + " seconds")

    return [spikes_file, newSettings]


def compressAedat(eventsDir, filePath, settings, ignoreOverwrite=True, verbose=True, compressor="ZSTD", returnData=True):
    # --- Get bytes needed to address and timestamp representation ---
    addressSize = int(round(settings.num_channels * (settings.mono_stereo + 1) *
                            (settings.on_off_both + 1) / 256))
    orgAddressSize = settings.address_size
    # TODO: Timestamp size = 2
    # orgTimestampSize = settings.

    # --- Get dataset folder and file name ---
    splitFilePath = filePath.split('/')
    dataset = splitFilePath[0]
    fileName = splitFilePath[1]

    # --- Check the file ---
    compressedEventsDir = eventsDir + "../compressedEvents/"

    if not ignoreOverwrite:
        if os.path.exists(compressedEventsDir + filePath):
            print("The compressed aedat file for this aedat file already exists\n"
                  "Do you want to overwrite it? Y/N")
            option = input()

            if option == "N":
                print("File compression has been cancelled")
                return

    # --- Load data from original aedat file ---
    timeIni = time.time()
    if verbose:
        print("Loading " + fileName + " (original aedat file)")

    # TODO: Optimize loadAEDAT
    data = Loaders.loadAEDAT(eventsDir + filePath, settings)
    addresses = data.addresses
    timestamps = data.timestamps

    timeEnd = time.time()
    if verbose:
        print("Original file loaded in " + '{0:.3f}'.format(timeEnd - timeIni) + " seconds")
        print("Compressing " + fileName + " with " + str(orgAddressSize) + "-byte addresses into an aedat file with "
              + str(addressSize) + "-byte addresses through " + compressor + " compressor")
    timeIni = time.time()

    # --- New data ---
    header = bytearray()
    rawData = bytearray()

    # Header definition
    if compressor == "ZSTD":
        header.extend(bytes("ZSTD", "utf-8"))  # 4 bytes for the compressor
    elif compressor == "LZ4":
        header.extend(bytes("LZ4 ", "utf-8"))  # 4 bytes for the compressor
    else:
        print("Compressor not recognized. Aborting...")
        sys.exit(1)

    header.extend((addressSize - 1).to_bytes(1, "big"))  # 1 byte for address size

    # Reorder the data by discarding useless addresses bytes
    for i in range(len(addresses) - 1):
        rawData.extend(addresses[i].to_bytes(addressSize, "big"))
        rawData.extend(timestamps[i].to_bytes(4, "big"))

    # --- Compress and store the data ---
    if compressor == "ZSTD":
        cctx = zstandard.ZstdCompressor()
        compressedData = cctx.compress(rawData)
    else:
        compressedData = lz4.frame.compress(rawData)

    # Join header with compressed data
    fileData = header.join(compressedData)

    # Check the destination folder
    if not os.path.exists(compressedEventsDir):
        os.makedirs(compressedEventsDir)

    if not os.path.exists(compressedEventsDir + dataset):
        os.makedirs(compressedEventsDir + dataset)

    file = open(compressedEventsDir + filePath, "wb")
    file.write(fileData)
    file.close()

    timeEnd = time.time()
    if verbose:
        print("Compression achieved in " + '{0:.3f}'.format(timeEnd - timeIni) + " seconds")

    if returnData:
        return fileData
