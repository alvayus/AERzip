from setup import setup_args


class CompressedFileHeader:
    """
    Class that collects the main information of a compressed aedat file.

    Attributes:
        library_version (string): A string indicating the library version.
        library_version_length (int): An int indicating the number of bytes required to store the library_version string.
        compressor (string): A string indicating the compressor used.
        compressor_length (int): An int indicating the number of bytes required to store the compressor string.
        address_size (int): An int indicating the size of the addresses in the compressed file.
        address_length (int): An int indicating the number of bytes required to store the address_size.
        timestamp_size (int): An int indicating the size of the timestamps in the compressed file.
        timestamp_length (int): An int indicating the number of bytes required to store the timestamp_size.
        end_header (string): The string that represents the end of the header of the generic aedat files.
        end_header_length (int): An int indicating the number of bytes required to store the end_header string.
        header_size (int): An int indicating the sum total of the lengths of each field in the header.
    """

    def __init__(self, compressor="ZSTD", address_size=4, timestamp_size=4):
        """
        Constructor of CompressedFileHeader objects.

        Args:
            compressor (string): A string indicating the compressor to be used.
            address_size (int): An int indicating the size of the addresses.
            timestamp_size (int): An int indicating the size of the timestamps.
        """
        self.library_version = "AERzip v" + setup_args["version"]
        self.library_version_length = 20

        self.compressor = compressor
        self.compressor_length = 10

        self.address_size = address_size
        self.address_length = 4  # 32-bit int

        self.timestamp_size = timestamp_size
        self.timestamp_length = 4  # 32-bit int

        self.end_header = "#End Of ASCII Header\r\n"
        self.end_header_length = len(bytes(self.end_header))

        self.header_size = self.library_version_length + self.compressor_length + self.address_length + self.timestamp_length + self.end_header_length

    def toBytes(self):
        """
        Constructs a bytearray from each field in the CompressedFileHeader object.

        Returns:
            header (bytearray): The CompressedFileHeader object as a bytearray.

        Notes:
            Each field of the header has a fixed position in the returned bytearray.
        """
        header = bytearray()

        header.extend(bytes(self.library_version.ljust(self.library_version_length), "utf-8"))

        if self.compressor == "ZSTD" or self.compressor == "LZ4" or self.compressor == "LZMA":
            header.extend(bytes(self.compressor.ljust(self.compressor_length), "utf-8"))
        else:
            raise ValueError("Compressor not recognized")

        header.extend(self.address_size.to_bytes(self.address_length, "big"))
        header.extend(self.timestamp_size.to_bytes(self.timestamp_length, "big"))

        header.extend(bytes(self.end_header.ljust(self.end_header_length), "utf-8"))

        return header
