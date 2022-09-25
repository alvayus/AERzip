import copy
import os
import time

import lz4.frame
import pylzma
import zstandard
from pyNAVIS import *

from AERzip.CompressedFileHeader import CompressedFileHeader
from AERzip.conversionFunctions import bytesToSpikesFile, spikesFileToBytes, calcRequiredBytes

# TODO: Related to compressDataFromStoredNASFile function
# But how to load a generic aedat file
'''def compressDataFromStoredFile(file_path, address_size, timestamp_size, compressor, store=True, verbose=True):
    pass'''


def compressDataFromStoredNASFile(initial_file_path, settings, compressor, store=True, ask_user=False, overwrite=False,
                                  verbose=True):
    """
    Reads an original aedat NAS file, extracts and compress its raw spikes data and returns a compressed file bytearray.
    This function cannot be used with files not associated with the NAS.

    :param string initial_file_path: A string indicating the original aedat file path.
    :param MainSettings settings: A MainSettings object from pyNAVIS containing information about the file.
    :param string compressor: A string indicating the compressor to be used.
    :param boolean store: A boolean indicating whether or not store the compressed file.
    :param boolean ask_user: A boolean indicating whether or not to prompt the user to overwrite a file that has been found at the specified path.
    :param boolean overwrite: A boolean indicating wheter or not a file that has been found at the specified path must be or not be overwritten.
    :param boolean verbose: A boolean indicating whether or not debug comments are printed.

    :return: The output bytearray. It contains the CompressedFileHeader bound to the compressed spikes data.
    :rtype: bytearray
    """
    file_name = os.path.basename(initial_file_path)
    dir_name = os.path.dirname(initial_file_path)
    dataset_name = os.path.basename(dir_name)
    main_folder = os.path.basename(os.path.dirname(dir_name))
    final_file_path = initial_file_path

    # --- If the final compress file should be stored, check the path ---
    if store:
        split_path = initial_file_path.split("/")
        split_path[len(split_path) - 2] = split_path[len(split_path) - 2] + "_" + compressor
        split_path[len(split_path) - 3] = "compressedEvents"
        split_path[0] = split_path[0] + "\\"
        final_file_path = checkFileExists(os.path.join(*split_path))

    # --- Load data from original aedat file ---
    start_time = time.time()
    if verbose:
        print("\nLoading " + "/" + main_folder + "/" + dataset_name + "/" + file_name + " (original aedat file)")

    spikes_file = Loaders.loadAEDAT(initial_file_path, settings)

    # Adapt timestamps to allow timestamp compression
    if spikes_file.min_ts != 0:
        Functions.adapt_timestamps(spikes_file, settings)

    end_time = time.time()
    if verbose:
        print("Original file loaded in " + '{0:.3f}'.format(end_time - start_time) + " seconds")

    # Get the bytes to be discarded
    desired_address_size, desired_timestamp_size = calcRequiredBytes(spikes_file, settings)

    if verbose:
        print("\nCompressing " + "/" + main_folder + "/" + dataset_name + "/" + file_name + " with " +
              str(settings.address_size) + "-byte addresses and " + str(settings.timestamp_size) +
              "-byte timestamps via " + compressor + " compressor")
    start_time = time.time()

    # --- Compress the data ---
    compressed_file = spikesFileToCompressedFile(spikes_file, settings.address_size, settings.timestamp_size,
                                                 desired_address_size, desired_timestamp_size, compressor,
                                                 verbose=verbose)

    # --- Store the data ---
    if store:
        storeFile(compressed_file, final_file_path, ask_user=ask_user, overwrite=overwrite)

    end_time = time.time()
    if verbose:
        print("Compression achieved in " + '{0:.3f}'.format(end_time - start_time) + " seconds")

    return compressed_file, final_file_path


