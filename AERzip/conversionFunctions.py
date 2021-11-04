import copy
import math
import time

import numpy as np
from pyNAVIS import SpikesFile


# TODO: Checked
def bytesToSpikesFile(bytes_data, settings, header, verbose=True):
    """
    Converts a bytearray of raw spikes of a-bytes addresses and b-bytes timestamps, where a and b are options.address_size
    and options.timestamp_size parameters respectively, to a SpikesFile of raw spikes of the same shape (or with 4-byte
    addresses or timestamps if a or b were encoded in 3 bytes).

    Parameters:
        bytes_data (bytearray): The input bytearray. It must contain raw spikes data (without headers).
        settings (MainSettings): A MainSettings object from pyNAVIS. It should contain information about the original file.
        header (CompressedFileHeader): A CompressedFileHeader object. It should contain information about the compressed file.
        verbose (boolean): A boolean indicating whether or not debug comments are printed.

    Returns:
        spikes_file (SpikesFile): The output SpikesFile object from pyNAVIS. It contains raw spikes shaped
        as the raw spikes of the input bytearray.

    Notes:
        This function is the inverse of the spikesFileToBytes function.

        With options.address_size or options.timestamp_size are 3 bytes it is needed to work differently due to
        NumPy doesn't support np.uint24 (or working with data types of 3 bytes). Doing it cost more time that
        viewing the arrays as np.uint8 (1 byte), np.uint16 (2 bytes) or np.uint32 (4 bytes). When processing
        3-byte addresses or timestamps, the returned SpikesFile will contain 4-byte addresses or timestamps.
    """
    start_time = time.time()
    if verbose:
        print("bytesToSpikesFile: Converting spikes bytes to SpikesFile")

    # This is needed to work with 3-byte addresses or timestamps
    if header.address_size == 3 or header.timestamp_size == 3:
        # Separate addresses and timestamps
        spikes_struct = constructStruct("addresses", (header.address_size,), "timestamps", (header.timestamp_size,))
        spikes = np.frombuffer(bytes_data, spikes_struct)

        # Fill addresses and timestamps with zeros to reach 4-bytes per element
        address_struct = constructStruct("zeros", (4 - header.address_size,), "addresses", (header.address_size,))
        timestamp_struct = constructStruct("zeros", (4 - header.timestamp_size,), "timestamps", (header.timestamp_size,))
        filled_addresses = np.zeros(len(spikes), dtype=address_struct)
        filled_timestamps = np.zeros(len(spikes), dtype=timestamp_struct)
        filled_addresses['addresses'] = spikes['addresses']
        filled_timestamps['timestamps'] = spikes['timestamps']

        # View these filled addresses and timestamps as 4-byte ints
        addresses = filled_addresses.view(">u4")
        timestamps = filled_timestamps.view(">u4")

    else:
        # Separate addresses and timestamps
        struct = np.dtype(">u" + str(header.address_size) + ", " + ">u" + str(header.timestamp_size))
        spikes = np.frombuffer(bytes_data, struct)
        addresses = spikes['f0']
        timestamps = spikes['f1']

    # Return the SpikesFile
    spikes_file = SpikesFile(addresses, timestamps)

    # Return the modified options
    new_settings = copy.deepcopy(settings)
    new_settings.address_size = header.address_size
    new_settings.timestamp_size = header.timestamp_size

    end_time = time.time()
    if verbose:
        print("bytesToSpikesFile: Data conversion has took " + '{0:.3f}'.format(
            end_time - start_time) + " seconds")

    return spikes_file, new_settings


