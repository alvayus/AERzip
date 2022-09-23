import copy
import math
import time

import numpy as np
from pyNAVIS import SpikesFile


def bytesToSpikesFile(bytes_data, initial_address_size, initial_timestamp_size, verbose=True):
    """
    Converts a bytearray of raw spikes of a-byte addresses and b-byte timestamps, where a and b are initial_address_size
    and initial_timestamp_size fields, respectively, to a SpikesFile of raw spikes of the same shape (or with 4-byte
    addresses or timestamps if a or b are equal to 3 bytes).

    This is the inverse function of the spikesFileToBytes function.

    :param bytearray bytes_data: The input bytearray. It must contain raw spikes data (without headers).
    :param int initial_address_size: An int indicating the size of the addresses in bytes_data.
    :param int initial_timestamp_size: An int indicating the size of the timestamps in bytes_data.
    :param boolean verbose: A boolean indicating whether or not debug comments are printed.

    :return:
    - spikes_file (SpikesFile): The output SpikesFile object from pyNAVIS.
    - final_address_size (int): An int indicating the size of the addresses in the final SpikesFile.
    - final_timestamp_size (int): An int indicating the size of the timestamps in the final SpikesFile.

    .. notes:
        When input_options sizes are 3 bytes it is needed to work differently due to NumPy and Python does not support
        np.uint24 (or working with data types of 3 bytes). It cost more time that viewing the arrays as np.uint8 (1 byte),
        np.uint16 (2 bytes) or np.uint32 (4 bytes). When processing 3-byte addresses or timestamps, the returned
        SpikesFile will contain 4-byte addresses or timestamps to allow SpikesFile processing.

        Based on the above comment, there are two different cases that must be considered:

        1) If the input_options size fields are equal to 3 bytes, final_address_size and final_timestamp_size will be 4
        bytes.

        2) Otherwise, these will have the same value as in the input_options.

        Currently all compressed files use 4-byte addresses and timestamps except those which were compressing with the
        LZMA compressor. You can find more information about this in the spikesFileToCompressedFile function.
    """
    if verbose:
        start_time = time.time()
        print("bytesToSpikesFile: Converting spikes bytes to SpikesFile")

    # Storing new sizes
    final_address_size = copy.deepcopy(initial_address_size)
    final_timestamp_size = copy.deepcopy(initial_timestamp_size)

    if final_address_size == 3:
        address_param = ">3u1"
    else:
        address_param = ">u" + str(final_address_size)

    if final_timestamp_size == 3:
        timestamp_param = ">3u1"
    else:
        timestamp_param = ">u" + str(final_timestamp_size)

    # Separate addresses and timestamps
    spikes_struct = np.dtype(address_param + ", " + timestamp_param)
    spikes = np.frombuffer(bytes_data, spikes_struct)

    if initial_address_size == 3:
        # Filling timestamps to reach 4-byte ints
        address_struct = constructStruct("zeros", (4 - initial_address_size,),
                                         "addresses", (initial_address_size,))
        addresses = np.zeros(len(spikes['f0']), dtype=address_struct)
        addresses['addresses'] = np.array(spikes['f0'], copy=False)
        addresses = addresses.view(">u4")

        # Modify the output_options with the new size
        final_address_size = 4
    else:
        addresses = spikes['f0']

    if initial_timestamp_size == 3:
        # Filling timestamps to reach 4-byte ints
        timestamp_struct = constructStruct("zeros", (4 - initial_timestamp_size,),
                                           "timestamps", (initial_timestamp_size,))
        timestamps = np.zeros(len(spikes['f1']), dtype=timestamp_struct)
        timestamps['timestamps'] = np.array(spikes['f1'], copy=False)
        timestamps = timestamps.view(">u4")

        # Modify the output_options with the new size
        final_timestamp_size = 4
    else:
        timestamps = spikes['f1']

    # Return the SpikesFile
    spikes_file = SpikesFile(addresses, timestamps)

    if verbose:
        end_time = time.time()
        print("bytesToSpikesFile: Data conversion has took " + '{0:.3f}'.format(end_time - start_time) + " seconds")

    return spikes_file, final_address_size, final_timestamp_size


