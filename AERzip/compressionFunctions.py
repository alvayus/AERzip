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
from AERzip.conversionFunctions import bytesToSpikesFile, spikesFileToBytes, getBytesToPrune


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
    address_size, timestamp_size = getBytesToPrune(settings)

    if verbose:
        print("\nCompressing " + "/" + dataset_name + "/" + file_name + " with " + str(settings.address_size) +
              "-byte addresses and " + str(settings.timestamp_size) + "-byte timestamps into an aedat file with " +
              str(address_size) + "-byte addresses and " + str(timestamp_size) + "-byte timestamps via " +
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


def decompressDataFromFile(src_compressed_events_dir, dataset_name, file_name, settings, compressor, verbose=True):
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
              "-byte addresses and " + str(header.timestamp_size) + "-byte timestamps via " +
              header.compressor + " decompressor")
    start_time = time.time()

    decompressed_data = decompressData(compressed_data, compressor, verbose=False)

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


def compressData(spikes_bytes, compressor, verbose=True):
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


def decompressData(compressed_data, compressor, verbose=True):
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
    compressed_file = file.read()

    # Extract compressed data
    header, compressed_data = extractCompressedData(compressed_file)

    # Close the file
    file.close()

    return header, compressed_data


def bytesToCompressedFile(spikes_bytes, address_size, timestamp_size, compressor="ZSTD", verbose=True):
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


def spikesFileToCompressedFile(spikes_file, address_size, timestamp_size, compressor="ZSTD", verbose=True):
    """
    Converts a SpikesFile of raw spikes of a-bytes addresses and b-bytes timestamps to a bytearray of CompressedFileHeader
    and compressed spikes (compressed via the specified compressor) of the same shape.

    Parameters:
        spikes_file (SpikesFile): The input SpikesFile object from pyNAVIS. It must contain raw spikes data (without headers).
        address_size (int): An int indicating the size of the addresses.
        timestamp_size (int): An int indicating the size of the timestamps.
        compressor (string): A string indicating the compressor to be used.
        verbose (boolean): A boolean indicating whether or not debug comments are printed.

    Returns:
        compressed_file (bytearray): The output bytearray. It contains the CompressedFileHeader bound to the compressed
        spikes data.

    Notes:
        This function is the inverse of the compressedFileToSpikesFile function.
    """
    # Convert to bytearray (needed to compress)
    spikes_bytes = spikesFileToBytes(spikes_file, address_size, timestamp_size)

    # Call to bytesToCompressedFile function
    compressed_file = bytesToCompressedFile(spikes_bytes, address_size, timestamp_size, compressor)

    if verbose:
        print("spikesFileToCompressedFile: SpikesFile compressed into a compressed file bytearray")

    return compressed_file


def compressedFileToSpikesFile(compressed_file, verbose=False):
    """
    Converts a bytearray of CompressedFileHeader and compressed spikes of a-bytes addresses and b-bytes timestamps,
    where a and b are address_size and timestamp_size ints which are inside the bytearray, to a SpikesFile of raw spikes
    of the same shape.

    Parameters:
        compressed_file (bytearray): The input bytearray that contains the CompressedFileHeader and the compressed spikes data.
        verbose (boolean): A boolean indicating whether or not debug comments are printed.

    Returns:
        spikes_file (SpikesFile): The output SpikesFile object from pyNAVIS. It contains raw spikes shaped
        as the compressed spikes of the input bytearray.

    Notes:
        This function is the inverse of the spikesFileToCompressedFile function.
    """
    # Extract the compressed spikes data
    header, compressed_data = extractCompressedData(compressed_file)

    # Decompress the data
    decompressed_data = decompressData(compressed_data, header.compressor)

    # Return the SpikesFile
    spikes_file = bytesToSpikesFile(decompressed_data, header.address_size, header.timestamp_size)

    if verbose:
        print("compressedFileToSpikesFile: Compressed file bytearray decompressed into a SpikesFile")

    return spikes_file


def extractCompressedData(compressed_file, verbose=False):
    """
    Extracts the CompressedFileHeader object and the compressed spikes data from an input bytearray.

    Parameters:
        compressed_file (bytearray, bytes): The input bytearray (or bytes). It contains the CompressedFileHeader bound to the compressed spikes data.
        verbose (boolean): A boolean indicating whether or not debug comments are printed.

    Returns:
        header (CompressedFileHeader): The output CompressedFileHeader object.
        compressed_data (bytearray): The output bytearray that contains the compressed spikes data.
    """
    start_time = time.time()

    # Create a new CompressedFileHeader
    header = CompressedFileHeader()

    # Separate header and compressed data
    start_index = 0
    end_index = header.library_version_length
    header.library_version = compressed_file[start_index:end_index].decode("utf-8").strip()

    start_index = end_index
    end_index = start_index + header.compressor_length
    header.compressor = compressed_file[start_index:end_index].decode("utf-8").strip()

    start_index = end_index
    end_index = start_index + header.address_length
    header.address_size = int.from_bytes(compressed_file[start_index:end_index], "big") + 1

    start_index = end_index
    end_index = start_index + header.timestamp_length
    header.timestamp_size = int.from_bytes(compressed_file[start_index:end_index], "big") + 1

    start_index = end_index + header.end_header_length
    compressed_data = compressed_file[start_index:]

    end_time = time.time()
    if verbose:
        print("-> Extracted data in " + '{0:.3f}'.format(end_time - start_time) + " seconds")

    return header, compressed_data


def getCompressedFile(compressed_data, address_size=4, timestamp_size=4, compressor="ZSTD", verbose=False):
    """
    Assembles the full compressed aedat file by joining the CompressedFileHeader object
    to the compressed spikes raw data.

    Parameters:
        compressed_data (bytearray): The input bytearray that contains the compressed spikes data.
        address_size (int): An int indicating the size of the addresses.
        timestamp_size (int): An int indicating the size of the timestamps.
        compressor (string): A string indicating the compressor to be used.
        verbose (boolean): A boolean indicating whether or not debug comments are printed.

    Returns:
        compressed_file (bytearray): The output bytearray. It contains the CompressedFileHeader bound to the compressed
        spikes data.
    """
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
    """
    Checks if the specified compressed file exists. If it does, this function allows the user to
    decide whether to overwrite it or not. If the user decides not to overwrite the file, a new file path
    is generated to write the file to.

    Parameters:
        dst_compressed_events_dir (string): A string indicating the compressed files folder.
        dataset_name (string): A string indicating the dataset name. It must exists inside the compressed files folder.
        file_name (string): A string indicating the file name. It must exists inside the dataset folder.

    Returns:
        file_path (string): The output string that indicates where to write the file
    """
    file_path = dst_compressed_events_dir + "/" + dataset_name + "/" + file_name

    if os.path.exists(file_path):
        print("\nThe compressed aedat file already exists\n"
              "Do you want to overwrite it? Y/N")
        option = input()

        if option == "N":
            cut_file_name = file_name.replace(".aedat", "")

            i = 1
            while os.path.exists(
                    dst_compressed_events_dir + "/" + dataset_name + "/" + cut_file_name + " (" + str(i) + ").aedat"):
                i += 1

            file_path = dst_compressed_events_dir + "/" + dataset_name + "/" + cut_file_name + " (" + str(
                i) + ").aedat "

    return file_path
