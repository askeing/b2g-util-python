# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import tempfile
import textwrap
import unittest
import logging

from mock import patch, Mock

from b2g_util.util.adb_helper import AdbWrapper
from b2g_util.util.adb_helper import AdbHelper


class AdbWrapperTester(unittest.TestCase):

    def setUp(self):
        # setup mock object
        self.popen_patcher = patch('subprocess.Popen')
        self.mock_popen = self.popen_patcher.start()
        self.mock_obj = Mock()
        self.mock_obj.returncode = 0

    def test_no_device(self):
        '''
        Test no device.
        '''
        str_ret = 'List of devices attached\n\r'
        expected_ret = {}
        self.mock_obj.communicate.return_value = [str_ret, None]
        self.mock_popen.return_value = self.mock_obj
        devices = AdbWrapper.adb_devices()
        self.assertEqual(devices, expected_ret,
                         'The result should be {}, not {}.'.format(expected_ret, devices))

    def test_one_device(self):
        '''
        Test one device.
        '''
        str_ret = textwrap.dedent('''\
                                  List of devices attached
                                  foo\tbar''')
        expected_ret = {'foo': 'bar'}
        self.mock_obj.communicate.return_value = [str_ret, None]
        self.mock_popen.return_value = self.mock_obj
        devices = AdbWrapper.adb_devices()
        self.assertEqual(devices, expected_ret,
                         'The result should be {}, not {}.'.format(expected_ret, devices))

    def test_two_device(self):
        '''
        Test two device.
        '''
        str_ret = textwrap.dedent('''\
                                  List of devices attached
                                  foo\tbar
                                  askeing\tcool''')
        expected_ret = {'foo': 'bar', 'askeing': 'cool'}
        self.mock_obj.communicate.return_value = [str_ret, None]
        self.mock_popen.return_value = self.mock_obj
        devices = AdbWrapper.adb_devices()
        self.assertEqual(devices, expected_ret,
                         'The result should be {}, not {}.'.format(expected_ret, devices))

    def test_pull(self):
        '''
        Test pull.
        '''
        str_ret = '2 KB/s (104 bytes in 0.040s)'
        expected_ret = '2 KB/s (104 bytes in 0.040s)'
        self.mock_obj.communicate.return_value = [str_ret, None]
        self.mock_popen.return_value = self.mock_obj
        ret = AdbWrapper.adb_pull('/b2g/mozilla.test', '')
        self.assertEqual(ret, expected_ret,
                         'The result should be {}, not {}.'.format(expected_ret, ret))

    def test_pull_fail(self):
        '''
        Test pull fail.
        '''
        str_ret = 'remote object \'foo\' does not exist'
        with self.assertRaises(Exception) as cm:
            self.mock_obj.returncode = 1
            self.mock_obj.communicate.return_value = [str_ret, None]
            self.mock_popen.return_value = self.mock_obj
            ret = AdbWrapper.adb_pull('foo', '')

    def test_push(self):
        '''
        Test push.
        '''
        str_ret = '2 KB/s (104 bytes in 0.040s)'
        expected_ret = '2 KB/s (104 bytes in 0.040s)'
        self.mock_obj.communicate.return_value = [str_ret, None]
        self.mock_popen.return_value = self.mock_obj
        ret = AdbWrapper.adb_push('mozilla.test', '/b2g/mozilla.test')
        self.assertEqual(ret, expected_ret,
                         'The result should be {}, not {}.'.format(expected_ret, ret))

    def test_push_fail(self):
        '''
        Test push fail.
        '''
        str_ret = 'failed to copy \'foo\' to \'bar\': No such file or directory'
        with self.assertRaises(Exception) as cm:
            self.mock_obj.returncode = 1
            self.mock_obj.communicate.return_value = [str_ret, None]
            self.mock_popen.return_value = self.mock_obj
            ret = AdbWrapper.adb_push('foo', 'bar')

    def test_root(self):
        '''
        Test root.
        '''
        # test adb already running as root
        str_ret = 'adbd is already running as root'
        self.mock_obj.communicate.return_value = [str_ret, None]
        self.mock_popen.return_value = self.mock_obj
        ret = AdbWrapper.adb_root()
        self.assertTrue(ret, 'The result should be True')

        # test adb not running, then running as root
        str_ret = textwrap.dedent('''\
                                  * daemon not running. starting it now on port 5037 *
                                  * daemon started successfully *
                                  adbd is already running as root''')
        self.mock_obj.communicate.return_value = [str_ret, None]
        self.mock_popen.return_value = self.mock_obj
        ret = AdbWrapper.adb_root()
        self.assertTrue(ret, 'The result should be True.')

    def test_root_faile(self):
        '''
        Test root fail.
        '''
        str_ret = 'adbd cannot run as root in production builds'
        self.mock_obj.communicate.return_value = [str_ret, None]
        self.mock_popen.return_value = self.mock_obj
        ret = AdbWrapper.adb_root()
        self.assertFalse(ret, 'The result should be False.')

    def test_shell(self):
        '''
        Test shell.
        '''
        # test running command and the command success (retcode 0)
        str_ret = textwrap.dedent('''\
                                  test_result
                                  0''')
        expected_ret = 'test_result'
        excepted_retcode = 0
        self.mock_obj.communicate.return_value = [str_ret, None]
        self.mock_popen.return_value = self.mock_obj
        ret, retcode = AdbWrapper.adb_shell('b2g-test')
        self.assertEqual(ret, expected_ret,
                         'The result should be {}, not {}.'.format(expected_ret, ret))
        self.assertEqual(retcode, excepted_retcode,
                         'The return code should be {}, not {}.'.format(excepted_retcode, retcode))

        # test running command and the command failed (retcode 1)
        str_ret = textwrap.dedent('''\
                                  test_result
                                  1''')
        expected_ret = 'test_result'
        not_excepted_retcode = 0
        self.mock_obj.communicate.return_value = [str_ret, None]
        self.mock_popen.return_value = self.mock_obj
        ret, retcode = AdbWrapper.adb_shell('b2g-test')
        self.assertEqual(ret, expected_ret,
                         'The result should be {}, not {}.'.format(expected_ret, ret))
        self.assertNotEqual(retcode, not_excepted_retcode,
                         'The return code cannot be {}, but it is.'.format(not_excepted_retcode))

    def test_shell_fail(self):
        '''
        Test shell fail.
        '''
        str_ret = 'error: device not found'
        with self.assertRaises(Exception) as cm:
            self.mock_obj.returncode = 1
            self.mock_obj.communicate.return_value = [str_ret, None]
            self.mock_popen.return_value = self.mock_obj
            ret = AdbWrapper.adb_shell('foo')

    def tearDown(self):
        # stop
        self.popen_patcher.stop()


if __name__ == '__main__':
    unittest.main()
