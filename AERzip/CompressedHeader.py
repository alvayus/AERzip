import sys


class CompressedHeader:
    def __init__(self, compressor="ZSTD", address_size=4, timestamp_size=4):
        self.compressor = compressor
        self.address_size = address_size
        self.timestamp_size = timestamp_size
        self.header_size = 6

    def toBytes(self):
        header = bytearray()

        if self.compressor == "ZSTD":
            header.extend(bytes("ZSTD", "utf-8"))  # 4 bytes for the compressor
        elif self.compressor == "LZ4":
            header.extend(bytes("LZ4 ", "utf-8"))  # 4 bytes for the compressor
        else:
            raise ValueError("Compressor not recognized. Aborting...")

        header.extend((self.address_size - 1).to_bytes(1, "big"))  # 1 byte for address size
        header.extend((self.timestamp_size - 1).to_bytes(1, "big"))  # 1 byte for timestamp size

        return header
