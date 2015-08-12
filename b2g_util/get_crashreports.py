#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os
import re
import logging
import argparse
from argparse import ArgumentDefaultsHelpFormatter
from util.adb_helper import AdbHelper
from util.adb_helper import AdbWrapper


logger = logging.getLogger(__name__)


class CrashReporter(object):
    def __init__(self, **kwargs):
        self.arg_parser = argparse.ArgumentParser(description='Get the Crash Reports from Firefox OS Phone.',
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
        AdbWrapper.check_adb()

    def get_crashreports(self, serial=None):
        AdbWrapper.adb_root(serial=serial)
        logger.info('Getting Crash Reports...')

        pending, retcode_pending = AdbWrapper.adb_shell('ls -al /data/b2g/mozilla/Crash\ Reports/pending', serial=serial)
        print('Pending Crash Reports:\n{}\n'.format(pending))

        submitted, retcode_submitted = AdbWrapper.adb_shell('ls -al /data/b2g/mozilla/Crash\ Reports/submitted', serial=serial)
        print('Submitted Crash Reports:\n{}\n'.format(submitted))

        if retcode_submitted == 0:
            print('The links of Submitted Crash Reports:')
            for line in submitted.split('\n'):
                submmited_id = re.sub(r'\.txt\s*$', '', re.sub(r'^.+bp-', '', line))
                submitted_url = 'https://crash-stats.mozilla.com/report/index/{}'.format(submmited_id)
                print(submitted_url)

    def run(self):
        devices = AdbWrapper.adb_devices()

        if len(devices) == 0:
            raise Exception('No device.')
        elif len(devices) >= 1:
            final_serial = AdbHelper.get_serial(self.args.serial)
            if final_serial is None:
                if len(devices) == 1:
                    logger.debug('No serial, and only one device')
                    self.get_crashreports(serial=final_serial)
                else:
                    logger.debug('No serial, but there are more than one device')
                    raise Exception('Please specify the device by --serial option.')
            else:
                print('Serial: {0} (State: {1})'.format(final_serial, devices[final_serial]))
                self.get_crashreports(serial=final_serial)


def main():
    try:
        CrashReporter().run()
    except Exception as e:
        logger.error(e)
        exit(1)


if __name__ == '__main__':
    main()
