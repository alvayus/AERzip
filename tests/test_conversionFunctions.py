import unittest

import numpy as np
from pyNAVIS import MainSettings, SpikesFile, Functions

from AERzip.CompressedFileHeader import CompressedFileHeader
from AERzip.conversionFunctions import calcBytesToPrune, spikesFileAsType


class JAERSettingsTest(unittest.TestCase):

    def setUp(self):
        # jAER settings
        self.num_channels = 64
        self.mono_stereo = 1
        self.on_off_both = 1
        self.address_size = 4
        self.timestamp_size = 4

        # Number of samples for the SpikesFile
        self.num_samples = 10

        # Create settings object
        self.settings = MainSettings(num_channels=self.num_channels, mono_stereo=self.mono_stereo, on_off_both=self.on_off_both,
                                     address_size=self.address_size, timestamp_size=self.timestamp_size, ts_tick=1,
                                     bin_size=10000)

        # Create spikes file with 4-byte addresses (prunable to 1-byte addresses) and 4-byte timestamps (prunable to
        # 3 byte addresses)
        self.spikes_file = SpikesFile(np.random.randint(0, self.num_channels * (self.mono_stereo + 1) * (self.on_off_both + 1),
                                                        self.num_samples),
                                      np.random.randint(0, 256 * 256 * 256, self.num_samples))
        Functions.order_SpikesFile(self.spikes_file, self.settings)

        # Create header object (compression)
        self.header = calcBytesToPrune(self.spikes_file, self.settings)

    def test_calcBytesToPruneTest(self):
        self.assertIsInstance(self.header, CompressedFileHeader)

        self.assertIsInstance(self.header.address_size, int)
        self.assertGreaterEqual(self.header.address_size, 0)
        self.assertLess(self.header.address_size, self.settings.num_channels * (self.settings.mono_stereo + 1) *
                        (self.settings.on_off_both + 1))

        self.assertIsInstance(self.header.timestamp_size, int)
        self.assertGreaterEqual(self.header.timestamp_size, 0)
        self.assertLess(self.header.timestamp_size, 256 * 256 * 256)

    def test_spikesFileAsTypeTest(self):
        self.header.timestamp_size = 4
        self.header.timestamp_size = 4

        bytes_data = spikesFileAsType(self.spikes_file, self.settings, self.header)

        start_index = 2
        end_index = 2 + self.header.address_size
        for i in range(0, self.num_samples):
            address = int.from_bytes(bytes_data[start_index:end_index], "big")

            start_index = end_index
            end_index += self.header.timestamp_size
            timestamp = int.from_bytes(bytes_data[start_index:end_index], "big")

            self.assertEqual(address, self.spikes_file.addresses[i])
            self.assertEqual(timestamp, self.spikes_file.timestamps[i])

            start_index = end_index
            end_index += self.header.address_size


if __name__ == '__main__':
    unittest.main(verbosity=2)
