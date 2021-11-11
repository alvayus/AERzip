import copy
import math
import time

import numpy as np
from pyNAVIS import SpikesFile

from AERzip.CompressedFileHeader import CompressedFileHeader


def bytesToSpikesFile(bytes_data, input_options, verbose=True):
    """
    Converts a bytearray of raw spikes of a-byte addresses and b-byte timestamps, where a and b are input_options address_size
    and timestamp_size fields respectively, to a SpikesFile of raw spikes of the same shape (or with 4-byte addresses or
    timestamps if a or b are equal to 3 bytes).

    Parameters:
        bytes_data (bytearray): The input bytearray. It must contain raw spikes data (without headers).
        input_options (MainSettings, CompressedFileHeader): A MainSettings object from pyNAVIS or CompressedFileHeader that contains information about the input bytes_data.
        verbose (boolean): A boolean indicating whether or not debug comments are printed.

    Returns:
        spikes_file (SpikesFile): The output SpikesFile object from pyNAVIS.
        output_options (MainSettings, CompressedFileHeader): A MainSettings object from pyNAVIS or CompressedFileHeader that contains information about the output spikes_file.

    Notes:
        This function is the inverse of the spikesFileToBytes function.

        When input_options sizes are 3 bytes it is needed to work differently due to NumPy and Python does not support
        np.uint24 (or working with data types of 3 bytes). It cost more time that viewing the arrays as np.uint8 (1 byte),
        np.uint16 (2 bytes) or np.uint32 (4 bytes). When processing 3-byte addresses or timestamps, the returned
        SpikesFile will contain 4-byte addresses or timestamps to allow SpikesFile processing.

        Based on the above comment, there are two different cases that must be considered:

        1) If the input_options size fields are equal to 3 bytes, output_options size fields will be 4 bytes. You can
        find more information about this in the spikesFileToBytes function.

        2) Otherwise, output_options size fields will have the same value as in the input_options.

        On the other hand, this function can have two different inputs and it is needed to consider these situations:

        1) When **input_settings** is associated with a bytearray extracted from an **original AEDAT file** (you
        want to convert the bytes of the SpikesFile extracted from the original AEDAT file into a
        SpikesFile again) **input_settings should be a MainSettings object**.

        2) When **input_settings** is associated with a bytearray extracted from a **compressed AEDAT file** (you
        want to convert the bytes extracted from the compressed AEDAT file into a SpikesFile), **input_settings should
        be a CompressedFileHeader object**.

        Currently all compressed files use 4-byte addresses and timestamps except those which were compressing with the
        LZMA compressor. You can find more information about this in the spikesFileToBytes function.
    """
    if verbose:
        start_time = time.time()
        print("bytesToSpikesFile: Converting spikes bytes to SpikesFile")

    # Create the new options
    output_options = copy.deepcopy(input_options)

    # 1-byte, 2-byte or 4-byte output addresses
    if input_options.address_size != 3:
        address_struct = np.dtype(">u" + str(input_options.address_size))
    # 3-byte addresses
    else:
        address_struct = np.dtype([("f0", ">u1", input_options.address_size)])

    # 1-byte, 2-byte or 4-byte output timestamps
    if input_options.timestamp_size != 3:
        timestamp_struct = np.dtype(">u" + str(input_options.timestamp_size))
    # 3-byte timestamps
    else:
        timestamp_struct = np.dtype([("f1", ">u1", input_options.timestamp_size)])

    # Separate addresses and timestamps
    spikes_struct = np.dtype([("addresses", address_struct),
                              ("timestamps", timestamp_struct)])
    spikes = np.frombuffer(bytes_data, spikes_struct)

    if input_options.address_size == 3:
        # View addresses as 4-byte ints
        spikes['addresses'] = spikes['addresses'].astype(">u4")

        # Modify the output_options with the new size
        output_options.address_size = 4

    if input_options.timestamp_size == 3:
        # View timestamps as 4-byte ints
        spikes['timestamps'] = spikes['timestamps'].astype(">u4")

        # Modify the output_options with the new size
        output_options.timestamp_size = 4

    # Return the SpikesFile
    spikes_file = SpikesFile(spikes['addresses'], spikes['timestamps'])

    if verbose:
        end_time = time.time()
        print("bytesToSpikesFile: Data conversion has took " + '{0:.3f}'.format(end_time - start_time) + " seconds")

    return spikes_file, output_options