def spikesFileToBytes(spikes_file, initial_address_size, initial_timestamp_size, final_address_size,
                      final_timestamp_size, verbose=True):
    """
    Converts a SpikesFile of raw spikes of a-byte addresses and b-byte timestamps, where a and b are specified by
    settings, to a bytearray of raw spikes of c-byte addresses and d-byte timestamps, where c and d are
    final_address_size and final_timestamp_size, respectively.

    This is the inverse function of the bytesToSpikesFile function.

    :param SpikesFile spikes_file: The input SpikesFile object from pyNAVIS.
    :param int initial_address_size: An int indicating the size of the addresses in spikes_file.
    :param int initial_timestamp_size: An int indicating the size of the timestamps in spikes_file.
    :param int final_address_size: An int indicating the size of the addresses in the final bytearray.
    :param int final_timestamp_size: An int indicating the size of the timestamps in the final bytearray.
    :param boolean verbose: A boolean indicating whether or not debug comments must be printed.

    :return bytearray bytes_data: The output bytearray.
    """
    if verbose:
        start_time = time.time()
        print("spikesFileToBytes: Converting the SpikesFile to raw bytes")

    # ----- ADDRESSES -----
    # 1-byte, 2-byte or 4-byte output addresses (pruning, no operation and filling cases)
    if final_address_size != 3:
        address_struct = np.dtype(">u" + str(final_address_size))
        addresses = spikes_file.addresses.astype(dtype=address_struct, copy=False)

    # 3-byte output addresses
    else:
        # Pruning case
        if initial_address_size > final_address_size:
            address_struct = constructStruct("pruned", (initial_address_size - final_address_size,),
                                             "not_pruned", (final_address_size,))

            # There can be a problem if addresses are not encoded in big endian
            addresses = np.array(spikes_file.addresses, copy=False).view(address_struct)['not_pruned']

        # Filling and no operation cases
        else:
            address_struct = constructStruct("zeros", (final_address_size - initial_address_size,),
                                             "addresses", (final_address_size,))
            addresses = np.zeros(len(spikes_file.addresses), dtype=address_struct)
            addresses['addresses'] = np.array(spikes_file.addresses, copy=False)

    # ----- TIMESTAMPS -----
    # 1-byte, 2-byte or 4-byte output timestamps (pruning, no operation and filling cases)
    if final_timestamp_size != 3:
        timestamp_struct = np.dtype(">u" + str(final_timestamp_size))
        timestamps = spikes_file.timestamps.astype(dtype=timestamp_struct, copy=False)

    # 3-byte output timestamps
    else:
        # Pruning case
        if initial_timestamp_size > final_timestamp_size:
            timestamp_struct = constructStruct("pruned", (initial_timestamp_size - final_timestamp_size,),
                                               "not_pruned", (final_timestamp_size,))

            # There can be a problem if timestamps are not encoded in big endian
            timestamps = np.array(spikes_file.timestamps, copy=False).view(timestamp_struct)['not_pruned']

        # Filling and no operation cases
        else:
            timestamp_struct = constructStruct("zeros", (final_timestamp_size - initial_timestamp_size,),
                                               "timestamps", (final_timestamp_size,))
            timestamps = np.zeros(len(spikes_file.timestamps), dtype=timestamp_struct)
            timestamps['timestamps'] = np.array(spikes_file.timestamps, copy=False)

    # ----- BYTES_DATA -----
    # Create an array that contains the retyped addresses and timestamps
    if final_address_size == 3:
        address_param = ">3u1"
    else:
        address_param = ">u" + str(final_address_size)

    if final_timestamp_size == 3:
        timestamp_param = ">3u1"
    else:
        timestamp_param = ">u" + str(final_timestamp_size)

    spikes_struct = np.dtype(address_param + ", " + timestamp_param)
    new_spikes_file = np.zeros(len(addresses), dtype=spikes_struct)
    new_spikes_file['f0'] = addresses
    new_spikes_file['f1'] = timestamps

    # Numpy tobytes() function already joins addresses with timestamps spike by spike due to
    # the spikes_struct structure
    data_bytes = new_spikes_file.tobytes()

    if verbose:
        end_time = time.time()
        print("spikesFileToBytes: Data conversion has took " + '{0:.3f}'.format(end_time - start_time) + " seconds")

    return data_bytes


def calcRequiredBytes(spikes_file, settings):
    """
    Calculates the minimum number of bytes required for address and timestamp representation based on the input settings
    and returns them. This function only works for uncompressed files because compressed files already contain this
    information within their headers.

    Note that, since input settings are contained in a MainSettings object from pyNAVIS, this function is only useful
    for NAS aedat files.

    :param SpikesFile spikes_file: The input SpikesFile object from pyNAVIS.
    :param MainSettings settings: A MainSettings object from pyNAVIS.

    :return CompressedFileHeader header: A CompressedFileHeader object.
    """
    # Address size
    address_size = int(math.ceil(settings.num_channels * (settings.mono_stereo + 1) *
                                 (settings.on_off_both + 1) / 256))

    # Timestamp size
    dec2bin = bin(spikes_file.max_ts)[2:]
    timestamp_size = int(math.ceil(len(dec2bin) / 8))

    return address_size, timestamp_size


def constructStruct(first_field, first_field_size, second_field, second_file_size):
    """
    Constructs a numpy data type of two fields to represent the data structure of a bytearray. This function has been
    internally used to simplify the AERzip's code, but it should not be needed in an external use of the package.

    :param string first_field: A string indicating the name of the first field.
    :param (int, tuple) first_field_size: An int or tuple indicating the number of bytes of the elements of the first field.
    :param string second_field: A string indicating the name of the second field.
    :param (int, tuple) second_file_size: An int or tuple indicating the number of bytes of the elements of the second field.

    :return struct: A numpy data type structure required to interpret a bytearray.
    """

    struct = np.dtype([(first_field, ">u1", first_field_size), (second_field, ">u1", second_file_size)])

    return struct
