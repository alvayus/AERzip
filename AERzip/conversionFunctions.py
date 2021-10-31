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

    # Check if the data is correct (with original aedat file sizes)
    checkBytes(bytes_data, settings.address_size, settings.timestamp_size)

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

    # Check if the data is correct
    checkBytes(bytes_data, address_size, timestamp_size)

    # Separate addresses and timestamps
    struct = constructStruct(address_size, timestamp_size)

    spikes = np.frombuffer(bytes_data, struct)
    addresses = spikes['f0']
    timestamps = spikes['f1']

    # Return the SpikesFile
    spikes_file = SpikesFile(addresses, timestamps)

    end_time = time.time()
    if verbose:
        print("bytesToSpikesFile: Data conversion has took " + '{0:.3f}'.format(
            end_time - start_time) + " seconds")

    return spikes_file


def spikesFileToBytes(spikes_file, address_size, timestamp_size, verbose=True):
    """
    Converts a SpikesFile of raw spikes of a-bytes addresses and b-bytes timestamps, where a and b are address_size
    and timestamp_size parameters respectively, to a bytearray of raw spikes of the same shape.

    Parameters:
        spikes_file (SpikesFile): The input SpikesFile object from pyNAVIS. It must contain raw spikes data (without headers).
        address_size (int): An int indicating the size of the addresses.
        timestamp_size (int): An int indicating the size of the timestamps.
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

    # Prune bytes before compression (if parameter sizes are not original sizes)
    address_param = ">u" + str(address_size)
    timestamp_param = ">u" + str(timestamp_size)
    struct = np.dtype(address_param + ", " + timestamp_param)

    bytes_data = np.zeros(len(spikes_file.addresses), dtype=struct)
    bytes_data['f0'] = spikes_file.addresses.astype(dtype=np.dtype(address_param), copy=False)
    bytes_data['f1'] = spikes_file.timestamps.astype(dtype=np.dtype(timestamp_param), copy=False)

    # Return the spikes bytearray (pruned or not)
    bytes_data = bytes_data.tobytes()

    end_time = time.time()
    if verbose:
        print("spikesFileToBytes: Data conversion has took " + '{0:.3f}'.format(
            end_time - start_time) + " seconds")

    return bytes_data


def checkBytes(bytes_data, address_size, timestamp_size):
    """
    Checks if the bytes_data input bytearray contains a whole number of spikes.

    Parameters:
        bytes_data (bytearray): The input bytearray. It must contain raw spikes data (without headers).
        address_size (int): An int indicating the size of the addresses.
        timestamp_size (int): An int indicating the size of the timestamps.

    Returns:
        True if bytes_data contains a whole number of spikes. Otherwise raise an exception.
    """
    bytes_per_spike = address_size + timestamp_size
    bytes_data_length = len(bytes_data)
    num_spikes = bytes_data_length / bytes_per_spike
    if not num_spikes.is_integer():
        raise ValueError("Spikes are not a whole number. Something went wrong with the file")
    else:
        return True


def getBytesToPrune(settings):
    """
    Gets the minimum number of bytes needed for spikes addresses and timestamps representation based on the input settings.

    Parameters:
        settings (MainSettings): A MainSettings object from pyNAVIS.

    Returns:
        address_size (int): An int indicating the minimum number of bytes to represent the addresses.
        timestamp_size (int): An int indicating the minimum number of bytes to represent the timestamps.
    """
    address_size = int(math.ceil(settings.num_channels * (settings.mono_stereo + 1) *
                                 (settings.on_off_both + 1) / 256))
    # TODO: Timestamps
    timestamp_size = 4

    return address_size, timestamp_size


def constructStruct(address_size, timestamp_size):
    """
    Constructs a numpy data type to represent the data structure of an bytearray.

    Parameters:
        address_size (int): An int indicating the size of the addresses.
        timestamp_size (int): An int indicating the size of the timestamps.

    Returns:
        struct (dtype):
    """
    address_param = ">u" + str(address_size)
    timestamp_param = ">u" + str(timestamp_size)
    struct = np.dtype(address_param + ", " + timestamp_param)

    return struct
