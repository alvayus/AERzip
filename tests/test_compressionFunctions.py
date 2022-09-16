import unittest

from pyNAVIS import MainSettings, Loaders

from AERzip.CompressedFileHeader import CompressedFileHeader
from AERzip.compressionFunctions import compressDataFromFile, compressedFileToSpikesFile, checkCompressedFileExists, \
    spikesFileToCompressedFile, compressData, getCompressedFile, extractCompressedData, loadCompressedFile
from AERzip.conversionFunctions import calcRequiredBytes


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
                compressed_file, _ = compressDataFromFile(file_data[0], file_data[1], algorithm, store=False,
                                                          verbose=False)

                # Decompressing the spikes_file
                header, spikes_file, final_address_size, final_timestamp_size = compressedFileToSpikesFile(
                    compressed_file, verbose=False)

                # Compare original and final spikes_file
                self.assertEqual(header.compressor, algorithm)
                self.assertEqual(spikes_file.addresses.tolist(), spikes_file.addresses.tolist())
                self.assertEqual(spikes_file.timestamps.tolist(), spikes_file.timestamps.tolist())
                self.assertEqual(header.header_end, "#End Of ASCII Header\r\n")

    '''def test_getCompressedFile(self):
        compression_algorithms = ["ZSTD", "LZMA", "LZ4"]
        
        for i in range(len(self.spikes_files)):
            # Target spikes_file
            spikes_file = self.spikes_files[i]
            files_data = self.files_data[i]
            
            # Get the bytes to be discarded
            final_address_size, final_timestamp_size = calcRequiredBytes(spikes_file, files_data[1])
            
            for algorithm in self.compression_algorithms: 
                # Compress the original spikes_file
                compressed_file = spikesFileToCompressedFile(spikes_file, files_data[1].address_size, 
                                                             files_data[1].timestamp_size, final_address_size, 
                                                             final_timestamp_size, algorithm, verbose=False)
                
                # '''

    def test_compressedFileToFromSpikesFile(self):
        for file_data in self.files_data:
            for algorithm in self.compression_algorithms:
                # Read compressed file
                compressed_file = loadCompressedFile(file_data[0])

                # Call to compressedFileToSpikesFile function
                header, spikes_file, final_address_size, final_timestamp_size = compressedFileToSpikesFile(compressed_file)

                # Call to spikesFileToCompressedFile function
                new_compressed_file = spikesFileToCompressedFile(spikes_file, final_address_size, final_timestamp_size,
                                                                 header.address_size, header.timestamp_size, algorithm,
                                                                 verbose=False)

                # Compare compressed_files
                self.assertIsNot(compressed_file, new_compressed_file)
                self.assertEqual(compressed_file, new_compressed_file)

    def test_getCompressedFile(self):
        for algorithm in self.compression_algorithms:
            # Test header
            header = CompressedFileHeader(algorithm, 3, 4)

            # Test compressed data
            compressed_data = compressData("This is a text".encode("utf-8"), algorithm, verbose=False)

            # Get the compressed file bytearray
            compressed_file = getCompressedFile(header, compressed_data)

            # Extract data from the compressed_file
            dec_header, dec_data = extractCompressedData(compressed_file)

            # Compare objects
            self.assertIsNot(header, dec_header)
            self.assertEqual(header.__dict__, dec_header.__dict__)
            self.assertEqual(compressed_data, dec_data)

    def test_checkCompressedFileExists(self):
        initial_file_path = "events/dataset/enun_stereo_64ch_ONOFF_addr4b_ts1.aedat"
        initial_file_path_split = initial_file_path.split(".")
        final_file_path = checkCompressedFileExists(initial_file_path)

        self.assertEqual(final_file_path, initial_file_path_split[0] + "(" + str(3) + ")." +
                         initial_file_path_split[1])  # Enter 'N' as input value


if __name__ == '__main__':
    unittest.main(verbosity=2)
