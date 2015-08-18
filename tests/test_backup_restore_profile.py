# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import tempfile
import textwrap
import unittest

from b2g_util.backup_restore_profile import BackupRestoreHelper


class BackupResotreTester(unittest.TestCase):

    def setUp(self):
        self.app = BackupRestoreHelper()

    def test_compare_version(self):
        '''
        Test compare_version.
        '''
        # Backup 37.0_20150808, Device 37.0_20150801
        self.assertTrue(self.app.compare_version('37.0_20150808', '37.0_20150801'),
                        '37.0 = 37.0, should return True.')
        # Backup 34.0a1_20150808, Device 37.0_20150801
        self.assertTrue(self.app.compare_version('34.0a1_20150808', '37.0_20150801'),
                        '34.0 < 37.0, should return True.')
        # Backup 41.0a1_20150624160209/20150624160209, Device 42.0a1_20150803030210/20150803030210
        self.assertTrue(self.app.compare_version('41.0a1_20150624160209/20150624160209', '42.0a1_20150803030210/20150803030210'),
                        '41.0 < 42.0, should return True.')

        # Backup 37.0_20150801, Device 34.0a1_20150808
        with self.assertRaises(Exception) as cm:
            self.app.compare_version('37.0_20150801', '34.0a1_20150808')
        expected_msg = 'Backup Profile 37.0 > Device Profile 34.0'
        self.assertEqual(cm.exception.message, expected_msg,
                         'Error message should be [{}], not [{}].'.format(expected_msg, cm.exception.message))

        # Backup 42.0a1_20150803030210/20150803030210, Device 41.0a1_20150624160209/20150624160209
        with self.assertRaises(Exception) as cm:
            self.app.compare_version('42.0a1_20150803030210/20150803030210', '41.0a1_20150624160209/20150624160209')
        expected_msg = 'Backup Profile 42.0 > Device Profile 41.0'
        self.assertEqual(cm.exception.message, expected_msg,
                         'Error message should be [{}], not [{}].'.format(expected_msg, cm.exception.message))

    def test_get_profile_path(self):
        '''
        test get_profile_path
        '''
        # create fake file
        expected_path = 'foo.default'
        profile_contect = textwrap.dedent('''\
                                          [General]
                                          StartWithLastProfile=1

                                          [Profile0]
                                          Name=default
                                          IsRelative=1
                                          Path={}
                                          Default=1
                                          '''.format(expected_path))
        # test load settings
        with tempfile.NamedTemporaryFile(prefix='test_b2g_util_') as temp:
            temp.write(profile_contect)
            temp.flush()
            result = self.app.get_profile_path(temp.name)
            self.assertEqual(result, expected_path, 'Get [{}], expected [{}].'.format(result, expected_path))

        # test failed
        with self.assertRaises(Exception) as cm:
            with tempfile.NamedTemporaryFile(prefix='test_b2g_util_') as temp:
                result = self.app.get_profile_path(temp.name)

    def test_get_version_from_profile(self):
        '''
        test get_version_from_profile
        '''
        # create fake file
        expected_version = '42.0a1_20150803030210/20150803030210'
        compatibility_contect = textwrap.dedent('''\
                                          [Compatibility]
                                          LastVersion={}
                                          LastOSABI=Android_arm-eabi-gcc3
                                          LastPlatformDir=/system/b2g
                                          LastAppDir=/system/b2g
                                          '''.format(expected_version))
        # test load settings
        with tempfile.NamedTemporaryFile(prefix='test_b2g_util_') as temp:
            temp.write(compatibility_contect)
            temp.flush()
            result = self.app.get_version_from_profile(temp.name)
            self.assertEqual(result, expected_version, 'Get [{}], expected [{}].'.format(result, expected_version))

        # test failed
        with self.assertRaises(Exception) as cm:
            with tempfile.NamedTemporaryFile(prefix='test_b2g_util_') as temp:
                result = self.app.get_version_from_profile(temp.name)


if __name__ == '__main__':
    unittest.main()
