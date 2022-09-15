import unittest

from pyNAVIS import MainSettings, Loaders

from AERzip.compressionFunctions import compressDataFromFile, compressedFileToSpikesFile


class CompressionFunctionTests(unittest.TestCase):

    def setUp(self):
        # Defining settings
        self.file_settings_stereo_64ch_4a_4t_ts1 = MainSettings(num_channels=64, mono_stereo=1, on_off_both=1,
                                                                address_size=4, timestamp_size=4, ts_tick=1,
                                                                bin_size=10000)
        self.file_settings_stereo_64ch_2a_4t_ts02 = MainSettings(num_channels=64, mono_stereo=1, on_off_both=1,
                                                                 address_size=2, timestamp_size=4, ts_tick=0.2,
                                                                 bin_size=10000)
        self.file_settings_mono_64ch_2a_4t_ts02 = MainSettings(num_channels=64, mono_stereo=0, on_off_both=1,
                                                               address_size=2, timestamp_size=4, ts_tick=0.2,
                                                               bin_size=10000)
        self.file_settings_mono_32ch_2a_4t_ts02 = MainSettings(num_channels=32, mono_stereo=0, on_off_both=1,
                                                               address_size=2, timestamp_size=4, ts_tick=0.2,
                                                               bin_size=10000)

        # Loading spikes_files
        self.files_data = [
            ("events/dataset/enun_stereo_64ch_ONOFF_addr4b_ts1.aedat", self.file_settings_stereo_64ch_4a_4t_ts1),
            ("events/dataset/130Hz_mono_64ch_ONOFF_addr2b_ts02.aedat", self.file_settings_mono_64ch_2a_4t_ts02),
            ("events/dataset/523Hz_stereo_64ch_ONOFF_addr2b_ts02.aedat", self.file_settings_stereo_64ch_2a_4t_ts02),
            ("events/dataset/sound_mono_32ch_ONOFF_addr2b_ts02.aedat", self.file_settings_mono_32ch_2a_4t_ts02)
        ]
        self.spikes_files = []
        for file_data in self.files_data:
            self.spikes_files.append(Loaders.loadAEDAT(file_data[0], file_data[1]))

    def test_compressAndDecompress(self):
        compression_algorithms = ["ZSTD", "LZMA", "LZ4"]

        for i in range(len(self.spikes_files)):
            spikes_file = self.spikes_files[i]
            file_data = self.files_data[i]

            for algorithm in compression_algorithms:
                # Compressing the spikes_file
                compressed_file, _ = compressDataFromFile(file_data[0], file_data[1], algorithm, store=False, verbose=False)

                # Decompressing the spikes_file
                header, spikes_file, final_address_size, final_timestamp_size = compressedFileToSpikesFile(compressed_file, verbose=False)

                # Compare original and final spikes_file
                self.assertEqual(header.compressor, algorithm)
                self.assertEqual(spikes_file.addresses.tolist(), spikes_file.addresses.tolist())
                self.assertEqual(spikes_file.timestamps.tolist(), spikes_file.timestamps.tolist())
                self.assertEqual(header.header_end, "#End Of ASCII Header\r\n")


if __name__ == '__main__':
    unittest.main(verbosity=2)
