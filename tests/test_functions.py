import copy
import os
import unittest

import numpy as np
from pyNAVIS import MainSettings, Loaders

import AERzip
from AERzip.CompressedFileHeader import CompressedFileHeader
from AERzip.functions import loadCompressedFile, saveCompressedFile


class NewFunctionTests(unittest.TestCase):

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
        self.file_data = [
            (os.path.abspath("tests/events/dataset/enun_stereo_64ch_ONOFF_addr4b_ts1.aedat"), self.file_settings_stereo_64ch_4a_4t_ts1),
            (os.path.abspath("tests/events/dataset/130Hz_mono_64ch_ONOFF_addr2b_ts02.aedat"), self.file_settings_mono_64ch_2a_4t_ts02),
            (os.path.abspath("tests/events/dataset/523Hz_stereo_64ch_ONOFF_addr2b_ts02.aedat"), self.file_settings_stereo_64ch_2a_4t_ts02),
            (os.path.abspath("tests/events/dataset/sound_mono_32ch_ONOFF_addr2b_ts02.aedat"), self.file_settings_mono_32ch_2a_4t_ts02)
        ]
        self.spike_files = []
        for file_data in self.file_data:
            self.spike_files.append(Loaders.loadAEDAT(file_data[0], file_data[1]))

    def test_compressRealFile(self):
        print("--- Real test ---")

        for i in range(len(self.file_data)):
            addresses = self.spike_files[i].addresses
            timestamps = self.spike_files[i].timestamps
            timestamps = timestamps - min(timestamps)
            
            file_basename = os.path.basename(self.file_data[i][0]) 
            print("Processing file: " + file_basename)

            compressed_file_path = "tests/events/compressedEvents/" + file_basename.split(".")[0] + "_compressed.aerzip"
            saveCompressedFile(addresses, timestamps, compressed_file_path, overwrite=True, verbose=True)
            new_addresses, new_timestamps = loadCompressedFile(compressed_file_path, verbose=True)
            print("\n")

            # Ordering original arrays by addresses to compare with loaded arrays
            sort_idx = np.lexsort((timestamps, addresses))
            addresses = addresses[sort_idx]
            timestamps = timestamps[sort_idx]
            
            loaded_sort_idx = np.lexsort((new_timestamps, new_addresses))
            new_addresses = new_addresses[loaded_sort_idx]
            new_timestamps = new_timestamps[loaded_sort_idx]

            # Asserting equality
            self.assertEqual(len(new_addresses), len(addresses))
            self.assertEqual(len(new_timestamps), len(timestamps))
            self.assertTrue((new_addresses == addresses).all())
            self.assertTrue((new_timestamps == timestamps).all())

            # Cleaning up
            #os.remove(compressed_file_path)

    def test_compressIdealFile(self):
        print("--- Ideal test ---")
        addresses = np.random.randint(0, 2 ** 8, size=1000000, dtype=np.uint64)
        timestamps = np.random.randint(0, 2 ** 32, size=1000000, dtype=np.uint64)
        timestamps = timestamps - min(timestamps)

        file_name = "ideal_test.aerzip"
        saveCompressedFile(addresses, timestamps, "tests/events/compressedEvents/" + file_name, overwrite=True, verbose=True)
        new_addresses, new_timestamps = loadCompressedFile("tests/events/compressedEvents/" + file_name, verbose=True)

        # Ordering original arrays by addresses to compare with loaded arrays
        sort_idx = np.lexsort((timestamps, addresses))
        addresses = addresses[sort_idx]
        timestamps = timestamps[sort_idx]
        
        loaded_sort_idx = np.lexsort((new_timestamps, new_addresses))
        new_addresses = new_addresses[loaded_sort_idx]
        new_timestamps = new_timestamps[loaded_sort_idx]

        # Asserting equality
        self.assertEqual(len(new_addresses), len(addresses))
        self.assertEqual(len(new_timestamps), len(timestamps))
        self.assertTrue((new_addresses == addresses).all())
        self.assertTrue((new_timestamps == timestamps).all())
        #os.remove("tests/events/compressedEvents/" + file_name)
        
if __name__ == '__main__':
    unittest.main(verbosity=2)
