from pyNAVIS import MainSettings


class CompressedFileHeader:
    """
    A CompressedFileHeader describes the information contained in its associated compressed aedat file.

    These are the main attributes of this class:
    - library_version (string): A string indicating the library version.
    - compressor (string): A string indicating the compressor used.
    - num_channels (int): An int indicating the number of channels of the NAS.
    - mono_stereo (int): An int indicating if the file is mono or stereo.
    - ts_tick (float): A float indicating the correspondence factor for timestamps.
    - on_off (int): An int indicating if the addresses correspond to ON or OFF (or both) spikes
    - address_size (int): An int indicating the size of the addresses contained in the compressed file.
    - timestamp_size (int): An int indicating the size of the timestamps contained in the compressed file.
    - end_header (string): The string that represents the end of the header in generic aedat files.
    - header_size (int): An int indicating the total length of the header in the compressed file.

    Each attribute has an int associated which represents its length in bytes inside the compressed aedat file. These
    ints are not stored in the file and they cannot be changed since they are fixed in the CompressedFileHeader's
    constructor method, in order to allow compatibility between different versions of AERzip.
    """

    def __init__(self, compressor, settings):
        """
        Constructor of CompressedFileHeader objects.

        :param string compressor: A string indicating the compressor to be used.
        :param MainSettings settings: A MainSettings object from pyNAVIS containing the required fields for the building of the compressed file.
        """
        if not (self.compressor == "ZSTD" or self.compressor == "LZ4" or self.compressor == "LZMA"):
            raise ValueError("Only ZSTD, LZ4 or LZMA compression algorithms are supported for now")

        if not settings or not isinstance(settings, MainSettings):
            raise ValueError("Settings must be specified as a MainSettings object from pyNAVIS")

        self.library_version = "AERzip v0.6.5"
        self.library_version_length = 20

        self.compressor = compressor
        self.compressor_length = 10

        self.num_channels = settings.num_channels
        self.num_channels_length = 4  # 32-bit int

        self.mono_stereo = settings.mono_stereo
        self.mono_stereo_length = 1  # 8-bit int. Minimum data size in Python

        self.ts_tick = settings.ts_tick
        self.ts_tick_length = 4  # 32-bit float

        self.on_off_both = settings.on_off_both
        self.on_off_both_length = 1  # 8-bit int. Minimum data size in Python

        self.address_size = settings.address_size
        self.address_length = 4  # 32-bit int

        self.timestamp_size = settings.timestamp_size
        self.timestamp_length = 4  # 32-bit int

        self.end_header = "#End Of ASCII Header\r\n"
        self.end_header_length = 22  # Fixed value (compatibility with other versions?)

        self.header_size = self.library_version_length + self.compressor_length + self.num_channels_length + self.mono_stereo_length + self.ts_tick_length + self.on_off_both_length + self.address_length + self.timestamp_length + self.end_header_length

    def toBytes(self):
        """
        Constructs a bytearray from the CompressedFileHeader object using the information contained in each of its
        fields. These fields have a fixed position in the returned bytearray, calculated from the length in bytes of
        each.

        :return bytearray header_bytes: The CompressedFileHeader object as a bytearray.
        """
        header_bytes = bytearray()

        # Library version and compressor used
        header_bytes.extend(bytes(self.library_version.ljust(self.library_version_length), "utf-8"))
        header_bytes.extend(bytes(self.compressor.ljust(self.compressor_length), "utf-8"))

        # MainSetting fields (with or without pruning)
        header_bytes.extend(self.num_channels.to_bytes(self.num_channels_length, "big"))
        header_bytes.extend(self.mono_stereo.to_bytes(self.mono_stereo_length, "big"))
        header_bytes.extend(self.ts_tick.to_bytes(self.ts_tick_length, "big"))
        header_bytes.extend(self.on_off_both.to_bytes(self.on_off_both_length, "big"))
        header_bytes.extend(self.address_size.to_bytes(self.address_length, "big"))
        header_bytes.extend(self.timestamp_size.to_bytes(self.timestamp_length, "big"))

        # End of the header
        header_bytes.extend(bytes(self.end_header.ljust(self.end_header_length), "utf-8"))

        return header_bytes
