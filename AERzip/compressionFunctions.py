import copy
import os
import time

import lz4.frame
import pylzma
import zstandard
from pyNAVIS import *

from AERzip.CompressedFileHeader import CompressedFileHeader
from AERzip.conversionFunctions import bytesToSpikesFile, spikesFileToBytes, calcRequiredBytes


def compressDataFromFile(src_file_path, settings, compressor, store=True, ignore_overwriting=True, verbose=True):
    """
    Reads an original aedat file, extracts and compress its raw spikes data and returns a compressed file bytearray.

    Parameters:
        src_file_path (string): A string indicating the original aedat file path.
        settings (MainSettings): A MainSettings object from pyNAVIS.
        compressor (string): A string indicating the compressor to be used.
        store (boolean): A boolean indicating whether or not store the compressed file.
        ignore_overwriting (boolean): A boolean indicating whether or not ignore overwriting.
        verbose (boolean): A boolean indicating whether or not debug comments are printed.

    Returns:
        compressed_file (bytearray): The output bytearray. It contains the CompressedFileHeader bound to the compressed spikes data.
    """
    # TODO: Only for NAS? Because it uses MainSettings as parameter. This is a problem for compatibility
    # --- Check the file ---
    split_path = src_file_path.split("/")
    split_path[len(split_path) - 2] = split_path[len(split_path) - 2] + "_" + compressor
    split_path[len(split_path) - 3] = "compressedEvents"
    split_path[0] = split_path[0] + "\\"

    dst_file_path = os.path.join(*split_path)
    if store and not ignore_overwriting:
        dst_file_path = checkCompressedFileExists(dst_file_path)

    file = os.path.basename(src_file_path)
    dir_path = os.path.dirname(src_file_path)
    dataset = os.path.basename(dir_path)
    main_folder = os.path.basename(os.path.dirname(dir_path))

    # --- Load data from original aedat file ---
    start_time = time.time()
    if verbose:
        print("\nLoading " + "/" + main_folder + "/" + dataset + "/" + file + " (original aedat file)")

    spikes_file = Loaders.loadAEDAT(src_file_path, settings)

    # Adapt timestamps to allow timestamp compression
    if spikes_file.min_ts != 0:
        Functions.adapt_timestamps(spikes_file, settings)

    end_time = time.time()
    if verbose:
        print("Original file loaded in " + '{0:.3f}'.format(end_time - start_time) + " seconds")

    # Get the bytes to be discarded
    address_size, timestamp_size = calcRequiredBytes(spikes_file, settings)

    if verbose:
        print("\nCompressing " + "/" + main_folder + "/" + dataset + "/" + file + " with " + str(settings.address_size) +
              "-byte addresses and " + str(settings.timestamp_size) + "-byte timestamps via " +
              compressor + " compressor")
    start_time = time.time()

    # --- Compress the data ---
    compressed_file = spikesFileToCompressedFile(spikes_file, settings.address_size, settings.timestamp_size,
                                                 address_size, timestamp_size, compressor, verbose=verbose)

    # --- Store the data ---
    if store:
        storeCompressedFile(compressed_file, dst_file_path)

    end_time = time.time()
    if verbose:
        print("Compression achieved in " + '{0:.3f}'.format(end_time - start_time) + " seconds")

    return compressed_file, dst_file_path


def decompressDataFromFile(src_file_path, verbose=True):
    """
    Reads a file as a compressed file, decompress it to extract its raw spikes data and returns a SpikesFile object.

    :param string src_file_path: A string indicating the compressed aedat file path.
    :param boolean verbose: A boolean indicating whether or not debug comments are printed.

    Returns:
        spikes_file (SpikesFile): The output SpikesFile object from pyNAVIS. It contains raw spikes.
        new_settings (MainSettings): A MainSettings object from pyNAVIS. It contains the CompressedFileHeader's address_size and timestamp_size fields.

    Notes:
        new_settings is returned in order to allow direct visualization of the files data using pyNAVIS plot functions.
    """
    # --- Load data from compressed aedat file ---
    file = os.path.basename(src_file_path)
    dir_path = os.path.dirname(src_file_path)
    dataset = os.path.basename(dir_path)
    main_folder = os.path.basename(os.path.dirname(dir_path))

    start_time = time.time()
    if verbose:
        print("\nLoading " + "/" + main_folder + "/" + dataset + "/" + file + " (compressed aedat file)")

    compressed_file = loadCompressedFile(src_file_path)

    end_time = time.time()
    if verbose:
        print("Compressed file loaded in " + '{0:.3f}'.format(end_time - start_time) + " seconds")

    # --- Decompress the data ---
    if verbose:
        print("\nDecompressing " + "/" + main_folder + "/" + dataset + "/" + file)
    start_time = time.time()

    # Call to bytesToSpikesFile function
    header, spikes_file, new_settings = compressedFileToSpikesFile(compressed_file)

    end_time = time.time()
    if verbose:
        print("Decompression achieved in " + '{0:.3f}'.format(end_time - start_time) + " seconds")

    return spikes_file, new_settings


