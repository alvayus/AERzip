import math
import time

import numpy as np
from pyNAVIS import SpikesFile


def pruneBytesToSpikesBytearray(bytes_data, settings, new_address_size,
                                new_timestamp_size, verbose=True):
    """
    Converts a bytearray of raw spikes of a-bytes addresses and b-bytes timestamps
    to a bytearray of raw spikes of c-bytes addresses and d-bytes timestamps, where
    a is settings.address_size field, b is settings.timestamp_size field and
    c and d are the new sizes input parameters (the desired sizes).

    Parameters:
        bytes_data (bytearray): The input bytearray. It must contain raw spikes data (without headers).
        settings (MainSettings): A MainSettings object from pyNAVIS. It must contain the address_size and timestamp_size fields.
        new_address_size (int): An int indicating the desired size of the addresses.
        new_timestamp_size (int): An int indicating the desired size of the timestamps.
        verbose (boolean): A boolean indicating whether or not debug comments are printed.

    Returns:
        pruned_bytes (bytearray): The output bytearray. It contains raw spikes shaped as desired.

    Notes:
        If a and b are equal to c and d respectively, output bytearray spikes will be of the same shape that input bytearray spikes.
    """
    start_time = time.time()
    if verbose:
        print("pruneBytesToSpikesBytearray: Converting bytes of spikes"
              "with " + str(settings.timestamp_size) + "-bytes addresses and " +
              str(settings.timestamp_size) + "-bytes timestamps to bytes of spikes with " +
              str(new_address_size) + "-bytes addresses and " + str(new_timestamp_size) +
              "-bytes timestamps")

    # Read addresses and timestamps (with original aedat file sizes)
    struct = constructStruct(settings.address_size, settings.timestamp_size)

    spikes = np.frombuffer(bytes_data, struct)

    # Convert address and timestamp sizes (with desired sizes)
    struct = constructStruct(new_address_size, new_timestamp_size)

    # Return the pruned bytearray
    pruned_bytes = spikes.astype(dtype=struct, copy=False)

    end_time = time.time()
    if verbose:
        print("pruneBytesToSpikesBytearray: Data conversion has took " + '{0:.3f}'.format(
            end_time - start_time) + " seconds")

    return pruned_bytes


def pruneBytesToSpikesFile(bytes_data, settings, new_address_size, new_timestamp_size, verbose=True):
    """
    Converts a bytearray of raw spikes of a-bytes addresses and b-bytes timestamps
    to a SpikesFile of raw spikes of c-bytes addresses and d-bytes timestamps, where
    a is settings.address_size field, b is settings.timestamp_size field and
    c and d are the new sizes input parameters (the desired sizes).

    Parameters:
        bytes_data (bytearray): The input bytearray. It must contain raw spikes data (without headers).
        settings (MainSettings): A MainSettings object from pyNAVIS. It must contain the address_size and timestamp_size fields.
        new_address_size (int): An int indicating the desired size of the addresses.
        new_timestamp_size (int): An int indicating the desired size of the timestamps.
        verbose (boolean): A boolean indicating whether or not debug comments are printed.

    Returns:
        spikes_file (SpikesFile): The output SpikesFile object from pyNAVIS. It contains raw spikes shaped
        as desired.

    Notes:
        If a and b are equal to c and d respectively, output SpikesFile spikes will be of the same shape that
        input bytearray spikes.
    """
    # Call to pruneBytesToSpikesBytearray function
    pruned_bytes = pruneBytesToSpikesBytearray(bytes_data, settings,
                                               new_address_size, new_timestamp_size)

    # Extracting addresses and timestamps from bytearray
    addresses = pruned_bytes['f0']
    timestamps = pruned_bytes['f1']

    # Return the SpikesFile
    spikes_file = SpikesFile(addresses, timestamps)

    if verbose:
        print("pruneBytesToSpikesFile: Spikes bytes converted into a SpikesFile")

    return spikes_file


# TODO: CHECK this
def bytesToSpikesFile(bytes_data, address_size, timestamp_size, verbose=True):
    """
    Converts a bytearray of raw spikes of a-bytes addresses and b-bytes timestamps, where a and b are address_size
    and timestamp_size parameters respectively, to a SpikesFile of raw spikes of the same shape.

    Parameters:
        bytes_data (bytearray): The input bytearray. It must contain raw spikes data (without headers).
        address_size (int): An int indicating the size of the addresses.
        timestamp_size (int): An int indicating the size of the timestamps.
        verbose (boolean): A boolean indicating whether or not debug comments are printed.

    Returns:
        spikes_file (SpikesFile): The output SpikesFile object from pyNAVIS. It contains raw spikes shaped
        as the raw spikes of the input bytearray.

    Notes:
        This function is the inverse of the spikesFileToBytes function.
    """
    start_time = time.time()
    if verbose:
        print("bytesToSpikesFile: Converting spikes bytes to SpikesFile")

    # Separate addresses and timestamps
    # TODO: struct = constructStruct(address_size, timestamp_size)
    spikes_struct = np.dtype([("addresses", ">u1", address_size),
                              ("timestamps", ">u1", timestamp_size)])

    spikes = np.frombuffer(bytes_data, spikes_struct)
    addresses = np.array(spikes['addresses'], copy=False).astype(">u4")
    timestamps = np.array(spikes['timestamps'], copy=False).astype(">u4")

    # Return the SpikesFile
    spikes_file = SpikesFile(addresses, timestamps)

    end_time = time.time()
    if verbose:
        print("bytesToSpikesFile: Data conversion has took " + '{0:.3f}'.format(
            end_time - start_time) + " seconds")

    return spikes_file


# TODO: Checked
def spikesFileToBytes(spikes_file, settings, address_size, timestamp_size, compressor, verbose=True):
    """
    Converts a SpikesFile of raw spikes of a-bytes addresses and b-bytes timestamps, where a and b are address_size
    and timestamp_size parameters respectively, to a bytearray of raw spikes of the same shape.

    Parameters:
        spikes_file (SpikesFile): The input SpikesFile object from pyNAVIS. It must contain raw spikes data (without headers).
        settings (MainSettings): A MainSettings object from pyNAVIS.
        address_size (int): An int indicating the size of the addresses.
        timestamp_size (int): An int indicating the size of the timestamps.
        compressor (string): A string indicating the compressor to be used.
        verbose (boolean): A boolean indicating whether or not debug comments are printed.

    Returns:
        bytes_data (bytearray): The output bytearray. It contains raw spikes shaped as the raw spikes of the
        input SpikesFile.

    Notes:
        This function is the inverse of the bytesToSpikesFile function.
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
        bytes_data['f0'] = spikes_file.addresses.astype(dtype=np.dtype(param), copy=False)
        bytes_data['f1'] = spikes_file.timestamps.astype(dtype=np.dtype(param), copy=False)
    else:
        # In the case of compressing with LZMA compressor, it is better to prune the bytes because
        # we can achieve practically the same compressed file size in a reasonably smaller time. This
        # pruning only happens when size parameters are greater than the original sizes of the addresses and timestamps

        org_address_size = settings.address_size
        org_timestamp_size = settings.timestamp_size

        if not settings.address_size > address_size:
            org_address_size = address_size

        if not settings.timestamp_size > timestamp_size:
            org_timestamp_size = timestamp_size

        address_struct = constructStruct("pruned", (org_address_size - address_size,), "not_pruned", (address_size,))
        timestamp_struct = constructStruct("pruned", (org_timestamp_size - timestamp_size,), "not_pruned", (timestamp_size,))
        spikes_struct = constructStruct("addresses", (address_size,), "timestamps", (timestamp_size,))

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
