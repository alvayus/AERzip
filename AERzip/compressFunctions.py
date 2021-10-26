import copy
import os
import sys
import time

import lz4.frame
import zstandard
from pyNAVIS import *

# TODO: Fix paths


def loadCompressedAedat(directory, file_path, settings, verbose=True):
    # --- Check the filePath ---
    if not os.path.exists(directory + file_path) and verbose:
        print("Unable to find the specified compressed aedat file. Aborting...")
        sys.exit(1)

    # --- Get dataset folder and file name ---
    split_file_path = file_path.split('/')
    dataset = split_file_path[0]
    file_name = split_file_path[1]

    # --- Load data from compressed aedat file ---
    start_time = time.time()
    if verbose:
        print("Loading " + file_name + " (compressed aedat file)")

    file = open(directory + file_path, "rb")
    file_data = file.read()  # Read all the file
    compressor = file_data[0:4].decode("utf-8").strip()
    address_size = file_data[4] + 1
    compressed_data = file_data[5:]
    file.close()

    end_time = time.time()
    if verbose:
        print("Compressed file loaded in " + '{0:.3f}'.format(end_time - start_time) + " seconds")
        print("Decompressing " + file_name + " with " + str(address_size) + "-byte addresses through " +
              compressor + " decompressor")
    start_time = time.time()

    # --- Decompress data ---
    if compressor == "ZSTD":
        dctx = zstandard.ZstdDecompressor()
        decompressed_data = dctx.decompress(compressed_data)
    elif compressor == "LZ4":
        decompressed_data = lz4.frame.decompress(compressed_data)
    else:
        print("Unable to perform " + compressor + " decompression. Aborting...")
        sys.exit(1)

    bytes_per_spike = address_size + 4
    num_spikes = len(decompressed_data) / bytes_per_spike
    if not num_spikes.is_integer():
        print("Spikes are not a whole number. Something went wrong. Aborting...")
        sys.exit(1)
    else:
        num_spikes = int(num_spikes)

    addresses = []
    timestamps = []

    for i in range(num_spikes):
        index = i * bytes_per_spike
        addresses.append(decompressed_data[index:(index + address_size)])
        timestamps.append(decompressed_data[(index + address_size):(index + bytes_per_spike)])

    # Return the new spikes file
    addresses = [int.from_bytes(x, "big") for x in addresses]  # Bytes to ints
    timestamps = [int.from_bytes(x, "big") for x in timestamps]  # Bytes to ints
    spikes_file = SpikesFile(addresses, timestamps)

    # Return the modified settings
    new_settings = copy.deepcopy(settings)
    new_settings.address_size = address_size

    end_time = time.time()
    if verbose:
        print("Decompression achieved in " + '{0:.3f}'.format(end_time - start_time) + " seconds")

    return [spikes_file, new_settings]


def compressAedat(events_dir, file_path, settings, ignore_overwriting=True, verbose=True, compressor="ZSTD",
                  return_data=True):
    # --- Get bytes needed to address and timestamp representation ---
    address_size = int(round(settings.num_channels * (settings.mono_stereo + 1) *
                            (settings.on_off_both + 1) / 256))
    org_address_size = settings.address_size
    # TODO: Timestamp size = 2
    # orgTimestampSize = settings.

    # --- Get dataset folder and file name ---
    split_file_path = file_path.split('/')
    dataset = split_file_path[0]
    file_name = split_file_path[1]

    # --- Check the file ---
    compressed_events_dir = events_dir + "../compressedEvents/"

    if not ignore_overwriting:
        if os.path.exists(compressed_events_dir + file_path):
            print("The compressed aedat file for this aedat file already exists\n"
                  "Do you want to overwrite it? Y/N")
            option = input()

            if option == "N":
                print("File compression has been cancelled")
                return

    # --- Load data from original aedat file ---
    start_time = time.time()
    if verbose:
        print("Loading " + file_name + " (original aedat file)")

    # TODO: Optimize loadAEDAT
    data = Loaders.loadAEDAT(events_dir + file_path, settings)
    addresses = data.addresses
    timestamps = data.timestamps

    end_time = time.time()
    if verbose:
        print("Original file loaded in " + '{0:.3f}'.format(end_time - start_time) + " seconds")
        print("Compressing " + file_name + " with " + str(org_address_size) + "-byte addresses into an aedat file with "
              + str(address_size) + "-byte addresses through " + compressor + " compressor")
    start_time = time.time()

    # --- New data ---
    header = bytearray()
    raw_data = bytearray()

    # Header definition
    if compressor == "ZSTD":
        header.extend(bytes("ZSTD", "utf-8"))  # 4 bytes for the compressor
    elif compressor == "LZ4":
        header.extend(bytes("LZ4 ", "utf-8"))  # 4 bytes for the compressor
    else:
        print("Compressor not recognized. Aborting...")
        sys.exit(1)

    header.extend((address_size - 1).to_bytes(1, "big"))  # 1 byte for address size

    # Reorder the data by discarding useless addresses bytes
    for i in range(len(addresses) - 1):
        raw_data.extend(addresses[i].to_bytes(address_size, "big"))
        raw_data.extend(timestamps[i].to_bytes(4, "big"))

    # --- Compress and store the data ---
    if compressor == "ZSTD":
        cctx = zstandard.ZstdCompressor()
        compressed_data = cctx.compress(raw_data)
    else:
        compressed_data = lz4.frame.compress(raw_data)

    # Join header with compressed data
    file_data = header.join(compressed_data)

    # Check the destination folder
    if not os.path.exists(compressed_events_dir):
        os.makedirs(compressed_events_dir)

    if not os.path.exists(compressed_events_dir + dataset):
        os.makedirs(compressed_events_dir + dataset)

    file = open(compressed_events_dir + file_path, "wb")
    file.write(file_data)
    file.close()

    end_time = time.time()
    if verbose:
        print("Compression achieved in " + '{0:.3f}'.format(end_time - start_time) + " seconds")

    if return_data:
        return file_data
