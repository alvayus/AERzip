from pyNAVIS import MainSettings

import AERzip


class CompressedFileHeader:
    """
    A CompressedFileHeader contains useful metadata for compressed files from AERzip. Thus, compressed files consist of a header and 
    the recorded data (addresses and time stamps of the spikes).

    The main fields of this header are the following:

    - library_version (string): A string indicating the library version.
    - compressor (string): A string indicating the compressor used.
    - address_size (int): An integer indicating the size of the addresses contained in the compressed file.
    - timestamp_size (int): An integer indicating the size of the timestamps contained in the compressed file.
    - header_end (string): The string that represents the end of the header. This is the string used in generic AEDAT files.

    Each field has a specific size. Thus, the sum of the size of all these fields determines the total size of the header. 
    """

    def __init__(self, compressor=None, address_size=None, timestamp_size=None):
        # Checking parameters
        # TODO: Compressors? Empty for now
        '''if compressor is not None and not (compressor == "ZSTD" or compressor == "LZ4" or compressor == "LZMA"):
            raise ValueError("Only ZSTD, LZ4 or LZMA compression algorithms are supported for now")'''
        
        if address_size is None:
            raise ValueError("The address size must be defined.")
        if timestamp_size is None:
            raise ValueError("The time stamp size must be defined.")

        # Field sizes (bytes)
        self.library_version_size = 20
        self.compressor_size = 10
        self.address_size_size = 4  # 32-bit int
        self.timestamp_size_size = 4  # 32-bit int
        self.optional_size = 40
        self.header_end_size = 22  # Size of fixed string "#End Of ASCII Header\r\n"

        # Other internal attributes
        self.optional_available = self.optional_size  # Allows to control the space available in the optional field
        self.header_size = self.library_version_size + self.compressor_size + self.address_size_size + self.timestamp_size_size + self.optional_size + self.header_end_size

        # Field values
        self.library_version = "AERzip v" + AERzip.__version__
        self.compressor = compressor
        self.address_size = address_size
        self.timestamp_size = timestamp_size
        self.optional = bytearray().ljust(self.optional_size)
        self.header_end = "#End Of ASCII Header\r\n"

    def addOptional(self, data):
        """
        This function allows to insert data (in bytes) into the optional field of the header.

        :param bytearray data: Data to insert into the optional
        :raises MemoryError: It is not allowed to use this function when there is not enough space in the optional field.
        :return: None
        """
        data_size = len(data)

        if data_size > self.optional_available:
            raise MemoryError("The optional field has reached its maximum capacity.")

        start_index = self.optional_size - self.optional_available
        end_index = start_index + data_size
        self.optional[start_index:end_index] = data
        self.optional_available -= data_size

    def toBytes(self):
        """
        This function constructs a bytearray from the CompressedFileHeader object. This facilitates its storage in a compressed file.

        :return: The CompressedFileHeader object as a bytearray.
        :rtype: bytearray
        """
        header_bytes = bytearray()

        # Inserting header data
        header_bytes.extend(bytes(self.library_version.ljust(self.library_version_size), "utf-8"))
        header_bytes.extend(bytes(self.compressor.ljust(self.compressor_size), "utf-8"))
        header_bytes.extend(self.address_size.to_bytes(self.address_size_size, "big"))
        header_bytes.extend(self.timestamp_size.to_bytes(self.timestamp_size_size, "big"))
        header_bytes.extend(self.optional.ljust(self.optional_size))
        header_bytes.extend(bytes(self.header_end.ljust(self.header_end_size), "utf-8"))

        return header_bytes

    # TODO: Delete this function
    '''def addMainSettings(self, settings):
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
        self.addOptional(on_off_both_bytes)'''