def extractDataFromCompressedFile(file_path, verbose=True):
    """
    Reads a compressed aedat file and extracts and decompress its compressed information.

    :param string file_path: A string indicating the compressed aedat file path.
    :param boolean verbose: A boolean indicating whether or not debug comments are printed.

    :return: This function returns two different objects, listed below:
    - spikes_file (SpikesFile): The output SpikesFile object from pyNAVIS. It contains raw spikes.
    - new_settings (MainSettings): A MainSettings object from pyNAVIS. It contains the CompressedFileHeader's address_size and timestamp_size fields.
    """
    # --- Load data from compressed aedat file ---
    file = os.path.basename(file_path)
    dir_path = os.path.dirname(file_path)
    dataset = os.path.basename(dir_path)
    main_folder = os.path.basename(os.path.dirname(dir_path))

    start_time = time.time()
    if verbose:
        print("\nLoading " + "/" + main_folder + "/" + dataset + "/" + file + " (compressed aedat file)")

    compressed_file = loadFile(file_path)

    end_time = time.time()
    if verbose:
        print("Compressed file loaded in " + '{0:.3f}'.format(end_time - start_time) + " seconds")

    # --- Decompress the data ---
    if verbose:
        print("\nDecompressing " + "/" + main_folder + "/" + dataset + "/" + file)
    start_time = time.time()

    # Call to bytesToSpikesFile function
    header, spikes_file, final_address_size, final_timestamp_size = compressedFileToSpikesFile(compressed_file, verbose=verbose)

    end_time = time.time()
    if verbose:
        print("Decompression achieved in " + '{0:.3f}'.format(end_time - start_time) + " seconds")

    return header, spikes_file, final_address_size, final_timestamp_size


def bytesToCompressedFile(bytes_data, header, verbose=True):
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

    :return: The output bytearray. It contains the CompressedFileHeader bound to the compressed spikes data.
    :rtype: bytearray
    """
    start_time = time.time()
    if verbose:
        print("bytesToCompressedFile: Converting spikes bytes into a spikes compressed file...")

    # Join header with compressed data
    compressed_file = getCompressedFile(header, bytes_data)

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

    :return: The output bytearray. It contains raw spikes shaped as the compressed spikes of the compressed file.
    :rtype: bytearray
    """
    # Extract the compressed spikes
    header, compressed_data = extractCompressedData(compressed_file)

    # Decompress the data
    decompressed_data = decompressData(compressed_data, header.compressor)

    if verbose:
        print("compressedFileToBytes: Compressed file bytearray decompressed into a raw spikes bytearray")

    return decompressed_data, header


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

    :return: The output bytearray. It contains the CompressedFileHeader bound to the compressed spikes data.
    :rtype: bytearray
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

    # Create the header of the compressed file
    header = CompressedFileHeader(compressor, final_address_size, final_timestamp_size)

    # Call to bytesToCompressedFile function
    compressed_file = bytesToCompressedFile(spikes_bytes, header, verbose=verbose)

    if verbose:
        print("Done! SpikesFile compressed into a compressed file bytearray")

    return compressed_file


def compressedFileToSpikesFile(compressed_file, verbose=False):
    """
    Converts a bytearray of CompressedFileHeader and compressed spikes of a-bytes addresses and b-bytes timestamps,
    where a and b are address_size and timestamp_size ints which are inside the bytearray, to a SpikesFile of raw spikes
    of the same shape.

    This function is the inverse of the spikesFileToCompressedFile function.

    :param bytearray, bytes compressed_file: The input bytearray that contains the CompressedFileHeader and the compressed spikes.
    :param boolean verbose: A boolean indicating whether or not debug comments are printed.

    :return: The output SpikesFile object from pyNAVIS.
    :rtype: SpikesFile
    """
    # Call to compressedFileToBytes function
    data, header = compressedFileToBytes(compressed_file, verbose=verbose)

    # Call to bytesToSpikesFile function
    spikes_file, final_address_size, final_timestamp_size = bytesToSpikesFile(data, header.address_size,
                                                                              header.timestamp_size, verbose=verbose)

    if verbose:
        print("compressedFileToSpikesFile: Compressed file bytearray decompressed into a SpikesFile")

    return header, spikes_file, final_address_size, final_timestamp_size


