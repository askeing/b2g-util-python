#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import logging
import argparse
from argparse import ArgumentDefaultsHelpFormatter
from util.adb_helper import AdbHelper
from util.adb_helper import AdbWrapper

logger = logging.getLogger(__name__)


class PhoneReseter(object):
    """
    Reset Firefox OS Phone.
    """

    def __init__(self):
        self.serial = None

    def set_serial(self, serial):
        """
        Setup the serial number.
        @param serial: the given serial number.
        """
        self.serial = serial
        logger.debug('Set serial: {}'.format(self.serial))

    def cli(self):
        """
        Handle the argument parse, and the return the instance itself.
        """
        # argument parser
        arg_parser = argparse.ArgumentParser(description='Reset Firefox OS Phone.',
                                             formatter_class=ArgumentDefaultsHelpFormatter)
        arg_parser.add_argument('-s', '--serial', action='store', dest='serial', default=None,
                                help='Directs command to the device or emulator with the given serial number.'
                                     'Overrides ANDROID_SERIAL environment variable.')
        arg_parser.add_argument('-v', '--verbose', action='store_true', dest='verbose', default=False,
                                help='Turn on verbose output, with all the debug logger.')

        # parse args and setup the logging
        args = arg_parser.parse_args()
        # setup the logging config
        if args.verbose is True:
            verbose_formatter = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            logging.basicConfig(level=logging.DEBUG, format=verbose_formatter)
        else:
            formatter = '%(levelname)s: %(message)s'
            logging.basicConfig(level=logging.INFO, format=formatter)
        # check ADB
        AdbWrapper.check_adb()
        # assign the variable
        self.set_serial(args.serial)
        # return instance
        return self

    @staticmethod
    def reset_phone(serial=None):
        """
        Reset the B2G device.
        @param serial: device serial number. (optional)
        @raise exception: When no root permission for reset device.
        """
        # checking the adb root for backup/restore
        if not AdbWrapper.adb_root(serial=serial):
            raise Exception('No root permission for reset device.')
        # starting to reset
        logger.info('Starting to Reset Firefox OS Phone...')
        AdbWrapper.adb_shell('rm -r /cache/*', serial=serial)
        AdbWrapper.adb_shell('mkdir /cache/recovery', serial=serial)
        AdbWrapper.adb_shell('echo "--wipe_data" > /cache/recovery/command', serial=serial)
        AdbWrapper.adb_shell('reboot recovery', serial=serial)
        logger.info('Reset Firefox OS Phone done.')

    def run(self):
        """
        Entry point.
        """
        devices = AdbWrapper.adb_devices()

        if len(devices) == 0:
            raise Exception('No device.')
        elif len(devices) >= 1:
            final_serial = AdbHelper.get_serial(self.serial)
            if final_serial is None:
                if len(devices) == 1:
                    logger.debug('No serial, and only one device')
                    self.reset_phone(serial=final_serial)
                else:
                    logger.debug('No serial, but there are more than one device')
                    raise Exception('Please specify the device by --serial option.')
            else:
                print('Serial: {0} (State: {1})'.format(final_serial, devices[final_serial]))
                self.reset_phone(serial=final_serial)


def main():
    try:
        PhoneReseter().cli().run()
    except Exception as e:
        logger.error(e)
        exit(1)


if __name__ == '__main__':
    main()
