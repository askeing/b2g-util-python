#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os
import logging
import argparse
from argparse import ArgumentDefaultsHelpFormatter
from util.adb_helper import AdbHelper
from util.adb_helper import AdbWrapper


logger = logging.getLogger(__name__)


class PhoneReseter(object):
    def __init__(self, **kwargs):
        self.arg_parser = argparse.ArgumentParser(description='Reset Firefox OS Phone.',
                                                  formatter_class=ArgumentDefaultsHelpFormatter)
        self.arg_parser.add_argument('-s', '--serial', action='store', dest='serial', default=None, help='Directs command to the device or emulator with the given serial number. Overrides ANDROID_SERIAL environment variable.')
        self.arg_parser.add_argument('-v', '--verbose', action='store_true', dest='verbose', default=False, help='Turn on verbose output, with all the debug logger.')
        self.args = self.arg_parser.parse_args()
        # setup the logging config
        if self.args.verbose is True:
            verbose_formatter = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            logging.basicConfig(level=logging.DEBUG, format=verbose_formatter)
        else:
            formatter = '%(levelname)s: %(message)s'
            logging.basicConfig(level=logging.INFO, format=formatter)
        self.check_adb()

    def check_adb(self):
        # check adb
        if not AdbWrapper.has_adb():
            raise Exception('There is no "adb" in your environment PATH.')

    def reset_phone(self, serial=None):
        # checking the adb root for backup/restore
        if not AdbWrapper.adb_root(serial=serial):
            raise Exception('No root permission for backup and resotre.')
        # starting to reset
        logger.info('Starting to Reset Firefox OS Phone...')
        AdbWrapper.adb_shell('rm -r /cache/*', serial=serial)
        AdbWrapper.adb_shell('mkdir /cache/recovery', serial=serial)
        AdbWrapper.adb_shell('echo "--wipe_data" > /cache/recovery/command', serial=serial)
        AdbWrapper.adb_shell('reboot recovery', serial=serial)
        logger.info('Reset Firefox OS Phone done.')

    def run(self):
        devices = AdbWrapper.adb_devices()

        if len(devices) == 0:
            raise Exception('No device.')
        elif len(devices) >= 1:
            final_serial = AdbHelper.get_serial(self.args.serial)
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
        PhoneReseter().run()
    except Exception as e:
        logger.error(e)
        exit(1)

if __name__ == '__main__':
    main()
