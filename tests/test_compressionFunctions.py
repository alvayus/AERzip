import unittest

from pyNAVIS import MainSettings, Loaders

from AERzip.compressionFunctions import compressDataFromFile, compressedFileToSpikesFile


class CompressionFunctionTests(unittest.TestCase):

    def setUp(self):
        # Create settings object
        self.file_settings = MainSettings(num_channels=64, mono_stereo=1, on_off_both=1, address_size=4,
                                          timestamp_size=4, ts_tick=1, bin_size=10000)

        # Loading a spikes_file
        self.file_path = "events/dataset/enun_stereo_64ch_ONOFF_addr4b_ts1.aedat"
        self.spikes_file = Loaders.loadAEDAT(self.file_path, self.file_settings)

    def test_compressAndDecompress(self):
        compression_algorithms = ["ZSTD", "LZMA", "LZ4"]

        for algorithm in compression_algorithms:
            # Compressing the spikes_file
            compressed_file, _ = compressDataFromFile(self.file_path, self.file_settings, algorithm, store=False)

            # Decompressing the spikes_file
            _, spikes_file, _ = compressedFileToSpikesFile(compressed_file)

            # Compare original and final spikes_file
            self.assertEqual(self.spikes_file.addresses.tolist(), spikes_file.addresses.tolist())
            self.assertEqual(self.spikes_file.timestamps.tolist(), spikes_file.timestamps.tolist())


    '''def test_compressDataFromFile(self):
        # Calling the target function
        compressed_file_zstd = compressDataFromFile(self.file_path, self.file_settings, "ZSTD", store=False)
        compressed_file_lzma = compressDataFromFile(self.file_path, self.file_settings, "LZMA", store=False)
        compressed_file_lz4 = compressDataFromFile(self.file_path, self.file_settings, "LZ4", store=False)'''


if __name__ == '__main__':
    unittest.main(verbosity=2)
