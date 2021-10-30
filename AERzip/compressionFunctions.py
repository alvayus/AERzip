import copy
import os
import sys
import time

import lz4.frame
import zstandard
from pyNAVIS import *

from AERzip.CompressedFileHeader import CompressedFileHeader
# TODO: Documentation and history on v1.0.0
# TODO: Test files
from AERzip.conversionFunctions import bytesToSpikesFile, spikesFileToBytes, getBytesToDiscard


def compressDataFromFile(src_events_dir, dst_compressed_events_dir, dataset_name, file_name,
                         settings, compressor="ZSTD", store=True, ignore_overwriting=True, verbose=True):
    # --- Check the file ---
    if store and not ignore_overwriting:
        checkCompressedFileExists(dst_compressed_events_dir, dataset_name, file_name)

    # --- Load data from original aedat file ---
    start_time = time.time()
    if verbose:
        print("\nLoading " + "/" + dataset_name + "/" + file_name + " (original aedat file)")

    spikes_file = Loaders.loadAEDAT(src_events_dir + "/" + dataset_name + "/" + file_name, settings)

    end_time = time.time()
    if verbose:
        print("Original file loaded in " + '{0:.3f}'.format(end_time - start_time) + " seconds")

    # Get the bytes to be discarded
    address_size, timestamp_size = getBytesToDiscard(settings)

    if verbose:
        print("\nCompressing " + "/" + dataset_name + "/" + file_name + " with " + str(settings.address_size) +
              "-byte addresses and " + str(settings.timestamp_size) + "-byte timestamps into an aedat file with " +
              str(address_size) + "-byte addresses and " + str(timestamp_size) + "-byte timestamps through " +
              compressor + " compressor")
    start_time = time.time()

    # --- Compress the data ---
    compressed_file = spikesFileToCompressedFile(spikes_file, address_size, timestamp_size, compressor)

    # --- Store the data ---
    if store:
        storeCompressedFile(compressed_file, dst_compressed_events_dir, dataset_name, file_name)

    end_time = time.time()
    if verbose:
        print("Compression achieved in " + '{0:.3f}'.format(end_time - start_time) + " seconds")

    return compressed_file


def decompressDataFromFile(src_compressed_events_dir, dataset_name, file_name, settings, verbose=True):
    # --- Check the file path ---
    if not os.path.exists(src_compressed_events_dir + "/" + dataset_name + "/" + file_name):
        raise FileNotFoundError("Unable to find the specified compressed aedat file: "
                                + "/" + dataset_name + "/" + file_name)

    # --- Load data from compressed aedat file ---
    start_time = time.time()
    if verbose:
        print("\nLoading " + "/" + dataset_name + "/" + file_name + " (compressed aedat file)")

    header, compressed_data = loadCompressedFile(src_compressed_events_dir + "/" + dataset_name + "/" + file_name)

    end_time = time.time()
    if verbose:
        print("Compressed file loaded in " + '{0:.3f}'.format(end_time - start_time) + " seconds")

    # --- Decompress the data ---
    if verbose:
        print("\nDecompressing " + "/" + dataset_name + "/" + file_name + " with " + str(header.address_size) +
              "-byte addresses and " + str(header.timestamp_size) + "-byte timestamps through " +
              header.compressor + " decompressor")
    start_time = time.time()

    decompressed_data = decompressData(compressed_data, verbose=False)

    # Convert addresses and timestamps from bytes to ints
    spikes_file = bytesToSpikesFile(decompressed_data, header.address_size, header.timestamp_size)

    # Return the modified settings
    new_settings = copy.deepcopy(settings)
    new_settings.address_size = header.address_size
    new_settings.timestamp_size = header.timestamp_size

    end_time = time.time()
    if verbose:
        print("Decompression achieved in " + '{0:.3f}'.format(end_time - start_time) + " seconds")

    return spikes_file, new_settings


def compressData(spikes_bytes, compressor="ZSTD", verbose=True):
    start_time = time.time()

    if compressor == "ZSTD":
        cctx = zstandard.ZstdCompressor()
        compressed_data = cctx.compress(spikes_bytes)
    elif compressor == "LZ4":
        compressed_data = lz4.frame.compress(spikes_bytes)
    else:
        raise ValueError("Compressor not recognized")

    end_time = time.time()
    if verbose:
        print("-> Compressed data in " + '{0:.3f}'.format(end_time - start_time) + " seconds")

    return compressed_data


