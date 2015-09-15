# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os
import re
import logging
import threading
import subprocess
from distutils import spawn


logger = logging.getLogger(__name__)


class AdbWrapper(object):

    @classmethod
    def check_adb(cls):
        """
        Check the ADB command.
        @return: True if your system have ADB command.
        @raise exception: There is no ADB command in your system.
        """
        logger.debug('Checking ADB...')
        if spawn.find_executable('adb') is None:
            raise Exception('There is no "adb" in your environment PATH.')
        logger.debug('You have ADB.')
        return True

    @classmethod
    def adb_devices(cls):
        """
        Get the device list.
        @return: devices as dict {device_serial: device_status, ...}.
        @raise exception: When return code isn't zero.
        """
        cmd = 'adb devices'
        p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        output, stderr = p.communicate()
        logger.debug('CMD: {0}'.format(cmd))
        logger.debug('RET: {0}'.format(output))
        if stderr:
            logger.debug('ERR: {0}'.format(stderr))
        if p.returncode is not 0:
            raise Exception('{}'.format({'STDOUT': output, 'STDERR': stderr}))
        output = re.sub(r'\r+', '', output)
        output_list = re.split(r'\n+', output)
        # remove '', '* daemon not running. starting it now on port xxx *', and '* daemon started successfully *'
        output_list = [item for item in output_list if item and not item.startswith('* daemon')]
        msg_filter = re.compile(r'(^List of devices attached\s*|^\s+$)')
        output_list = [i for i in output_list if not msg_filter.search(i)]
        output_list = [(re.split(r'\t', item)) for item in output_list if True]
        devices = {}
        for device in output_list:
            devices[device[0]] = device[1]
        return devices

    @classmethod
    def adb_pull(cls, source, dest, serial=None):
        """
        Pull files from device.
        @return: stdout of command.
        @raise exception: When return code isn't zero.
        """
        if serial is None:
            cmd = 'adb pull'
        else:
            cmd = 'adb -s %s pull' % (serial,)
        cmd = "%s '%s' '%s'" % (cmd, source, dest)
        p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        output, stderr = p.communicate()
        logger.debug('CMD: {0}'.format(cmd))
        logger.debug('RET: {0}'.format(output))
        if stderr:
            logger.debug('ERR: {0}'.format(stderr))
        if p.returncode is not 0:
            raise Exception('{}'.format({'STDOUT': output, 'STDERR': stderr}))
        return output

    @classmethod
    def adb_push(cls, source, dest, serial=None):
        """
        Push files into device.
        @return: stdout of command.
        @raise exception: when return code isn't zero.
        """
        if serial is None:
            cmd = 'adb push'
        else:
            cmd = 'adb -s %s push' % (serial,)
        cmd = "%s '%s' '%s'" % (cmd, source, dest)
        p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        output, stderr = p.communicate()
        logger.debug('CMD: {0}'.format(cmd))
        logger.debug('RET: {0}'.format(output))
        if stderr:
            logger.debug('ERR: {0}'.format(stderr))
        if p.returncode is not 0:
            raise Exception('{}'.format({'STDOUT': output, 'STDERR': stderr}))
        return output

    @classmethod
    def adb_shell(cls, command, serial=None):
        """
        Run command on device.
        @return: the stdout and return code (from device) of "adb shell" command. e.g. (stdout, retcode)
        @raise exception: When return code (from adb command) isn't zero.
        """
        if serial is None:
            cmd = 'adb shell'
        else:
            cmd = 'adb -s %s shell' % (serial,)
        # get returncode from device
        cmd = "%s '%s; echo $?'" % (cmd, command)
        p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        shell_ret, stderr = p.communicate()
        logger.debug('CMD: {0}'.format(cmd))
        logger.debug('RAW_RET: {0}'.format(shell_ret))
        if stderr:
            logger.debug('RAW_ERR: {0}'.format(stderr))
        if p.returncode is not 0:
            raise Exception('{}'.format({'STDOUT': shell_ret, 'STDERR': stderr}))
        # split the stdout and retcode (from device)
        shell_ret = re.sub(r'\s+$', '', shell_ret)
        shell_output = re.split(r'\s+(\d+$)', shell_ret, maxsplit=1)
        # when no stdout, set output to ''
        if len(shell_output) == 1:
            # only returncode, no stdout
            output = ''
            try:
                returncode = int(shell_output[0])
            except Exception as e:
                logger.debug(e)
                # some command will stop device with no returncode. e.g. adb shell reboot recovery
                returncode = 0
        else:
            # stdout with returncode
            output = shell_output[0]
            try:
                returncode = int(shell_output[1])
            except Exception as e:
                logger.debug(e)
                returncode = 0
        logger.debug('RET: {0}'.format(output))
        logger.debug('RET CODE: {0}'.format(returncode))
        return output, returncode

    @classmethod
    def adb_root(cls, serial=None):
        """
        Get the root permission of ADB.
        @return: True if adb already running as root. False if failed.
        """
        if serial is None:
            cmd = 'adb root'
        else:
            cmd = 'adb -s %s root' % (serial,)
        p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        output, stderr = p.communicate()
        logger.debug('CMD: {0}'.format(cmd))
        logger.debug('RET: {0}'.format(output))
        if stderr:
            logger.debug('ERR: {0}'.format(stderr))
        if p.returncode is 0 and ('cannot' not in output):
            if 'restarting' in output:
                import time
                time.sleep(1)
            logger.debug('adb root successed')
            logger.info('{}'.format(output))
            return True
        else:
            logger.debug('adb root failed')
            logger.warning('{}'.format(output))
            return False

    @classmethod
    def adb_remount(cls, serial=None):
        """
        Remounts the /system partition on the device read-write
        @return: True if succeeded. False if failed.
        """
        if serial is None:
            cmd = 'adb remount'
        else:
            cmd = 'adb -s %s remount' % (serial,)
        p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        output, stderr = p.communicate()
        logger.debug('CMD: {0}'.format(cmd))
        logger.debug('RET: {0}'.format(output))
        if stderr:
            logger.debug('ERR: {0}'.format(stderr))
        if p.returncode is 0:
            if 'remount succeeded' in output:
                logger.info('{}'.format(output))
                return True
            else:
                logger.warning('{}'.format(output))
                return False
        else:
            logger.debug('adb remount failed')
            raise Exception('{}'.format({'STDOUT': output, 'STDERR': stderr}))

    @classmethod
    def adb_wait_for_device(cls, timeout=60, serial=None):
        """
        block until device is online. (default timeout is 60 seconds)
        @param timeout: specify the timeout for the operation in seconds. Default is 60 seconds.
        @raise exception: when running for more than timeout seconds.
        """
        thread = None
        cls.p_wait_for_device = None

        def _wait_for_device():
            logger.info('Starting adb wait-for-device, timeout: {}, serial: {}'.format(timeout, serial))
            if serial is None:
                cmd = 'adb wait-for-device'
            else:
                cmd = 'adb -s %s wait-for-device' % (serial,)
            cls.p_wait_for_device = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            cls.p_wait_for_device.communicate()
        thread = threading.Thread(target=_wait_for_device)
        thread.start()
        thread.join(timeout)
        if thread.is_alive():
            logger.debug('Terminating wait-for-device process.')
            cls.p_wait_for_device.terminate()
            cls.p_wait_for_device = None
            raise Exception('adb wait-for-device timeout, timeout {}, serial: {}'.format(timeout, serial))
        return True


