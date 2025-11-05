import os
import pickle
import struct
import time

import msgpack
import numpy as np

from AERzip.CompressedFileHeader import CompressedFileHeader


def saveCompressedFile(addresses, timestamps, file_path, max_address=None, max_timestamp=None, min_timestamp=None, ask=False, overwrite=False, verbose=False):
    """
    This function compresses and saves a compressed file from the provided addresses and timestamps.

    :param list addresses: A list containing the addresses of the spikes to be stored.
    :param list timestamps: A list containing the timestamps of the spikes to be stored
    :param string file_path: A string indicating where the file should be written.
    :param int max_address: An integer indicating the maximum address of the addresses list. Not required, but can speed up the compression.
    :param int max_timestamp: An integer indicating the maximum time stamp of the timestamps list. Not required, but can speed up the compression.
    :param int min_timestamp: An integer indicating the minimum time stamp of the timestamps list. Not required, but can speed up the compression.
    :param boolean ask: A boolean indicating whether or not to prompt the user to overwrite a file that has been found at the specified path.
    :param boolean overwrite: A boolean indicating wheter or not a file that has been found at the specified path must be or not be overwritten (if the user is not asked).
    :param boolean verbose: A boolean indicating whether or not to print information about the process.
    """
    if verbose:
        start_time = time.time()
        print("Compressing and storing...")

    # --- COMPRESS DATA ---
    # Checking expected sizes
    n_addresses = len(addresses)
    n_timestamps = len(timestamps)
    if n_addresses != n_timestamps:
        raise ValueError("The size of the address list must be equal to the size of the time stamp list.")
    
    # Converting addresses and time stamps numpy arrays    
    new_addresses = np.array(addresses, copy=False)
    new_timestamps = np.array(timestamps, copy=False)

    # Method 1) Reducing time stamps
    if min_timestamp is None:
        min_timestamp = np.min(timestamps)

    new_timestamps = new_timestamps - min_timestamp
    
    # Method 2) Grouping time stamps by address
    spikes = {}
    for address, timestamp_list in zip(new_addresses, new_timestamps):  # Note: spikes dictionary could be not sorted
        spikes.setdefault(address.item(), []).append(timestamp_list.item())

    # --- STORE DATA ---
    # Check the destination folder
    dst_path = file_path

    if not os.path.exists(os.path.dirname(file_path)):
        os.makedirs(os.path.dirname(file_path))
    else:
        # If the destination folder exists, check if the file exists
        if os.path.exists(dst_path):
            if ask:
                print("A file already exists in the specified path.\n"
                    "Do you want to overwrite it? Y/N\n")
                option = input()

                while option != "Y" and option != "N":
                    print("Unexpected value. Please, enter 'Y' (overwrite) or 'N' (no overwrite)\n")
                    option = input()
            else:
                if overwrite:
                    option = "Y"
                else:
                    option = "N"

            if option == "N":
                split_path = os.path.splitext(dst_path)
                i = 1

                while os.path.exists(dst_path):
                    dst_path = split_path[0] + "_" + str(i) + split_path[1]
                    i += 1

    # Calculating bytes required for addresses and timestamps
    if max_address is None:
        max_address = np.max(new_addresses)

    if max_address <= 0xFF:
        address_bytes = 1
    elif max_address <= 0xFFFF:
        address_bytes = 2
    elif max_address <= 0xFFFFFF:
        address_bytes = 3
    elif max_address <= 0xFFFFFFFF:
        address_bytes = 4
    elif max_address <= 0xFFFFFFFFFF:
        address_bytes = 5
    elif max_address <= 0xFFFFFFFFFFFF:
        address_bytes = 6
    elif max_address <= 0xFFFFFFFFFFFFFF:
        address_bytes = 7
    else:
        address_bytes = 8

    if max_timestamp is None:
        max_timestamp = np.max(new_timestamps)

    if max_timestamp <= 0xFF:
        timestamp_bytes = 1
    elif max_timestamp <= 0xFFFF:
        timestamp_bytes = 2
    elif max_timestamp <= 0xFFFFFF:
        timestamp_bytes = 3
    elif max_timestamp <= 0xFFFFFFFF:
        timestamp_bytes = 4
    elif max_timestamp <= 0xFFFFFFFFFF:
        timestamp_bytes = 5
    elif max_timestamp <= 0xFFFFFFFFFFFF:
        timestamp_bytes = 6
    elif max_timestamp <= 0xFFFFFFFFFFFFFF:
        timestamp_bytes = 7
    else:
        timestamp_bytes = 8

    # Save the file
    file = open(dst_path, "wb")

    header = CompressedFileHeader(address_size=address_bytes, timestamp_size=timestamp_bytes)
    file.write(header.toBytes())

    # Write pairs key-value
    delimiter = pow(2, 8 * timestamp_bytes) - 1  # Maximum value for time stamps
    for address, timestamp_list in spikes.items():
        # Write the address
        file.write(address.to_bytes(address_bytes, byteorder="little", signed=False))
        
        # Write the time stamps
        for timestamp in timestamp_list:
            file.write(timestamp.to_bytes(timestamp_bytes, byteorder="little", signed=False))
        
        # Write the delimiter
        # Note: Using timestamo_bytes bytes to represent the delimiter in order to simplify the reading process
        file.write(delimiter.to_bytes(timestamp_bytes, byteorder="little", signed=False))

    file.close()

    if verbose:
        end_time = time.time()
        print("Compressed file saved (took " + '{0:.3f}'.format(end_time - start_time) + " seconds)")

