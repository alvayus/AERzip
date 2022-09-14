import unittest

from pyNAVIS import MainSettings, Loaders

from AERzip.CompressedFileHeader import CompressedFileHeader
from AERzip.conversionFunctions import calcBytesToPrune, spikesFileAsType, spikesFileToBytes, bytesToSpikesFile


class JAERSettingsTest(unittest.TestCase):

    def setUp(self):
        # jAER settings
        self.num_channels = 64
        self.mono_stereo = 1
        self.on_off_both = 1
        self.address_size = 4
        self.timestamp_size = 4

        # Number of samples for the SpikesFile
        self.num_spikes = 10

        # Create settings object
        self.settings = MainSettings(num_channels=self.num_channels, mono_stereo=self.mono_stereo, on_off_both=self.on_off_both,
                                     address_size=self.address_size, timestamp_size=self.timestamp_size, ts_tick=1,
                                     bin_size=10000)

        # Load a spikes file with 4-byte addresses (prunable to 1-byte addresses) and 4-byte timestamps (prunable to
        # 3 byte addresses)
        self.spikes_file = Loaders.loadAEDAT("enun_stereo_64ch_ONOFF_addr4b_ts1.aedat", self.settings)

        # Create header object (compression)
        self.header = calcBytesToPrune(self.spikes_file, self.settings)

    def check_spikes(self, output_options, bytes_data):
        start_index = 0
        end_index = output_options.address_size
        for n in range(0, self.num_spikes):
            address = int.from_bytes(bytes_data[start_index:end_index], "big")

            start_index = end_index
            end_index += output_options.timestamp_size
            timestamp = int.from_bytes(bytes_data[start_index:end_index], "big")

            self.assertEqual(address, self.spikes_file.addresses[n])
            self.assertEqual(timestamp, self.spikes_file.timestamps[n])

            start_index = end_index
            end_index += output_options.address_size

    def test_calcBytesToPrune(self):
        self.assertIsInstance(self.header, CompressedFileHeader)

        self.assertIsInstance(self.header.address_size, int)
        self.assertGreaterEqual(self.header.address_size, 0)
        self.assertLess(self.header.address_size, self.settings.num_channels * (self.settings.mono_stereo + 1) *
                        (self.settings.on_off_both + 1))

        self.assertIsInstance(self.header.timestamp_size, int)
        self.assertGreaterEqual(self.header.timestamp_size, 0)
        self.assertLess(self.header.timestamp_size, 256 * 256 * 256)

    def test_spikesFileAsType(self):
        """
        This test checks that there is no loss of information while using all the numbers of bytes greater than the minimum
        number of bytes to encode addresses or timestamps (between the minimum and 4).
        """
        for i in range(self.header.address_size, 5):
            for j in range(self.header.timestamp_size, 5):
                self.header.address_size = i
                self.header.timestamp_size = j

                bytes_data = spikesFileAsType(self.spikes_file, self.settings, self.header)

                self.check_spikes(self.header, bytes_data)

    def test_spikesFileToBytes(self):
        """
        This test checks that when we are not using LZMA compressor the returned bytearray contains values of 32 bits
        (and are also the same value as the original values).
        """
        # --- No compression ---
        bytes_data = spikesFileToBytes(self.spikes_file, self.settings, self.settings, False)

        self.assertEqual(self.settings.address_size, 4)
        self.assertEqual(self.settings.timestamp_size, 4)

        self.check_spikes(self.settings, bytes_data)

        # --- LZ4 ---
        self.header.compressor = "LZ4"

        bytes_data = spikesFileToBytes(self.spikes_file, self.settings, self.header, False)

        self.assertEqual(self.header.address_size, 4)
        self.assertEqual(self.header.timestamp_size, 4)

        self.check_spikes(self.header, bytes_data)

        # --- ZSTD ----
        self.header = calcBytesToPrune(self.spikes_file, self.settings)  # Update header because it has been previously modified
        self.header.compressor = "ZSTD"

        bytes_data = spikesFileToBytes(self.spikes_file, self.settings, self.header, False)

        self.assertEqual(self.header.address_size, 4)
        self.assertEqual(self.header.timestamp_size, 4)

        self.check_spikes(self.header, bytes_data)

        # --- LZMA ---
        self.header = calcBytesToPrune(self.spikes_file, self.settings)  # Update header because it has been previously modified
        self.header.compressor = "LZMA"

        # Save prune values
        address_size = self.header.address_size
        timestamp_size = self.header.timestamp_size

        bytes_data = spikesFileToBytes(self.spikes_file, self.settings, self.header, False)

        # Check prune values
        self.assertEqual(self.header.address_size, address_size)  # Check that the value has not been modified
        self.assertEqual(self.header.timestamp_size, timestamp_size)  # Check that the value has not been modified

        self.check_spikes(self.header, bytes_data)

    def test_bytesToSpikesFile(self):
        # --- LZ4 ---
        self.header.compressor = "LZ4"

        bytes_data = spikesFileToBytes(self.spikes_file, self.settings, self.header, False)
        new_spikes_file = bytesToSpikesFile(bytes_data, self.header, False)

        self.assertEqual(self.spikes_file.addresses.tolist(), new_spikes_file[0].addresses.tolist())
        self.assertEqual(self.spikes_file.timestamps.tolist(), new_spikes_file[0].timestamps.tolist())

        # --- ZSTD ---
        self.header = calcBytesToPrune(self.spikes_file, self.settings)  # Update header because it has been previously modified
        self.header.compressor = "ZSTD"

        bytes_data = spikesFileToBytes(self.spikes_file, self.settings, self.header, False)
        new_spikes_file = bytesToSpikesFile(bytes_data, self.header, False)

        self.assertEqual(self.spikes_file.addresses.tolist(), new_spikes_file[0].addresses.tolist())
        self.assertEqual(self.spikes_file.timestamps.tolist(), new_spikes_file[0].timestamps.tolist())

        # --- LZMA ---
        self.header = calcBytesToPrune(self.spikes_file, self.settings)  # Update header because it has been previously modified
        self.header.compressor = "LZMA"

        bytes_data = spikesFileToBytes(self.spikes_file, self.settings, self.header, False)
        new_spikes_file = bytesToSpikesFile(bytes_data, self.header, False)

        self.assertEqual(self.spikes_file.addresses.tolist(), new_spikes_file[0].addresses.tolist())
        self.assertEqual(self.spikes_file.timestamps.tolist(), new_spikes_file[0].timestamps.tolist())


if __name__ == '__main__':
    unittest.main(verbosity=2)
