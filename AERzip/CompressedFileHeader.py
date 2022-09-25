import pkg_resources
from pyNAVIS import MainSettings

import AERzip


class CompressedFileHeader:
    """
    A CompressedFileHeader describes the information contained in its associated compressed aedat file.

    These are the main attributes of this class:

    - library_version (string): A string indicating the library version.
    - compressor (string): A string indicating the compressor used.
    - address_size (int): An int indicating the size of the addresses contained in the compressed file.
    - timestamp_size (int): An int indicating the size of the timestamps contained in the compressed file.
    - header_end (string): The string that represents the end of the header in generic aedat files.

    Each attribute has an int associated which represents its length in bytes inside the compressed aedat file. These
    ints are not stored in the file and they cannot be changed since they are fixed in the CompressedFileHeader's
    constructor method, in order to allow compatibility between different versions of AERzip.
    """

    def __init__(self, compressor=None, address_size=None, timestamp_size=None):
        # Checks before object creation
        if compressor is not None and not (compressor == "ZSTD" or compressor == "LZ4" or compressor == "LZMA"):
            raise ValueError("Only ZSTD, LZ4 or LZMA compression algorithms are supported for now")

        # Sizes of fixed fields
        self.library_version_length = 20
        self.compressor_length = 10
        self.address_size_length = 4  # 32-bit int
        self.timestamp_size_length = 4  # 32-bit int
        self.optional_length = 40
        self.optional_available = 40  # Allows to control the space available in the optional field
        self.header_end_length = 22  # Size of fixed string "#End Of ASCII Header\r\n"
        self.header_length = self.library_version_length + self.compressor_length + self.address_size_length + self.timestamp_size_length + self.optional_length + self.header_end_length

        # Values for fixed fields
        self.library_version = "AERzip v" + AERzip.__version__
        self.compressor = compressor
        self.address_size = address_size
        self.timestamp_size = timestamp_size
        self.optional = bytearray().ljust(self.optional_length)
        self.header_end = "#End Of ASCII Header\r\n"

    def addOptional(self, data_bytes):
        """
        Adds bytes from data_bytes to the optional field of the header.

        :param bytearray data_bytes: Bytes to add to the optional field
        """
        data_bytes_len = len(data_bytes)

        if data_bytes_len > self.optional_available:
            raise MemoryError("The optional field has reached its maximum capacity. No more information can be added")

        start_index = self.optional_length - self.optional_available
        end_index = start_index + data_bytes_len
        self.optional[start_index:end_index] = data_bytes
        self.optional_available -= data_bytes_len

    def toBytes(self):
        """
        Constructs a bytearray from the CompressedFileHeader object using the information contained in each of its
        fields. These fields have a fixed position in the returned bytearray, calculated from the length in bytes of
        each.

        :return: The CompressedFileHeader object as a bytearray.
        :rtype: bytearray
        """
        header_bytes = bytearray()

        # Fixed fields
        header_bytes.extend(bytes(self.library_version.ljust(self.library_version_length), "utf-8"))
        header_bytes.extend(bytes(self.compressor.ljust(self.compressor_length), "utf-8"))
        header_bytes.extend(self.address_size.to_bytes(self.address_size_length, "big"))
        header_bytes.extend(self.timestamp_size.to_bytes(self.timestamp_size_length, "big"))

        # MainSetting fields (with or without pruning)
        header_bytes.extend(self.optional.ljust(self.optional_length))

        # End of the header
        header_bytes.extend(bytes(self.header_end.ljust(self.header_end_length), "utf-8"))

        return header_bytes

    def addMainSettings(self, settings):
        """
        Stores extra information of a MainSettings object from pyNAVIS in the optional field of the header.

        This information is summarized below:

        - num_channels (int): An int indicating the number of channels of the NAS.
        - mono_stereo (int): An int indicating if the file is mono or stereo.
        - ts_tick (float): A float indicating the correspondence factor for timestamps.
        - on_off (int): An int indicating if the addresses correspond to ON or OFF (or both) spikes

        :param MainSettings settings: A MainSettings object from pyNAVIS.
        """
        # Checking settings
        if not isinstance(settings, MainSettings):
            raise ValueError("Settings must be specified as a MainSettings object from pyNAVIS")

        # Fields to bytes
        num_channels_bytes = settings.num_channels.to_bytes(4, "big")  # 32-bit int
        mono_stereo_bytes = settings.mono_stereo.to_bytes(1, "big")  # 8-bit int. Minimum data size in Python
        ts_tick_bytes = settings.ts_tick.to_bytes(4, "big")  # 32-bit float
        on_off_both_bytes = settings.on_off_both.to_bytes(1, "big")  # 8-bit int. Minimum data size in Python

        # Adding bytes to optional field
        self.addOptional(num_channels_bytes)
        self.addOptional(mono_stereo_bytes)
        self.addOptional(ts_tick_bytes)
        self.addOptional(on_off_both_bytes)
