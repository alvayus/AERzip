import copy
import os
import time

import lz4.frame
import zstandard
from pyNAVIS import *

from AERzip.CompressedFileHeader import CompressedFileHeader
# TODO: Documentation and history on v1.0.0
# TODO: Test files
from AERzip.conversionFunctions import bytesToSpikesFile, spikesFileToBytes, getBytesToPrune


def compressDataFromFile(src_events_dir, dst_compressed_events_dir, dataset_name, file_name,
                         settings, compressor, store=True, ignore_overwriting=True, verbose=True):
    """
        Reads an original aedat file, extracts and compress its raw spikes data and returns a compressed file bytearray.

        Parameters:
            src_events_dir (string): A string indicating the original aedat files folder.
            dst_compressed_events_dir (string): A string indicating the compressed files folder.
            dataset_name (string): A string indicating the dataset name. It must exist inside the compressed files folder.
            file_name (string): A string indicating the file name. It must exist inside the dataset folder.
            settings (MainSettings): A MainSettings object from pyNAVIS.
            compressor (string): A string indicating the compressor to be used.
            verbose (boolean): A boolean indicating whether or not debug comments are printed.

        Returns:
            compressed_file (bytearray): The output bytearray. It contains the CompressedFileHeader bound to the compressed spikes data.
        """
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
    """
    Reads a file as a compressed file, decompress it to extract its raw spikes data and returns a SpikesFile object.

    Parameters:
        src_compressed_events_dir (string): A string indicating the compressed files folder.
        dataset_name (string): A string indicating the dataset name. It must exist inside the compressed files folder.
        file_name (string): A string indicating the file name. It must exist inside the dataset folder.
        settings (MainSettings): A MainSettings object from pyNAVIS.
        compressor (string): A string indicating the compressor to be used.
        verbose (boolean): A boolean indicating whether or not debug comments are printed.

    Returns:
        spikes_file (SpikesFile): The output SpikesFile object from pyNAVIS. It contains raw spikes.
        new_settings (MainSettings): A MainSettings object from pyNAVIS. It contains the CompressedFileHeader's address_size and timestamp_size fields.

    Notes:
        new_settings is returned in order to allow direct visualization of the files data using pyNAVIS plot functions.
    """
    # --- Load data from compressed aedat file ---
    start_time = time.time()
    if verbose:
        print("\nLoading " + "/" + dataset_name + "/" + file_name + " (compressed aedat file)")

    compressed_file = loadCompressedFile(src_compressed_events_dir, dataset_name, file_name)

    end_time = time.time()
    if verbose:
        print("Compressed file loaded in " + '{0:.3f}'.format(end_time - start_time) + " seconds")

    # --- Decompress the data ---
    if verbose:
        print("\nDecompressing " + "/" + dataset_name + "/" + file_name)
    start_time = time.time()

    # Call to bytesToSpikesFile function
    header, spikes_file = compressedFileToSpikesFile(compressed_file)

    # Return the modified settings
    new_settings = copy.deepcopy(settings)
    new_settings.address_size = header.address_size
    new_settings.timestamp_size = header.timestamp_size

    end_time = time.time()
    if verbose:
        print("Decompression achieved in " + '{0:.3f}'.format(end_time - start_time) + " seconds")

    return spikes_file, new_settings


def compressData(bytes_data, compressor, verbose=True):
    """
    Decompress the input compressed spikes bytearray via the specified compressor.

    Parameters:
        bytes_data (bytearray): The input bytearray. It must contain raw spikes data (without headers)
        compressor (string): A string indicating the compressor to be used.
        verbose (boolean): A boolean indicating whether or not debug comments are printed.

    Returns:
        compressed_data (bytearray): The output bytearray that contains the compressed spikes.
    """
    start_time = time.time()

    if compressor == "ZSTD":
        cctx = zstandard.ZstdCompressor()
        compressed_data = cctx.compress(bytes_data)
    elif compressor == "LZ4":
        compressed_data = lz4.frame.compress(bytes_data)
    else:
        raise ValueError("Compressor not recognized")

    end_time = time.time()
    if verbose:
        print("-> Compressed data in " + '{0:.3f}'.format(end_time - start_time) + " seconds")

    return compressed_data


def decompressData(compressed_data, compressor, verbose=False):
    """
    Decompress the input compressed spikes bytearray via the specified compressor.

    Parameters:
        compressed_data (bytearray): The input bytearray that contains the compressed spikes.
        compressor (string): A string indicating the compressor to be used.
        verbose (boolean): A boolean indicating whether or not debug comments are printed.

    Returns:
        decompressed_data (bytearray): The output bytearray. It contains raw spikes.
    """
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
    """
    Stores a compressed_file bytearray.

    Parameters:
        compressed_file (bytearray): The input bytearray that contains the CompressedFileHeader and the compressed spikes.
        dst_compressed_events_dir (string): A string indicating the compressed files folder.
        dataset_name (string): A string indicating the dataset name. It must exist inside the compressed files folder.
        file_name (string): A string indicating the file name. It must exist inside the dataset folder.
        ignore_overwriting (boolean): A boolean indicating whether or not ignore overwriting.

    Returns:
        None
    """
    # Check the file
    file_path = dst_compressed_events_dir + "/" + dataset_name + "/" + file_name
    if not ignore_overwriting:
        file_path = checkCompressedFileExists(file_path, dataset_name, file_name)

    # Check the destination folder
    if not os.path.exists(dst_compressed_events_dir + "/" + dataset_name + "/"):
        os.makedirs(dst_compressed_events_dir + "/" + dataset_name + "/")

    # Write the file
    file = open(file_path, "wb")
    file.write(compressed_file)
    file.close()


