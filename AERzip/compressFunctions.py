import copy
import os
import sys
import time

import lz4.frame
import zstandard
from pyNAVIS import *

from AERzip.CompressedFileHeader import CompressedHeader


def compressData(data, compressor="ZSTD"):
    if compressor == "ZSTD":
        cctx = zstandard.ZstdCompressor()
        compressed_data = cctx.compress(data)
    else:
        compressed_data = lz4.frame.compress(data)

    return compressed_data


def compressDataFromFile(src_events_dir, dst_compressed_events_dir, dataset_name, file_name,
                         settings, compressor="ZSTD", store=True, ignore_overwriting=True, verbose=True):
    # --- Get bytes needed to address and timestamp representation ---
    address_size = int(round(settings.num_channels * (settings.mono_stereo + 1) *
                             (settings.on_off_both + 1) / 256))
    org_address_size = settings.address_size
    # TODO: Timestamp size = 2
    # orgTimestampSize = settings.

    # --- Check the file ---
    if store and not ignore_overwriting:
        if os.path.exists(dst_compressed_events_dir + dataset_name + file_name):
            print("The compressed aedat file associated with this aedat file already exists\n"
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
    spikes_file = Loaders.loadAEDAT(src_events_dir + dataset_name + file_name, settings)

    end_time = time.time()
    if verbose:
        print("Original file loaded in " + '{0:.3f}'.format(end_time - start_time) + " seconds")
        print("Compressing " + file_name + " with " + str(org_address_size) + "-byte addresses into an aedat file with "
              + str(address_size) + "-byte addresses through " + compressor + " compressor")
    start_time = time.time()

    # --- New data ---
    header = CompressedHeader(compressor, address_size).toBytes()
    raw_smallest_data = discardBytes(spikes_file, address_size, 4)  # Discard useless bytes

    # Compress the data
    compressed_data = compressData(raw_smallest_data, compressor)

    # Join header with compressed data
    file_data = header.join(compressed_data)

    # --- Store the data ---
    if store:
        # Check the destination folder
        if not os.path.exists(dst_compressed_events_dir):
            os.makedirs(dst_compressed_events_dir)

        if not os.path.exists(dst_compressed_events_dir + dataset_name):
            os.makedirs(dst_compressed_events_dir + dataset_name)

        # Write the file
        file = open(dst_compressed_events_dir + dataset_name + file_name, "wb")
        file.write(file_data)
        file.close()

    end_time = time.time()
    if verbose:
        print("Compression achieved in " + '{0:.3f}'.format(end_time - start_time) + " seconds")

    return file_data


def loadCompressedFile(src_compressed_file_path):
    # Read all the file
    file = open(src_compressed_file_path, "rb")
    file_data = file.read()

    # Header extraction from the file
    header = CompressedHeader()

    start_index = 0
    end_index = header.library_version_length
    header.library_version = file_data[start_index:end_index].decode("utf-8").strip()

    start_index = end_index
    end_index = start_index + header.compressor_length
    header.compressor = file_data[start_index:end_index].decode("utf-8").strip()

    start_index = end_index
    end_index = start_index + header.address_length
    header.address_size = file_data[start_index:end_index] + 1

    start_index = end_index
    end_index = start_index + header.timestamp_length
    header.timestamp_size = file_data[start_index:end_index] + 1

    start_index = end_index
    compressed_data = file_data[start_index:]

    # Close the file
    file.close()

    return header, compressed_data


def decompressData(compressed_data, compressor="ZSTD"):
    if compressor == "ZSTD":
        dctx = zstandard.ZstdDecompressor()
        decompressed_data = dctx.decompress(compressed_data)
    elif compressor == "LZ4":
        decompressed_data = lz4.frame.decompress(compressed_data)
    else:
        print("Unable to perform " + compressor + " decompression. Aborting...")
        sys.exit(1)

    return decompressed_data


def decompressDataFromFile(src_compressed_events_dir, dataset_name, file_name, settings, verbose=True):
    # --- Check the file path ---
    if not os.path.exists(src_compressed_events_dir + dataset_name + file_name) and verbose:
        # TODO: Exceptions
        print("Unable to find the specified compressed aedat file. Aborting...")
        sys.exit(1)

    # --- Load data from compressed aedat file ---
    start_time = time.time()
    if verbose:
        print("Loading " + file_name + " (compressed aedat file)")

    header, compressed_data = loadCompressedFile(src_compressed_events_dir + dataset_name + file_name)

    end_time = time.time()
    if verbose:
        print("Compressed file loaded in " + '{0:.3f}'.format(end_time - start_time) + " seconds")

    # --- Decompress data ---
    if verbose:
        print("Decompressing " + file_name + " with " + str(header.address_size) + "-byte addresses through " +
              header.compressor + " decompressor")
    start_time = time.time()

    decompressed_data = decompressData(compressed_data)

    bytes_per_spike = header.address_size + 4
    num_spikes = len(decompressed_data) / bytes_per_spike
    if not num_spikes.is_integer():
        print("Spikes are not a whole number. Something went wrong with the file " + file_name)
    else:
        num_spikes = int(num_spikes)

    # Convert addresses and timestamps from bytes to ints
    addresses = []
    timestamps = []

    for i in range(num_spikes):
        index = i * bytes_per_spike
        addresses.append(decompressed_data[index:(index + header.address_size)])
        timestamps.append(decompressed_data[(index + header.address_size):(index + bytes_per_spike)])

    addresses = [int.from_bytes(x, "big") for x in addresses]
    timestamps = [int.from_bytes(x, "big") for x in timestamps]

    # Return the new spikes file
    spikes_file = SpikesFile(addresses, timestamps)

    # Return the modified settings
    new_settings = copy.deepcopy(settings)
    new_settings.address_size = header.address_size
    # TODO: Modify settings to allow timestamp_size

    end_time = time.time()
    if verbose:
        print("Decompression achieved in " + '{0:.3f}'.format(end_time - start_time) + " seconds")

    return spikes_file, new_settings


def discardBytes(spikes_file, address_size, timestamp_size):
    raw_smallest_data = bytearray()
    addresses = spikes_file.addresses
    timestamps = spikes_file.timestamps

    for i in range(len(addresses) - 1):
        raw_smallest_data.extend(addresses[i].to_bytes(address_size, "big"))
        raw_smallest_data.extend(timestamps[i].to_bytes(timestamp_size, "big"))

    return raw_smallest_data