def spikesFileToBytes(spikes_file, input_options, output_options, verbose=True):
    """
    Converts a SpikesFile of raw spikes of a-byte addresses and b-byte timestamps, where a and b are input_options.address_size
    and input_options.timestamp_size fields respectively, to:

    1) A bytearray of raw spikes of c-byte addresses and d-byte timestamps, where c and d are output_options.address_size
    and output_options.timestamps_size fields respectively, **when you intend to compress it and you are using LZMA compressor
    (spikesFileAsType function uses default output_options values)**.

    2) A bytearray of raw spikes of 4-byte addresses and timestamps **when you intend to compress it and you are not using
    LZMA compressor** or **when input_options is not a CompressedFileHeader (MainSettings does not have a compressor
    field) and you do not intend to compress the bytearray**.

    Parameters:
        spikes_file (SpikesFile): The input SpikesFile object from pyNAVIS. It must contain raw spikes data (without headers).
        input_options (MainSettings, CompressedFileHeader): A MainSettings object from pyNAVIS or CompressedFileHeader that contains information about the input spikes_file.
        output_options (MainSettings, CompressedFileHeader): A MainSettings object from pyNAVIS or CompressedFileHeader that contains information about the output bytes_data.
        verbose (boolean): A boolean indicating whether or not debug comments are printed.

    Returns:
        bytes_data (bytearray): The output bytearray.

    Notes:
        This function is the inverse of the bytesToSpikesFile function.

        If you want to store a compressed file from a SpikesFile you must pass a CompressedFileHeader object
        as the output_options parameter and specify the compressor to be used. This is important to work properly in
        the different cases. In order to this, if you use a MainSettings object as output_options and later you set the
        compressor, you could have problems while encoding or decoding the compressed file information.

        In the case of compressing with LZMA compressor, it is better to prune the bytes because we can achieve
        practically the same compressed file size in a reasonably smaller time. Otherwise, viewing addresses and
        timestamps as 4-bytes data usually allows to achieve a better compression, regardless of their original sizes.
    """
    if verbose:
        start_time = time.time()
        print("spikesFileToBytes: Converting SpikesFile to spikes bytes")

    # Case 2. If compressing with LZMA, case 1 (default output_options values)
    if not hasattr(output_options, 'compressor') or output_options.compressor != "LZMA":
        output_options.address_size = 4
        output_options.timestamp_size = 4

    bytes_data = spikesFileAsType(spikes_file, input_options, output_options)

    if verbose:
        end_time = time.time()
        print("spikesFileToBytes: Data conversion has took " + '{0:.3f}'.format(end_time - start_time) + " seconds")

    return bytes_data


