class CompressedHeader:
    def __init__(self, compressor="ZSTD", address_size=4, timestamp_size=4):
        self.library_version = "AERzip v0.5.0"
        self.library_version_length = 13

        self.compressor = compressor
        self.compressor_length = 5

        self.address_size = address_size
        self.address_length = 1

        self.timestamp_size = timestamp_size
        self.timestamp_length = 1

        self.header_size = self.library_version_length + self.compressor_length + self.address_length + self.timestamp_length

    def toBytes(self):
        header = bytearray()

        header.extend(bytes(self.library_version.ljust(self.library_version_length), "utf-8"))

        if self.compressor == "ZSTD":
            header.extend(bytes("ZSTD".ljust(self.compressor_length), "utf-8"))
        elif self.compressor == "LZ4":
            header.extend(bytes("LZ4".ljust(self.compressor_length), "utf-8"))
        else:
            raise ValueError("Compressor not recognized")

        header.extend((self.address_size - 1).to_bytes(self.address_length, "big"))
        header.extend((self.timestamp_size - 1).to_bytes(self.timestamp_length, "big"))

        return header
