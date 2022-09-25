import copy
import os
import unittest

from pyNAVIS import MainSettings, Loaders

from AERzip.CompressedFileHeader import CompressedFileHeader
from AERzip.compressionFunctions import compressDataFromStoredFile, compressedFileToSpikesFile, checkFileExists, \
    getCompressedFile, extractCompressedData, decompressData, compressDataFromStoredNASFile, loadFile, \
    spikesFileToCompressedFile, extractDataFromCompressedFile


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

        # Defining compression algorithms
        self.compression_algorithms = ["ZSTD", "LZMA", "LZ4"]

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
        for i in range(len(self.spikes_files)):
            spikes_file = self.spikes_files[i]
            file_data = self.files_data[i]

            for algorithm in self.compression_algorithms:
                # Compressing the spikes_file
                compressed_file, _ = compressDataFromStoredNASFile(file_data[0], file_data[1], algorithm, store=False,
                                                                   ask_user=False, overwrite=False, verbose=False)

                # Decompressing the spikes_file
                header, spikes_file, final_address_size, final_timestamp_size = \
                    compressedFileToSpikesFile(compressed_file, verbose=False)

                # Compare original and final spikes_file
                self.assertEqual(header.compressor, algorithm)
                self.assertEqual(spikes_file.addresses.tolist(), spikes_file.addresses.tolist())
                self.assertEqual(spikes_file.timestamps.tolist(), spikes_file.timestamps.tolist())
                self.assertEqual(header.header_end, "#End Of ASCII Header\r\n")

    def test_compressedFileToFromSpikesFile(self):
        for file_data in self.files_data:
            for algorithm in self.compression_algorithms:
                # Get associated compressed file path
                split_path = file_data[0].split("/")
                split_path[len(split_path) - 2] = split_path[len(split_path) - 2] + "_" + algorithm
                split_path[len(split_path) - 3] = "compressedEvents"
                split_path[0] = split_path[0] + "\\"
                compressed_file_path = os.path.join(*split_path)

                # Read compressed file
                compressed_file = loadFile(compressed_file_path)

                # Call to compressedFileToSpikesFile function
                header, spikes_file, final_address_size, final_timestamp_size = compressedFileToSpikesFile(compressed_file)

                # Call to spikesFileToCompressedFile function
                new_compressed_file = spikesFileToCompressedFile(spikes_file, final_address_size, final_timestamp_size,
                                                                 header.address_size, header.timestamp_size, algorithm,
                                                                 verbose=False)

                # Compare compressed_files
                self.assertIsNot(compressed_file, new_compressed_file)
                self.assertEqual(compressed_file, new_compressed_file)

                # Call to compressedFileToSpikesFile function
                new_header, new_spikes_file, new_final_address_size, new_final_timestamp_size = extractDataFromCompressedFile(compressed_file_path, verbose=False)

                # Comparing header, address_size and timestamp_size
                self.assertEqual(header.__dict__, new_header.__dict__)
                self.assertEqual(final_address_size, new_final_address_size)
                self.assertEqual(final_timestamp_size, new_final_timestamp_size)

                # Compare original and final spikes_file
                self.assertIsNot(spikes_file, new_spikes_file)

                spikes_file_dict = copy.deepcopy(spikes_file).__dict__
                spikes_file_dict.pop("addresses")
                spikes_file_dict.pop("timestamps")

                new_spikes_file_dict = copy.deepcopy(new_spikes_file).__dict__
                new_spikes_file_dict.pop("addresses")
                new_spikes_file_dict.pop("timestamps")

                self.assertEqual(spikes_file_dict, new_spikes_file_dict)
                for j in range(len(spikes_file.addresses)):
                    self.assertEqual(spikes_file.addresses[j], new_spikes_file.addresses[j])
                for k in range(len(spikes_file.timestamps)):
                    self.assertEqual(spikes_file.timestamps[k], new_spikes_file.timestamps[k])

    def test_getCompressedFile(self):
        for algorithm in self.compression_algorithms:
            # Define initial objects
            header = CompressedFileHeader(algorithm, 3, 4)
            data = "This is a text".encode("utf-8")

            # Get the compressed file bytearray
            compressed_file = getCompressedFile(header, data)

            # Extract data from the compressed_file and decompress it
            new_header, compressed_data = extractCompressedData(compressed_file)
            decompressed_data = decompressData(compressed_data, new_header.compressor, verbose=False)

            # Compare objects
            self.assertIsNot(header, new_header)
            self.assertEqual(header.__dict__, new_header.__dict__)
            self.assertEqual(data, decompressed_data)

    def test_checkCompressedFileExists(self):
        initial_file_path = "events/dataset/enun_stereo_64ch_ONOFF_addr4b_ts1.aedat"
        initial_file_path_split = initial_file_path.split(".")
        final_file_path = checkFileExists(initial_file_path)

        self.assertEqual(final_file_path, initial_file_path_split[0] + "(" + str(3) + ")." +
                         initial_file_path_split[1])  # Enter 'N' as input value


if __name__ == '__main__':
    unittest.main(verbosity=2)
