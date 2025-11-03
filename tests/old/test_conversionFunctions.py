import copy
import unittest

from pyNAVIS import MainSettings, Loaders
from AERzip.conversionFunctions import calcRequiredBytes, spikesFileToBytes, bytesToSpikesFile


class JAERSettingsTest(unittest.TestCase):

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

    def test_spikesFileToBytesAndViceversa(self):
        for i in range(len(self.spikes_files)):
            spikes_file = self.spikes_files[i]
            file_settings = self.files_data[i][1]

            # Getting target sizes
            address_size, timestamp_size = calcRequiredBytes(spikes_file, file_settings)

            # spikes_file to raw bytes
            bytes_data = spikesFileToBytes(spikes_file, file_settings.address_size, file_settings.timestamp_size,
                                           address_size, timestamp_size, verbose=False)

            # Raw bytes to spikes_file
            new_spikes_file, _, _ = bytesToSpikesFile(bytes_data, address_size, timestamp_size, verbose=False)

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


if __name__ == '__main__':
    unittest.main(verbosity=2)