def compressData(bytes_data, compressor, verbose=True):
    """
    Compress the input data via the specified compressor.

    :param bytearray bytes_data: The input bytearray.
    :param string compressor: A string indicating the compressor to be used.
    :param boolean verbose: A boolean indicating whether or not debug comments are printed.

    :return bytearray compressed_data: The output bytearray (compressed data).
    """
    start_time = time.time()

    if compressor == "ZSTD":
        cctx = zstandard.ZstdCompressor()
        compressed_data = cctx.compress(bytes_data)
    elif compressor == "LZ4":
        compressed_data = lz4.frame.compress(bytes_data)
    elif compressor == "LZMA":
        compressed_data = pylzma.compress(bytes_data)
    else:
        raise ValueError("Compressor not recognized")

    end_time = time.time()
    if verbose:
        print("-> Compressed data in " + '{0:.3f}'.format(end_time - start_time) + " seconds")

    return compressed_data


def decompressData(compressed_data, compressor, verbose=False):
    """
    Decompress the input compressed data via the specified compressor.

    :param bytearray, bytes compressed_data: The input bytearray.
    :param string compressor: A string indicating the compressor to be used.
    :param boolean verbose: A boolean indicating whether or not debug comments are printed.

    :return bytearray decompressed_data: The output bytearray (decompressed data).
    """
    start_time = time.time()

    if compressor == "ZSTD":
        dctx = zstandard.ZstdDecompressor()
        decompressed_data = dctx.decompress(compressed_data)
    elif compressor == "LZ4":
        decompressed_data = lz4.frame.decompress(compressed_data)
    elif compressor == "LZMA":
        decompressed_data = pylzma.decompress(compressed_data)
    else:
        raise ValueError("Compressor not recognized")

    end_time = time.time()
    if verbose:
        print("-> Decompressed data in " + '{0:.3f}'.format(end_time - start_time) + " seconds")

    return decompressed_data


def storeCompressedFile(compressed_file, dst_compressed_file_path, ignore_overwriting=True):
    """
    Stores a compressed_file bytearray.

    Parameters:
        compressed_file (bytearray): The input bytearray that contains the CompressedFileHeader and the compressed spikes.
        dst_compressed_file_path (string): The input string that indicates where the file is intended to be written.
        ignore_overwriting (boolean): A boolean indicating whether or not ignore overwriting.

    Returns:
        None
    """
    # TODO: This function stores any file. Change documentation?
    # Check the file
    file_path = dst_compressed_file_path
    if not ignore_overwriting:
        file_path = checkCompressedFileExists(file_path)

    # Check the destination folder
    if not os.path.exists(os.path.dirname(file_path)):
        os.makedirs(os.path.dirname(file_path))

    # Write the file
    file = open(file_path, "wb")
    file.write(compressed_file)
    file.close()


def loadCompressedFile(src_file_path):
    """
    Extracts header and compressed data from a stored compressed file.

    :param string src_file_path: A string indicating the compressed aedat file path.

    :return bytearray compressed_file: The output bytearray. It contains the CompressedFileHeader bound to the compressed spikes data.
    """
    # TODO: This function reads any file. Change documentation?
    # Read all the file
    file = open(src_file_path, "rb")
    compressed_file = file.read()

    # Close the file
    file.close()

    return compressed_file