class AdbHelper(object):

    @classmethod
    def get_serial(cls, serial_number):
        """
        Input the serial number.
        This method will check with "ANDROID_SERIAL" environmental variable,
        and then return the serial number if the serial is avaiable.
        When serial number is not avaiable, return None.

        ex:
          - (serial O, ANDROID_SERIAL O) => serial
          - (serial O, ANDROID_SERIAL X) => serial
          - (serial X, ANDROID_SERIAL O) => ANDROID_SERIAL
          - (serial X, ANDROID_SERIAL X) => None

        @return: the serial number of device.
        @raise exception: if there is no device have the given serial number.
        """
        # return None if there are no serial and ANDROID_SERIAL
        final_serial_number = None
        # no serial then check ANDROID_SERIAL
        if serial_number is None or serial_number == '':
            if 'ANDROID_SERIAL' in os.environ:
                logger.debug('ANDROID_SERIAL={}'.format(os.environ.get('ANDROID_SERIAL')))
                final_serial_number = os.environ.get('ANDROID_SERIAL')
        else:
            final_serial_number = serial_number
            logger.debug('serial={}'.format(serial_number))
        # raise Exception if the serial is not in devices list
        if final_serial_number is not None:
            devices = AdbWrapper.adb_devices()
            logger.debug('Devices: {}'.format(devices))
            if final_serial_number not in devices:
                raise Exception('Can not found {} device in devices list {}.'.format(final_serial_number, devices))
        return final_serial_number