def spikesFileAsType(spikes_file, input_options, output_options):
    """
    Converts a-byte addresses and b-byte timestamps from a SpikesFile, where a and b are input_options.address_size and
    input_options.timestamps_size fields respectively, to c-byte addresses and d-byte timestamps, where c and d are
    output_options.address_size and output_options.timestamp_size fields respectively.

    Parameters:
        spikes_file (SpikesFile): The input SpikesFile object from pyNAVIS. It must contain raw spikes data (without headers).
        input_options (MainSettings, CompressedFileHeader): A MainSettings object from pyNAVIS or CompressedFileHeader that contains information about the input spikes_file.
        output_options (MainSettings, CompressedFileHeader): A MainSettings object from pyNAVIS or CompressedFileHeader that contains information about the output timestamps.

    Returns:
        bytes_data (bytearray): The output bytearray that contains the retyped addresses and timestamps (ordered by spikes).

    Notes:
        This function considers sizes between 1 and 4. There is a difference between working with 1, 2 or 4 byte and 3
        byte numpy types, because Python does not allow to work with the last one.

        This functions should be a SpikesFile to SpikesFile converter, but due to in the case of 3-byte types it is
        impossible to create a SpikesFile, the retyped addresses and timestamps are returned into a ordered bytearray.
        The returned bytearray contains the information as desired (output_options) and it is decoded in the
        bytesToSpikesFile function.

        By default numpy astype function is executed in unsafe mode, which means that any data conversions may be done.
        This is useful to convert from greater sizes to lower sizes and viceversa. Anyway, calcBytesToPrune always return
        the minimum number of bytes required for this operations, so in the case you use this function there should not
        be a loss of information (it should be possible to use the safe mode).

        You can find more information about numpy data types and numpy astype function in:
        https://numpy.org/doc/stable/reference/arrays.dtypes.html
        https://numpy.org/doc/stable/reference/generated/numpy.ndarray.astype.html
    """
    # ----- ADDRESSES -----
    # 1-byte, 2-byte or 4-byte output addresses (pruning, no operation and filling cases)
    if output_options.address_size != 3:
        address_struct = np.dtype(">u" + str(output_options.address_size))
        addresses = spikes_file.addresses.astype(dtype=address_struct, copy=False)

    # 3-byte output addresses
    else:
        # Pruning case
        if input_options.address_size > output_options.address_size:
            address_struct = constructStruct("pruned", (input_options.address_size - output_options.address_size,),
                                             "not_pruned", (output_options.address_size,))
            addresses = np.array(spikes_file.addresses, copy=False).view(address_struct)['not_pruned']

        # Filling and no operation cases
        else:
            # It is needed to view addresses as 4-byte (it is impossible to view as 3-byte type). This means that
            # it would not be possible to have 3-byte addresses after filling
            address_struct = np.dtype(">u4")
            addresses = spikes_file.addresses.astype(dtype=address_struct, copy=False)

            # At this point you have to update the output_options because the size field has changed
            output_options.timestamp_size = 4

    # ----- TIMESTAMPS -----
    # 1-byte, 2-byte or 4-byte output timestamps (pruning, no operation and filling cases)
    if output_options.timestamp_size != 3:
        timestamp_struct = np.dtype(">u" + str(output_options.timestamp_size))
        timestamps = spikes_file.timestamps.astype(dtype=timestamp_struct, copy=False)

    # 3-byte output timestamps
    else:
        # Pruning case
        if input_options.timestamp_size > output_options.timestamp_size:
            timestamp_struct = constructStruct("pruned", (input_options.timestamp_size - output_options.timestamp_size,),
                                               "not_pruned", (output_options.timestamp_size,))
            timestamps = np.array(spikes_file.timestamps, copy=False).view(timestamp_struct)['not_pruned']

        # Filling and no operation cases
        else:
            timestamp_struct = constructStruct("zeros", (output_options.timestamp_size - input_options.timestamp_size,),
                                               "timestamps", (output_options.timestamp_size,))
            timestamps = np.zeros(len(spikes_file.timestamps), dtype=timestamp_struct)
            timestamps['timestamps'] = np.array(spikes_file.timestamps, copy=False)

    # ----- BYTES -----
    # Create an array that contains the retyped addresses and timestamps
    spikes_struct = np.dtype(addresses.dtype + ", " + timestamps.dtype)
    new_spikes_file = np.zeros(len(addresses), dtype=spikes_struct)
    new_spikes_file['f0'] = addresses
    new_spikes_file['f1'] = timestamps
    
    # Numpy tobytes() function already joins addresses with timestamps spike by spike due to
    # the spikes_struct structure
    bytes_data = new_spikes_file.tobytes()

    return bytes_data


def calcBytesToPrune(spikes_file, settings):
    """
    Calculates the minimum numbers of bytes required for address and timestamp representation based on the input settings
    and returns a CompressedFileHeader object that contains them.

    Parameters:
        spikes_file (SpikesFile): The input SpikesFile object from pyNAVIS.
        settings (MainSettings): A MainSettings object from pyNAVIS.

    Returns:
        header (CompressedFileHeader): A CompressedFileHeader object.

    Notes:
        This function only works for uncompressed files. Compressed files already contain this information within their headers.
    """
    # Address size
    address_size = int(math.ceil(settings.num_channels * (settings.mono_stereo + 1) *
                                 (settings.on_off_both + 1) / 256))

    # Timestamp size
    dec2bin = bin(spikes_file.max_ts)[2:]
    timestamp_size = int(math.ceil(len(dec2bin) / 8))

    # Return the new CompressedFileHeader object
    header = CompressedFileHeader(address_size=address_size, timestamp_size=timestamp_size)

    return header


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