def bytesToCompressedFile(bytes_data, address_size, timestamp_size, compressor, verbose=True):
    """
    Converts a bytearray of raw spikes of a-bytes addresses and b-bytes timestamps, where a and b are address_size
    and timestamp_size parameters respectively, to a bytearray of CompressedFileHeader and compressed spikes
    (compressed via the specified compressor) of the same shape.

    This function is the inverse of the compressedFileToBytes function.

    :param bytearray bytes_data: The input bytearray. It must contain raw spikes data (without headers).
    :param int address_size: An int indicating the size of the addresses.
    :param int timestamp_size: An int indicating the size of the timestamps.
    :param string compressor: A string indicating the compressor to be used.
    :param boolean verbose: A boolean indicating whether or not debug comments are printed.

    :return bytearray compressed_file: The output bytearray. It contains the CompressedFileHeader bound to the compressed spikes data.
    """
    start_time = time.time()
    if verbose:
        print("bytesToCompressedFile: Converting spikes bytes into a spikes compressed file...")

    # Compress the data
    compressed_data = compressData(bytes_data, compressor, verbose=False)

    # Join header with compressed data
    compressed_file = getCompressedFile(compressed_data, address_size, timestamp_size, compressor)

    end_time = time.time()
    if verbose:
        print("bytesToCompressedFile: Data compression has took " + '{0:.3f}'.format(
            end_time - start_time) + " seconds")

    return compressed_file


def compressedFileToBytes(compressed_file, verbose=True):
    """
    Converts a bytearray of CompressedFileHeader and compressed spikes of a-bytes addresses and b-bytes timestamps,
    where a and b are address_size and timestamp_size ints which are inside the bytearray, to a bytearray of raw spikes
    of the same shape.

    This function is the inverse of the bytesToCompressedFile function.

    :param bytearray compressed_file: The input bytearray that contains the CompressedFileHeader and the compressed spikes.
    :param boolean verbose: A boolean indicating whether or not debug comments are printed.

    :return bytearray bytes_data: The output bytearray. It contains raw spikes shaped as the compressed spikes of the compressed file.
    """
    # Extract the compressed spikes
    header, compressed_data = extractCompressedData(compressed_file)

    # Decompress the data
    bytes_data = decompressData(compressed_data, header.compressor)

    if verbose:
        print("compressedFileToBytes: Compressed file bytearray decompressed into a raw spikes bytearray")

    return bytes_data, header


def spikesFileToCompressedFile(spikes_file, initial_address_size, initial_timestamp_size, desired_address_size,
                               desired_timestamp_size, compressor, verbose=True):
    """
    Converts a SpikesFile of raw spikes of a-bytes addresses and b-bytes timestamps, where a and b are address_size
    and timestamp_size parameters respectively, to a bytearray of CompressedFileHeader and compressed spikes
    (compressed via the specified compressor) of the same shape.

    This function is the inverse of the compressedFileToSpikesFile function.

    In the case of compressing with LZMA compressor, it is better to prune the bytes because we can achieve
    practically the same compressed file size in a reasonably smaller time. Otherwise, viewing addresses and
    timestamps as 4-bytes data usually allows to achieve a better compression, regardless of their original sizes.

    :param SpikesFile spikes_file: The input SpikesFile object from pyNAVIS. It must contain raw spikes data.
    :param int initial_address_size: An int indicating the size of the addresses in spikes_file.
    :param int initial_timestamp_size: An int indicating the size of the timestamps in spikes_file.
    :param int desired_address_size: An int indicating the size of the addresses.
    :param int desired_timestamp_size: An int indicating the size of the timestamps.
    :param string compressor: A string indicating the compressor to be used.
    :param boolean verbose: A boolean indicating whether or not debug comments are printed.

    :return bytearray compressed_file: The output bytearray. It contains the CompressedFileHeader bound to the compressed spikes data.
    """
    if compressor != "LZMA":
        if verbose:
            print("spikesFileToCompressedFile: Considering 4-byte addresses and timestamps before the compression "
                  "process when NOT using LZMA as the compression algorithm")
        final_address_size = 4
        final_timestamp_size = 4
    else:
        final_address_size = desired_address_size
        final_timestamp_size = desired_timestamp_size

    # Call to spikesFileToBytes function
    spikes_bytes = spikesFileToBytes(spikes_file, initial_address_size, initial_timestamp_size, final_address_size,
                                     final_timestamp_size, verbose=verbose)

    # Call to bytesToCompressedFile function
    compressed_file = bytesToCompressedFile(spikes_bytes, final_address_size, final_timestamp_size, compressor,
                                            verbose=verbose)

    if verbose:
        print("Done! SpikesFile compressed into a compressed file bytearray")

    return compressed_file


