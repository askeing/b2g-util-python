#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import re
import os
import json
import logging
import argparse
from argparse import ArgumentDefaultsHelpFormatter
from util.adb_helper import AdbHelper
from util.adb_helper import AdbWrapper

logger = logging.getLogger(__name__)


class CrashReporter(object):
    """
    Get the Crash Reports from Firefox OS Phone.
    """

    def __init__(self):
        self.pending_path = '/data/b2g/mozilla/Crash Reports/pending'
        self.submitted_path = '/data/b2g/mozilla/Crash Reports/submitted'
        self.pending_stdout = None
        self.submitted_stdout = None
        self.pending_files = []
        self.submitted_files = []
        self.submitted_url_list = []
        self.serial = None
        self.log_json = None

    def set_serial(self, serial):
        """
        Setup the serial number.
        @param serial: the given serial number.
        """
        self.serial = serial
        logger.debug('Set serial: {}'.format(self.serial))

    def set_log_json(self, log_json):
        """
        Setup the log_json file path.
        @param log_json: the outpupt json file path.
        """
        self.log_json = log_json
        logger.debug('Set log_json: {}'.format(self.log_json))

    def cli(self):
        """
        Handle the argument parse, and the return the instance itself.
        """
        # argument parser
        arg_parser = argparse.ArgumentParser(description='Get the Crash Reports from Firefox OS Phone.',
                                             formatter_class=ArgumentDefaultsHelpFormatter)
        arg_parser.add_argument('-s', '--serial', action='store', dest='serial', default=None,
                                help='Directs command to the device or emulator with the given serial number. '
                                     'Overrides ANDROID_SERIAL environment variable.')
        arg_parser.add_argument('--log-json', action='store', dest='log_json', default=None, help='JSON ouptut.')
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
        # assign variable
        self.set_serial(args.serial)
        self.set_log_json(args.log_json)
        # return instance
        return self

    def get_crashreports(self, serial=None):
        """
        Print the pending and submitted crash reports on device.

        The submitted crashs report will be displayed with URL link.

        @param serial: device serial number. (optional)
        """
        AdbWrapper.adb_root(serial=serial)
        logger.info('Getting Crash Reports...')

        self.pending_stdout, retcode_pending = AdbWrapper.adb_shell('ls -al "{}"'.format(self.pending_path),
                                                             serial=serial)
        print('Pending Crash Reports:\n{}\n'.format(self.pending_stdout))

        self.submitted_stdout, retcode_submitted = AdbWrapper.adb_shell('ls -al "{}"'.format(self.submitted_path),
                                                                 serial=serial)
        print('Submitted Crash Reports:\n{}\n'.format(self.submitted_stdout))
        # parse stdout for getting filepath
        self.pending_files = self._parse_stdout(self.pending_path, self.pending_stdout)
        self.submitted_files = self._parse_stdout(self.submitted_path, self.submitted_stdout)

        self.submitted_url_list = []
        if retcode_submitted == 0:
            print('The links of Submitted Crash Reports:')
            for line in self.submitted_stdout.split('\n'):
                submmited_id = re.sub(r'\.txt\s*$', '', re.sub(r'^.+bp-', '', line))
                submitted_url = 'https://crash-stats.mozilla.com/report/index/{}'.format(submmited_id)
                self.submitted_url_list.append(submitted_url)
                print(submitted_url)

    def _parse_stdout(self, base_path='', stdout=''):
        if not stdout or 'No such file or directory' in stdout:
            return []
        else:
            result = []
            lines = stdout.replace('\r', '').split('\n')
            for line in lines:
                path = os.path.join(base_path, line.rsplit(' ', 1)[1])
                result.append(path)
                logger.debug('parse: {} to {}'.format(line, path))
            return result

    def get_crashreports_info_dict(self):
        """
        Get the Crash Reports information dict.
        @return: the list of Submitted URL.
        """
        return {'PendingCrashReportsStdout': self.pending_stdout,
                'SubmittedCrashReportsStdout': self.submitted_stdout,
                'PendingCrashReports': self.pending_files,
                'SubmittedCrashReports': self.submitted_files,
                'SubmittedUrl': self.submitted_url_list}

    def output_log(self):
        if self.log_json:
            with open(self.log_json, 'w') as f:
                result = self.get_crashreports_info_dict()
                json.dump(result, f, indent=4)

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
                    self.get_crashreports(serial=final_serial)
                else:
                    logger.debug('No serial, but there are more than one device')
                    raise Exception('Please specify the device by --serial option.')
            else:
                print('Serial: {0} (State: {1})'.format(final_serial, devices[final_serial]))
                self.get_crashreports(serial=final_serial)
            self.output_log()


def main():
    try:
        CrashReporter().cli().run()
    except Exception as e:
        logger.error(e)
        exit(1)


if __name__ == '__main__':
    main()
