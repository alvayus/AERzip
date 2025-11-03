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

        # Field sizes (bytes)
        self.library_version_bytes = 20
        self.compressor_bytes = 10
        self.address_size_bytes = 1
        self.timestamp_size_bytes = 1
        self.optional_bytes = 40
        self.header_end_bytes = 22  # Size of fixed string "#End Of ASCII Header\r\n"

        # Other internal attributes
        self.optional_available = self.optional_bytes  # Allows to control the space available in the optional field
        self.header_size = self.library_version_bytes + self.compressor_bytes + self.address_size_bytes + self.timestamp_size_bytes + self.optional_bytes + self.header_end_bytes

        # Field values
        self.library_version = "AERzip v" + AERzip.__version__
        self.compressor = compressor
        self.address_size = address_size
        self.timestamp_size = timestamp_size
        self.optional = bytearray().ljust(self.optional_bytes)
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

        start_index = self.optional_bytes - self.optional_available
        end_index = start_index + data_size
        self.optional[start_index:end_index] = data
        self.optional_available -= data_size

    def toBytes(self):
        """
        This function constructs a bytearray from the CompressedFileHeader object. This facilitates its storage in a compressed file.

        :return: The CompressedFileHeader object as a bytearray.
        :rtype: bytearray
        """
        if self.address_size is None:
            raise ValueError("The address size must be defined first.")
        if self.timestamp_size is None:
            raise ValueError("The time stamp size must be defined first.")
        
        header_bytes = bytearray()

        # Inserting header data
        header_bytes.extend(bytes(self.library_version.ljust(self.library_version_bytes), "utf-8"))
        if self.compressor is not None:
            header_bytes.extend(bytes(self.compressor.ljust(self.compressor_bytes), "utf-8"))
        else:
            header_bytes.extend(bytes("".ljust(self.compressor_bytes), "utf-8"))
        header_bytes.extend(self.address_size.to_bytes(self.address_size_bytes, "little"))
        header_bytes.extend(self.timestamp_size.to_bytes(self.timestamp_size_bytes, "little"))
        header_bytes.extend(self.optional.ljust(self.optional_bytes))
        header_bytes.extend(bytes(self.header_end.ljust(self.header_end_bytes), "utf-8"))

        return header_bytes
