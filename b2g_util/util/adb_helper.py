# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os
import re
import logging
import subprocess
from distutils import spawn


logger = logging.getLogger(__name__)


class AdbWrapper(object):

    @staticmethod
    def has_adb():
        if spawn.find_executable('adb') == None:
            return False
        return True

    @staticmethod
    def adb_devices():
        cmd = 'adb devices'
        p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        output = p.communicate()[0]
        logger.debug('CMD: {0}'.format(cmd))
        logger.debug('RET: {0}'.format(output))
        output = re.sub(r'\r+', '', output)
        output_list = re.split(r'\n+', output)
        # remove '', '* daemon not running. starting it now on port xxx *', and '* daemon started successfully *'
        output_list = [item for item in output_list if item and not item.startswith('* daemon')]
        filter = re.compile(r'(^List of devices attached\s*|^\s+$)')
        output_list = [i for i in output_list if not filter.search(i)]
        output_list = [(re.split(r'\t', item)) for item in output_list if True]
        devices = {}
        for device in output_list:
            devices[device[0]] = device[1]
        return devices

    @staticmethod
    def adb_pull(source, dest, serial=None):
        if serial is None:
            cmd = 'adb pull'
        else:
            cmd = 'adb -s %s pull' % (serial,)
        cmd = '%s %s %s' % (cmd, source, dest)
        p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        output = p.communicate()[0]
        logger.debug('CMD: {0}'.format(cmd))
        logger.debug('RET: {0}'.format(output))
        if p.returncode is not 0:
            return False
        else:
            return True

    @staticmethod
    def adb_push(source, dest, serial=None):
        if serial is None:
            cmd = 'adb push'
        else:
            cmd = 'adb -s %s push' % (serial,)
        cmd = '%s %s %s' % (cmd, source, dest)
        p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        output = p.communicate()[0]
        logger.debug('CMD: {0}'.format(cmd))
        logger.debug('RET: {0}'.format(output))
        if p.returncode is not 0:
            return False
        else:
            return True

    @staticmethod
    def adb_shell(command, serial=None):
        if serial is None:
            cmd = 'adb shell'
        else:
            cmd = 'adb -s %s shell' % (serial,)
        cmd = "%s '%s'" % (cmd, command)
        p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        output = p.communicate()[0]
        logger.debug('CMD: {0}'.format(cmd))
        logger.debug('RET: {0}'.format(output))
        return output

    @staticmethod
    def adb_root(serial=None):
        if serial is None:
            cmd = 'adb root'
        else:
            cmd = 'adb -s %s root' % (serial,)
        p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        output = p.communicate()[0]
        logger.debug('cmd: {0}'.format(cmd))
        logger.debug('output: {0}'.format(output))
        if p.returncode is 0 and (not 'cannot' in output):
            logger.debug('adb root successed')
            logger.info('{}'.format(output))
            return True
        else:
            logger.debug('adb root failed')
            logger.warning('{}'.format(output))
            return False


class AdbHelper(object):

    @staticmethod
    def get_serial(serial_number):
        '''
        Input the serial number.
        This method will check with "ANDROID_SERIAL" environmental variable, then return the serial number if the serial is avaiable.
        When serial number is not avaiable, return None.
        ex:
            \ANDROID_SERIAL
        serial\ |  O  |  X
        --------+-----+------
              O |  s  |  s
        --------+-----+------
              X | A_S | None
        '''
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
            if not final_serial_number in devices:
                raise Exception('Can not found {} device in devices list {}.'.format(final_serial_number, devices))
        return final_serial_number