# TODO: Checked
def spikesFileToBytes(spikes_file, options, new_address_size, new_timestamp_size, compressor=None, verbose=True):
    """
    Converts a SpikesFile of raw spikes of a-bytes addresses and b-bytes timestamps, where a and b are options.address_size
    and options.timestamp_size fields respectively, to a bytearray of raw spikes of 4-byte addresses and timestamps when
    not using LZMA compressor and a bytearray of raw spikes of the desired new_address_size and new_timestamp_size
    parameter sizes when using it.

    Parameters:
        spikes_file (SpikesFile): The input SpikesFile object from pyNAVIS. It must contain raw spikes data (without headers).
        options (MainSettings, CompressedFileHeader): A MainSettings object from pyNAVIS or CompressedFileHeader that contains information about the spikes_file.
        new_address_size (int): An int indicating the desired size of the addresses (calculated by getBytesToPrune).
        new_timestamp_size (int): An int indicating the desired size of the timestamps (calculated by getBytesToPrune).
        compressor (string): A string indicating the compressor to be used.
        verbose (boolean): A boolean indicating whether or not debug comments are printed.

    Returns:
        bytes_data (bytearray): The output bytearray. It contains raw spikes shaped as the raw spikes of the
        input SpikesFile.

    Notes:
        This function is the inverse of the bytesToSpikesFile function.

        When not using LZMA compressor, the returned bytearray will contain 4-byte addresses and timestamps.
        Otherwise, bytes will be pruned as expected (a-byte addresses and b-byte timestamps to c-byte addresses
        and d-byte timestamps, where c and d are the new_address_size and new_timestamp_size parameters respectively).

        If you want to use the LZMA compression, you need to specify the compressor parameter to prune the bytes.
        Otherwise it could take a long time to compress the data.
    """
    start_time = time.time()
    if verbose:
        print("spikesFileToBytes: Converting SpikesFile to spikes bytes")

    if compressor != "LZMA":
        # Viewing addresses and timestamps as 4-bytes data usually allows to achieve a better compression,
        # regardless of their original sizes
        param = ">u4"
        struct = np.dtype(param + ", " + param)

        bytes_data = np.zeros(len(spikes_file.addresses), dtype=struct)
        bytes_data['f0'] = spikes_file.addresses.astype(dtype=struct[0], copy=False)
        bytes_data['f1'] = spikes_file.timestamps.astype(dtype=struct[1], copy=False)
    else:
        # In the case of compressing with LZMA compressor, it is better to prune the bytes because
        # we can achieve practically the same compressed file size in a reasonably smaller time. This
        # pruning only happens when size parameters are greater than the original sizes of the addresses and timestamps
        org_address_size = options.address_size
        org_timestamp_size = options.timestamp_size

        if not options.address_size > new_address_size:
            org_address_size = new_address_size

        if not options.timestamp_size > new_timestamp_size:
            org_timestamp_size = new_timestamp_size

        address_struct = constructStruct("pruned", (org_address_size - new_address_size,), "not_pruned", (new_address_size,))
        timestamp_struct = constructStruct("pruned", (org_timestamp_size - new_timestamp_size,), "not_pruned", (new_timestamp_size,))
        spikes_struct = constructStruct("addresses", (new_address_size,), "timestamps", (new_timestamp_size,))

        addresses = np.array(spikes_file.addresses, copy=False).view(address_struct)
        timestamps = np.array(spikes_file.timestamps, copy=False).view(timestamp_struct)

        bytes_data = np.zeros(len(spikes_file.addresses), dtype=spikes_struct)
        bytes_data['addresses'] = addresses['not_pruned']
        bytes_data['timestamps'] = timestamps['not_pruned']

    # Return the spikes bytearray (pruned or not)
    bytes_data = bytes_data.tobytes()

    end_time = time.time()
    if verbose:
        print("spikesFileToBytes: Data conversion has took " + '{0:.3f}'.format(
            end_time - start_time) + " seconds")

    return bytes_data


# TODO: Checked
def getBytesToPrune(spikes_file, settings):
    """
    Gets the minimum number of bytes needed for spikes addresses and timestamps representation based on the input settings.

    Parameters:
        spikes_file (SpikesFile): The input SpikesFile object from pyNAVIS.
        settings (MainSettings): A MainSettings object from pyNAVIS.

    Returns:
        address_size (int): An int indicating the minimum number of bytes to represent the addresses.
        timestamp_size (int): An int indicating the minimum number of bytes to represent the timestamps.
    """
    # Addresses
    address_size = int(math.ceil(settings.num_channels * (settings.mono_stereo + 1) *
                                 (settings.on_off_both + 1) / 256))

    # Timestamps
    dec2bin = bin(spikes_file.max_ts)[2:]
    timestamp_size = int(math.ceil(len(dec2bin) / 8))

    return address_size, timestamp_size


# TODO: Checked
def constructStruct(first_field, first_field_size, second_field, second_file_size):
    """
    Constructs a numpy data type of two fields to represent the data structure of a bytearray.

    Parameters:
        first_field (string): A string indicating the name of the first field.
        first_field_size (int, tuple): An int or tuple indicating the number of bytes of the elements of the first field.
        second_field (string): A string indicating the name of the second field.
        second_file_size (int, tuple): An int or tuple indicating the number of bytes of the elements of the second field.

    Returns:
        struct (type): A data type required to interpret a bytearray.
    """

    struct = np.dtype([(first_field, ">u1", first_field_size), (second_field, ">u1", second_file_size)])

    return struct