def decompressData(compressed_data, compressor="ZSTD", verbose=True):
    start_time = time.time()

    if compressor == "ZSTD":
        dctx = zstandard.ZstdDecompressor()
        decompressed_data = dctx.decompress(compressed_data)
    elif compressor == "LZ4":
        decompressed_data = lz4.frame.decompress(compressed_data)
    else:
        raise ValueError("Compressor not recognized")

    end_time = time.time()
    if verbose:
        print("-> Decompressed data in " + '{0:.3f}'.format(end_time - start_time) + " seconds")

    return decompressed_data


def storeCompressedFile(compressed_file, dst_compressed_events_dir, dataset_name,
                        file_name, ignore_overwriting=True):
    # Check the file
    if not ignore_overwriting:
        checkCompressedFileExists(dst_compressed_events_dir, dataset_name, file_name)

    # Check the destination folder
    if not os.path.exists(dst_compressed_events_dir + "/" + dataset_name + "/"):
        os.makedirs(dst_compressed_events_dir + "/" + dataset_name + "/")

    # Write the file
    file = open(dst_compressed_events_dir + "/" + dataset_name + "/" + file_name, "wb")
    file.write(compressed_file)
    file.close()


def loadCompressedFile(src_compressed_file_path):
    # Read all the file
    file = open(src_compressed_file_path, "rb")
    file_data = file.read()

    # Header extraction from the file
    header = CompressedFileHeader()

    start_index = 0
    end_index = header.library_version_length
    header.library_version = file_data[start_index:end_index].decode("utf-8").strip()

    start_index = end_index
    end_index = start_index + header.compressor_length
    header.compressor = file_data[start_index:end_index].decode("utf-8").strip()

    start_index = end_index
    end_index = start_index + header.address_length
    header.address_size = int.from_bytes(file_data[start_index:end_index], "big") + 1

    start_index = end_index
    end_index = start_index + header.timestamp_length
    header.timestamp_size = int.from_bytes(file_data[start_index:end_index], "big") + 1

    start_index = end_index + header.end_header_length
    compressed_data = file_data[start_index:]

    # Close the file
    file.close()

    return header, compressed_data


def bytesToCompressedFile(spikes_bytes, address_size=4, timestamp_size=4, compressor="ZSTD", verbose=True):
    start_time = time.time()
    if verbose:
        print("bytesToCompressedFile: Converting spikes bytes into a spikes compressed file...")

    # Compress the data
    compressed_data = compressData(spikes_bytes, compressor, verbose=False)

    # Join header with compressed data
    compressed_file = getCompressedFile(compressed_data, address_size, timestamp_size, compressor)

    end_time = time.time()
    if verbose:
        print("bytesToCompressedFile: Data compression has took " + '{0:.3f}'.format(
            end_time - start_time) + " seconds")

    return compressed_file


def spikesFileToCompressedFile(spikes_file, address_size=4, timestamp_size=4, compressor="ZSTD", verbose=True):
    # Convert to bytearray (needed to compress)
    spikes_bytes = spikesFileToBytes(spikes_file, address_size, timestamp_size)

    # Call to bytesToCompressedFile function
    compressed_file = bytesToCompressedFile(spikes_bytes, address_size, timestamp_size, compressor)

    if verbose:
        print("spikesFileToCompressedFile: SpikesFile converted into a bytearray and compressed")

    return compressed_file


def getCompressedFile(compressed_data, address_size=4, timestamp_size=4, compressor="ZSTD", verbose=False):
    start_time = time.time()

    # Create file with header
    compressed_file = CompressedFileHeader(compressor, address_size, timestamp_size).toBytes()

    # Extend file with data
    compressed_file.extend(compressed_data)

    end_time = time.time()
    if verbose:
        print("-> Compressed data attached to the header in " + '{0:.3f}'.format(end_time - start_time) + " seconds")

    return compressed_file


def checkCompressedFileExists(dst_compressed_events_dir, dataset_name, file_name):
    if os.path.exists(dst_compressed_events_dir + "/" + dataset_name + "/" + file_name):
        print("\nThe compressed aedat file associated with this aedat file already exists\n"
              "Do you want to overwrite it? Y/N")
        option = input()

        if option == "N":
            print("File compression for the file " + "/" + dataset_name + "/" + file_name + " has been cancelled")
            sys.exit(1)