def compressedFileToSpikesFile(compressed_file, verbose=False):
    """
    Converts a bytearray of CompressedFileHeader and compressed spikes of a-bytes addresses and b-bytes timestamps,
    where a and b are address_size and timestamp_size ints which are inside the bytearray, to a SpikesFile of raw spikes
    of the same shape.

    This function is the inverse of the spikesFileToCompressedFile function.

    :param bytearray compressed_file: The input bytearray that contains the CompressedFileHeader and the compressed spikes.
    :param boolean verbose: A boolean indicating whether or not debug comments are printed.

    :return SpikesFile spikes_file: The output SpikesFile object from pyNAVIS.
    """
    # Call to compressedFileToBytes function
    bytes_data, header = compressedFileToBytes(compressed_file, verbose=verbose)

    # Call to bytesToSpikesFile function
    spikes_file, final_address_size, final_timestamp_size = bytesToSpikesFile(bytes_data, header.address_size,
                                                                              header.timestamp_size, verbose=verbose)

    if verbose:
        print("compressedFileToSpikesFile: Compressed file bytearray decompressed into a SpikesFile")

    return header, spikes_file, final_address_size, final_timestamp_size


def extractCompressedData(compressed_file, verbose=False):
    """
    Extracts the CompressedFileHeader object and the compressed spikes from an input bytearray.

    :param bytearray, bytes compressed_file: The input bytearray (or bytes). It contains the CompressedFileHeader bound to the compressed spikes.
    :param boolean verbose: A boolean indicating whether or not debug comments are printed.

    :return:
    - header (CompressedFileHeader): The output CompressedFileHeader object.
    - compressed_data (bytearray): The output bytearray that contains the compressed spikes.
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
    end_index = start_index + header.address_size_length
    header.address_size = int.from_bytes(compressed_file[start_index:end_index], "big")

    start_index = end_index
    end_index = start_index + header.timestamp_size_length
    header.timestamp_size = int.from_bytes(compressed_file[start_index:end_index], "big")

    start_index = end_index
    end_index = start_index + header.optional_length
    header.optional = compressed_file[start_index:end_index]

    start_index = end_index
    end_index = start_index + header.header_end_length
    header.header_end = compressed_file[start_index:end_index].decode("utf-8")

    start_index = end_index
    compressed_data = bytes(compressed_file[start_index:])

    end_time = time.time()
    if verbose:
        print("-> Extracted data in " + '{0:.3f}'.format(end_time - start_time) + " seconds")

    return header, compressed_data


def getCompressedFile(compressed_data, address_size, timestamp_size, compressor, verbose=False):
    """
    Assembles the full compressed aedat file by joining the CompressedFileHeader object
    to the compressed spikes data.

    :param bytearray compressed_data: The input bytearray that contains the compressed spikes.
    :param int address_size: An int indicating the size of the addresses.
    :param int timestamp_size: An int indicating the size of the timestamps.
    :param string compressor: A string indicating the compressor to be used.
    :param boolean verbose: A boolean indicating whether or not debug comments are printed.

    :return bytearray compressed_file: The output bytearray. It contains the CompressedFileHeader bound to the compressed spikes data.
    """
    # TODO: Change parameters by a CompressedFileHeader object?
    start_time = time.time()

    # Create file with header
    compressed_file = CompressedFileHeader(compressor, address_size, timestamp_size).toBytes()

    # Extend file with data
    compressed_file.extend(compressed_data)

    end_time = time.time()
    if verbose:
        print("-> Compressed data attached to the header in " + '{0:.3f}'.format(end_time - start_time) + " seconds")

    return compressed_file


def checkCompressedFileExists(dst_compressed_file_path):
    """
    Checks if a compressed file already exits in the specified path. If it does, this function allows the user to
    decide whether to overwrite it or not. If the user decides not to overwrite the file, a new file path
    is generated to write the file to.

    :param string dst_compressed_file_path: The input string that indicates where the file is intended to be written.

    :return string file_path: The output string that indicates where the file will be finally written.
    """
    file_path = dst_compressed_file_path

    if os.path.exists(file_path):
        print("\nThe compressed aedat file already exists\n"
              "Do you want to overwrite it? Y/N")
        option = input()

        if option == "N":
            cut_ext = os.path.splitext(file_path)

            i = 1
            while os.path.exists(cut_ext[0] + " (" + str(i) + ")" + cut_ext[1]):
                i += 1

            file_path = cut_ext[0] + " (" + str(i) + ")" + cut_ext[1]

    return file_path
