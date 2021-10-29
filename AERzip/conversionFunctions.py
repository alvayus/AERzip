import math
import time

import numpy as np
from pyNAVIS import SpikesFile


def bytesToSpikesFile(bytes_data, address_size=4, timestamp_size=4, verbose=True):
    start_time = time.time()
    if verbose:
        print("bytesToSpikesFile: Converting bytes to SpikesFile")

    # Check if the data is correct
    checkBytes(bytes_data, address_size, timestamp_size)

    # Separate addresses and timestamps
    struct = constructStruct(address_size, timestamp_size)

    spikes = np.frombuffer(bytes_data, struct)
    addresses = spikes['f0']
    timestamps = spikes['f1']

    # Return the SpikesFile
    raw_file = SpikesFile(addresses, timestamps)

    end_time = time.time()
    if verbose:
        print("bytesToSpikesFile: Data conversion has took " + '{0:.3f}'.format(
            end_time - start_time) + " seconds")

    return raw_file


def discardBytesToSpikesBytearray(bytes_data, settings, new_address_size,
                                  new_timestamp_size, verbose=True):
    start_time = time.time()
    if verbose:
        print("discardBytesToSpikesBytearray: Converting bytearray of spikes"
              "from " + str(settings.timestamp_size) + "-bytes addresses and " +
              str(settings.timestamp_size) + "-bytes timestamps to " + new_address_size +
              "-bytes addresses and " + new_timestamp_size + "-bytes timestamps")

    # Check if the data is correct (with original aedat file sizes)
    checkBytes(bytes_data, settings.address_size, settings.timestamp_size)

    # Read addresses and timestamps (with original aedat file sizes)
    struct = constructStruct(settings.address_size, settings.timestamp_size)

    spikes = np.frombuffer(bytes_data, struct)

    # Convert address and timestamp sizes (with desired sizes)
    struct = constructStruct(new_address_size, new_timestamp_size)

    # Return the smallest bytearray
    small_bytes = spikes.astype(dtype=struct, copy=False)

    end_time = time.time()
    if verbose:
        print("discardBytesToSpikesBytearray: Data conversion has took " + '{0:.3f}'.format(
            end_time - start_time) + " seconds")

    return small_bytes


def discardBytesToSpikesFile(bytes_data, settings, new_address_size, new_timestamp_size, verbose=True):

    smallest_bytes_data = discardBytesToSpikesBytearray(bytes_data, settings,
                                                        new_address_size, new_timestamp_size)

    # Extracting addresses and timestamps from bytearray
    addresses = smallest_bytes_data['f0']
    timestamps = smallest_bytes_data['f1']

    # Return the SpikesFile
    raw_file = SpikesFile(addresses, timestamps)

    if verbose:
        print("discardBytesToSpikesFile: Spikes bytearray converted into a SpikesFile")

    return raw_file


def rawFileToSpikesBytearray(raw_file, address_size=4, timestamp_size=4, verbose=True):
    start_time = time.time()
    if verbose:
        print("rawFileToSpikesBytearray: Converting SpikesFile to bytes")

    # Discard bytes before compression (if parameter sizes are not original sizes)
    address_param = ">u" + str(address_size)
    timestamp_param = ">u" + str(timestamp_size)
    struct = np.dtype(address_param + ", " + timestamp_param)

    raw_data = np.zeros(len(raw_file.addresses), dtype=struct)
    raw_data['f0'] = raw_file.addresses.astype(dtype=np.dtype(address_param), copy=False)
    raw_data['f1'] = raw_file.timestamps.astype(dtype=np.dtype(timestamp_param), copy=False)

    # Return the spikes bytearray (smallest or not)
    raw_data = raw_data.tobytes()

    end_time = time.time()
    if verbose:
        print("rawFileToSpikesBytearray: Data conversion has took " + '{0:.3f}'.format(
            end_time - start_time) + " seconds")

    return raw_data


def checkBytes(bytes_data, address_size, timestamp_size):
    bytes_per_spike = address_size + timestamp_size
    bytes_data_length = len(bytes_data)
    num_spikes = bytes_data_length / bytes_per_spike
    if not num_spikes.is_integer():
        raise ValueError("Spikes are not a whole number. Something went wrong with the file")
    else:
        return True


def getBytesToDiscard(settings):
    # --- Get bytes needed to address and timestamp representation ---
    address_size = int(math.ceil(settings.num_channels * (settings.mono_stereo + 1) *
                                 (settings.on_off_both + 1) / 256))
    # TODO: Timestamps
    timestamp_size = 4

    return address_size, timestamp_size


def constructStruct(address_size, timestamp_size):
    address_param = ">u" + str(address_size)
    timestamp_param = ">u" + str(timestamp_size)
    struct = np.dtype(address_param + ", " + timestamp_param)

    return struct