def extractCompressedData(compressed_file, verbose=False):
    """
    Extracts the CompressedFileHeader object and the compressed spikes from an input bytearray.

    :param bytearray, bytes compressed_file: The input bytearray (or bytes). It contains the CompressedFileHeader bound to the compressed spikes.
    :param boolean verbose: A boolean indicating whether or not debug comments are printed.

    :return: This function returns two different objects, listed below:
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


def compressData(data, compressor, verbose=True):
    """
    Compress the input data via the specified compressor.

    :param bytearray, bytes data: The input data.
    :param string compressor: A string indicating the compressor to be used.
    :param boolean verbose: A boolean indicating whether or not debug comments are printed.

    :return: The output data (compressed data).
    :rtype: bytearray
    """
    start_time = time.time()

    if compressor == "ZSTD":
        cctx = zstandard.ZstdCompressor()
        compressed_data = cctx.compress(data)
    elif compressor == "LZ4":
        compressed_data = lz4.frame.compress(data)
    elif compressor == "LZMA":
        compressed_data = pylzma.compress(data)
    else:
        raise ValueError("Compressor not recognized")

    end_time = time.time()
    if verbose:
        print("-> Compressed data in " + '{0:.3f}'.format(end_time - start_time) + " seconds")

    return compressed_data


def decompressData(compressed_data, compressor, verbose=False):
    """
    Decompress the input compressed data via the specified compressor.

    :param bytearray, bytes compressed_data: The input data.
    :param string compressor: A string indicating the compressor to be used.
    :param boolean verbose: A boolean indicating whether or not debug comments are printed.

    :return: The output data (decompressed data).
    :rtype: bytearray
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


def getCompressedFile(header, data, verbose=False):
    """
    Assembles the full compressed aedat file by joining the CompressedFileHeader object to the compressed spikes data.

    :param CompressedFileHeader header: The header to attach to the compressed file.
    :param bytearray, bytes data: The input bytearray containing data to be compressed.
    :param boolean verbose: A boolean indicating whether or not debug comments are printed.

    :return: The output bytearray. It contains the CompressedFileHeader bound to the compressed spikes data.
    :rtype: bytearray
    """
    start_time = time.time()

    # Create file with header
    compressed_file = header.toBytes()

    # Compress data and extend the compressed file with it
    compressed_data = compressData(data, header.compressor, verbose=False)
    compressed_file.extend(compressed_data)

    end_time = time.time()
    if verbose:
        print("-> Compressed data attached to the header in " + '{0:.3f}'.format(end_time - start_time) + " seconds")

    return compressed_file


def storeFile(file_bytes, initial_file_path, ask_user=False, overwrite=False):
    """
    Stores a file.

    :param bytearray file_bytes: The input bytearray.
    :param string initial_file_path: A string indicating where the file is intended to be written.
    :param boolean ask_user: A boolean indicating whether or not to prompt the user to overwrite a file that has been found at the specified path.
    :param boolean overwrite: A boolean indicating wheter or not a file that has been found at the specified path must be or not be overwritten.
    """
    # Check the file
    final_file_path = checkFileExists(initial_file_path, ask_user=ask_user, overwrite=overwrite)

    # Check the destination folder
    if not os.path.exists(os.path.dirname(final_file_path)):
        os.makedirs(os.path.dirname(final_file_path))

    # Write the file
    file = open(final_file_path, "wb")
    file.write(file_bytes)
    file.close()


def checkFileExists(initial_file_path, ask_user=False, overwrite=False):
    """
    Checks if a file already exits in the specified path. If it does, this function allows the user to decide whether to
    overwrite it or not. If the user decides not to overwrite the file, a new file path is generated to write the file
    to.

    :param string initial_file_path: The input string indicating where the file is intended to be written.
    :param boolean ask_user: A boolean indicating whether or not to prompt the user to overwrite a file that has been found at the specified path.
    :param boolean overwrite: A boolean indicating wheter or not a file that has been found at the specified path must be or not be overwritten.

    :return: The output string indicating where the file will be finally written.
    :rtype: string
    """
    final_file_path = initial_file_path

    if os.path.exists(final_file_path):
        if ask_user:
            print("\nA file already exists in the specified path.\n"
                  "Do you want to overwrite it? Y/N")
            option = input()

            while option != "Y" and option != "N":
                print("\nUnexpected value. Please, enter 'Y' (overwrite) or 'N' (no overwrite)")
                option = input()
        else:
            if overwrite:
                option = "Y"
            else:
                option = "N"

        if option == "N":
            cut_ext = os.path.splitext(final_file_path)
            check_path = initial_file_path

            i = 1
            while os.path.exists(check_path):
                check_path = cut_ext[0] + "(" + str(i) + ")" + cut_ext[1]
                i += 1

            final_file_path = check_path

    return final_file_path


def loadFile(file_path):
    """
    Loads a file.

    :param string file_path: A string indicating the file path.

    :return: The output bytearray.
    :rtype: bytearray
    """
    # Read all the file
    file = open(file_path, "rb")
    file_bytes = file.read()

    # Close the file
    file.close()

    return file_bytes
