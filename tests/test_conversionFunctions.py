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
            final_address_size, final_timestamp_size = calcRequiredBytes(spikes_file, file_settings)

            # spikes_file to raw bytes
            bytes_data = spikesFileToBytes(spikes_file, file_settings, final_address_size, final_timestamp_size,
                                           verbose=False)

            # Raw bytes to spikes_file
            compressed_settings = copy.deepcopy(file_settings)
            compressed_settings.address_size = final_address_size
            compressed_settings.timestamp_size = final_timestamp_size

            new_spikes_file, _ = bytesToSpikesFile(bytes_data, compressed_settings, verbose=False)

            # Compare original and final spikes_file
            self.assertIsNot(spikes_file, new_spikes_file)
            self.assertEqual(spikes_file.addresses.tolist(), new_spikes_file.addresses.tolist())
            self.assertEqual(spikes_file.timestamps.tolist(), new_spikes_file.timestamps.tolist())
            self.assertEqual(spikes_file.max_ts, new_spikes_file.max_ts)
            self.assertEqual(spikes_file.min_ts, new_spikes_file.min_ts)
            self.assertEqual(spikes_file.max_ts_index, new_spikes_file.max_ts_index)
            self.assertEqual(spikes_file.min_ts_index, new_spikes_file.min_ts_index)


if __name__ == '__main__':
    unittest.main(verbosity=2)
