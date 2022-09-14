import unittest

from pyNAVIS import MainSettings, Loaders

from AERzip.CompressedFileHeader import CompressedFileHeader
from AERzip.conversionFunctions import calcBytesToPrune, spikesFileToBytes, bytesToSpikesFile


class JAERSettingsTest(unittest.TestCase):

    def setUp(self):
        # Create settings object
        self.file_settings = MainSettings(num_channels=64, mono_stereo=1, on_off_both=1, address_size=4,
                                          timestamp_size=4, ts_tick=1, bin_size=10000)

        # Loading a spikes_file
        self.file_path = "events/dataset/enun_stereo_64ch_ONOFF_addr4b_ts1.aedat"
        self.spikes_file = Loaders.loadAEDAT(self.file_path, self.file_settings)

        # Getting target sizes
        self.final_address_size, self.final_timestamp_size = calcBytesToPrune(self.spikes_file, self.file_settings)

    def test_spikesFileToBytesAndViceversa(self):
        # spikes_file to raw bytes
        bytes_data = spikesFileToBytes(self.spikes_file, self.file_settings, self.final_address_size, self.final_timestamp_size)

        # Raw bytes to spikes_file
        new_settings = self.file_settings
        new_settings.address_size = self.final_address_size
        new_settings.timestamp_size = self.final_timestamp_size

        spikes_file, _ = bytesToSpikesFile(bytes_data, new_settings)

        # Compare original and final spikes_file
        self.assertEqual(self.spikes_file.addresses.tolist(), spikes_file.addresses.tolist())
        self.assertEqual(self.spikes_file.timestamps.tolist(), spikes_file.timestamps.tolist())


if __name__ == '__main__':
    unittest.main(verbosity=2)