def loadCompressedFile(file_path, verbose=False):
    """
    This function loads a compressed file and returns the addresses and time stamps stored in it.

    :param string file_path: A string indicating the path of the compressed file to be loaded.
    :param boolean verbose: A boolean indicating whether or not to print information about the process.
    :return: A tuple containing two lists: the addresses and the time stamps stored in the compressed file.
    :rtype: tuple
    """
    if verbose:
        start_time = time.time()
        print("Loading the compressed file...")

    # Load the compressed file
    file = open(file_path, "rb")

    # Read header
    header = CompressedFileHeader()
    header.library_version = file.read(header.library_version_bytes).decode("utf-8").strip()
    header.compressor = file.read(header.compressor_bytes).decode("utf-8").strip()
    header.address_size = int.from_bytes(file.read(header.address_size_bytes), "little")
    header.timestamp_size = int.from_bytes(file.read(header.timestamp_size_bytes), "little")
    header.optional = file.read(header.optional_bytes)
    header.header_end = file.read(header.header_end_bytes).decode("utf-8").strip()

    # Read pairs key-value
    addresses = np.array([])
    timestamps = np.array([])

    delimiter = pow(2, 8 * header.timestamp_size) - 1  # Maximum value for time stamps

    # Read addresses and time stamps
    addresses = []
    timestamps = []

    while True:
        address_data = file.read(header.address_size)
        if not address_data:
            break

        if len(address_data) != header.address_size:
            raise EOFError("Unexpected end of file when reading address data.")
        
        address = int.from_bytes(address_data, byteorder="little", signed=False)

        # Read time stamps until the delimiter is found
        while True:
            timestamp_data = file.read(header.timestamp_size)
            if not timestamp_data or len(timestamp_data) != header.timestamp_size:
                raise EOFError("Unexpected end of file when reading timestamp data.")

            timestamp = int.from_bytes(timestamp_data, byteorder="little", signed=False)

            if timestamp == delimiter:
                break

            addresses.append(address)
            timestamps.append(timestamp)

    addresses = np.array(addresses, dtype=np.uint64)
    timestamps = np.array(timestamps, dtype=np.uint64)

    file.close()

    if verbose:
        end_time = time.time()
        print("Compressed file loaded (took " + '{0:.3f}'.format(end_time - start_time) + " seconds)")

    return addresses, timestamps