def loadCompressedFile(src_compressed_events_dir, dataset_name, file_name):
    """
    Extracts header and compressed data from a stored compressed file.

    Parameters:
        src_compressed_events_dir (string): A string indicating the compressed files folder.
        dataset_name (string): A string indicating the dataset name. It must exist inside the compressed files folder.
        file_name (string): A string indicating the file name. It must exist inside the dataset folder.

    Returns:
        compressed_file (bytearray): The output bytearray. It contains the CompressedFileHeader bound to the compressed spikes data.
    """
    # Check the file path
    file_path = src_compressed_events_dir + "/" + dataset_name + "/" + file_name
    if not os.path.exists(file_path):
        raise FileNotFoundError("Unable to find the specified compressed aedat file: "
                                + "/" + dataset_name + "/" + file_name)

    # Read all the file
    file = open(file_path, "rb")
    compressed_file = file.read()

    # Close the file
    file.close()

    return compressed_file


def bytesToCompressedFile(bytes_data, address_size, timestamp_size, compressor, verbose=True):
    """
    Converts a bytearray of raw spikes of a-bytes addresses and b-bytes timestamps, where a and b are address_size
    and timestamp_size parameters respectively, to a bytearray of CompressedFileHeader and compressed spikes
    (compressed via the specified compressor) of the same shape.

    Parameters:
        bytes_data (bytearray): The input bytearray. It must contain raw spikes data (without headers).
        address_size (int): An int indicating the size of the addresses.
        timestamp_size (int): An int indicating the size of the timestamps.
        compressor (string): A string indicating the compressor to be used.
        verbose (boolean): A boolean indicating whether or not debug comments are printed.

    Returns:
        compressed_file (bytearray): The output bytearray. It contains the CompressedFileHeader bound to the compressed
        spikes data.

    Notes:
        This function is the inverse of the compressedFileToBytes function.
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

    Parameters:
        compressed_file (bytearray): The input bytearray that contains the CompressedFileHeader and the compressed spikes.
        verbose (boolean): A boolean indicating whether or not debug comments are printed.

    Returns:
        bytes_data (bytearray): The output bytearray. It contains raw spikes shaped as the compressed spikes of the
        compressed file.

    Notes:
        This function is the inverse of the bytesToCompressedFile function.
    """
    # Call to compressedFileToSpikesFile function
    header, spikes_file = compressedFileToSpikesFile(compressed_file)

    # Call to spikesFileToBytes function
    bytes_data = spikesFileToBytes(spikes_file, header.address_size, header.timestamp_size)

    if verbose:
        print("compressedFileToBytes: Compressed file bytearray decompressed into a raw spikes bytearray")

    return bytes_data


def spikesFileToCompressedFile(spikes_file, address_size, timestamp_size, compressor, verbose=True):
    """
    Converts a SpikesFile of raw spikes of a-bytes addresses and b-bytes timestamps, where a and b are address_size
    and timestamp_size parameters respectively, to a bytearray of CompressedFileHeader and compressed spikes
    (compressed via the specified compressor) of the same shape.

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
    # Call to spikesFileToBytes function
    spikes_bytes = spikesFileToBytes(spikes_file, address_size, timestamp_size)

    # Call to bytesToCompressedFile function
    compressed_file = bytesToCompressedFile(spikes_bytes, address_size, timestamp_size, compressor)

    if verbose:
        print("Done! SpikesFile compressed into a compressed file bytearray")

    return compressed_file


def compressedFileToSpikesFile(compressed_file, verbose=False):
    """
    Converts a bytearray of CompressedFileHeader and compressed spikes of a-bytes addresses and b-bytes timestamps,
    where a and b are address_size and timestamp_size ints which are inside the bytearray, to a SpikesFile of raw spikes
    of the same shape.

    Parameters:
        compressed_file (bytearray): The input bytearray that contains the CompressedFileHeader and the compressed spikes.
        verbose (boolean): A boolean indicating whether or not debug comments are printed.

    Returns:
        spikes_file (SpikesFile): The output SpikesFile object from pyNAVIS. It contains raw spikes shaped
        as the compressed spikes of the input bytearray.

    Notes:
        This function is the inverse of the spikesFileToCompressedFile function.
    """
    # Extract the compressed spikes
    header, compressed_data = extractCompressedData(compressed_file)

    # Decompress the data
    decompressed_data = decompressData(compressed_data, header.compressor)

    # Call to bytesToSpikesFile function
    spikes_file = bytesToSpikesFile(decompressed_data, header.address_size, header.timestamp_size)

    if verbose:
        print("compressedFileToSpikesFile: Compressed file bytearray decompressed into a SpikesFile")

    return header, spikes_file


def extractCompressedData(compressed_file, verbose=False):
    """
    Extracts the CompressedFileHeader object and the compressed spikes from an input bytearray.

    Parameters:
        compressed_file (bytearray, bytes): The input bytearray (or bytes). It contains the CompressedFileHeader bound to the compressed spikes.
        verbose (boolean): A boolean indicating whether or not debug comments are printed.

    Returns:
        header (CompressedFileHeader): The output CompressedFileHeader object.
        compressed_data (bytearray): The output bytearray that contains the compressed spikes.
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


def getCompressedFile(compressed_data, address_size, timestamp_size, compressor, verbose=False):
    """
    Assembles the full compressed aedat file by joining the CompressedFileHeader object
    to the compressed spikes raw data.

    Parameters:
        compressed_data (bytearray): The input bytearray that contains the compressed spikes.
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
        dataset_name (string): A string indicating the dataset name. It must exist inside the compressed files folder.
        file_name (string): A string indicating the file name. It must exist inside the dataset folder.

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
