#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os
import re
import shutil
import logging
import argparse
import tempfile
import textwrap
from argparse import RawTextHelpFormatter
from argparse import ArgumentDefaultsHelpFormatter
from util.adb_helper import AdbHelper
from util.adb_helper import AdbWrapper
from util.b2g_helper import B2GHelper


logger = logging.getLogger(__name__)


class FullPrivilegeResetter(object):
    def __init__(self, **kwargs):
        self.arg_parser = argparse.ArgumentParser(description='Enable Certified Apps Debugging.',
                                                  formatter_class=RawTextHelpFormatter,
                                                  epilog=textwrap.dedent('''\
                                                  Please enable "ADB and Devtools" of device.
                                                  Ref:
                                                  - https://developer.mozilla.org/en-US/docs/Tools/WebIDE
                                                  - https://developer.mozilla.org/en-US/docs/Tools/WebIDE/Running_and_debugging_apps#Debugging_apps
                                                  '''))
        self.arg_parser.add_argument('-s', '--serial', action='store', dest='serial', default=None,
                                     help=textwrap.dedent('''\
                                     Directs command to the device or emulator with the
                                     given serial number. Overrides ANDROID_SERIAL
                                     environment variable. (default: %(default)s)
                                     '''))
        self.arg_parser.add_argument('--disable', action='store_true', dest='disable', default=False, help='Disable the privileges. (default: %(default)s)')
        self.arg_parser.add_argument('-v', '--verbose', action='store_true', dest='verbose', default=False,
                                     help=textwrap.dedent('''\
                                     Turn on verbose output, with all the debug logger.
                                     (default: %(default)s)
                                     '''))
        self.args = self.arg_parser.parse_args()
        # setup the logging config
        if self.args.verbose is True:
            verbose_formatter = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            logging.basicConfig(level=logging.DEBUG, format=verbose_formatter)
        else:
            formatter = '%(levelname)s: %(message)s'
            logging.basicConfig(level=logging.INFO, format=formatter)
        AdbWrapper.check_adb()

    def set_certapps(self, enable=True, serial=None):
        AdbWrapper.adb_root(serial=serial)
        logger.info('{} Full Privilege for WebIDE...'.format('Enabling' if enable else 'Disabling'))

        need_restart = True
        try:
            tmp_dir = tempfile.mkdtemp(prefix='enablecertapps_')
            # get profile folder name xxx.default under /data/b2g/mozilla/
            profile_dir_name, retcode = AdbWrapper.adb_shell('ls /data/b2g/mozilla/ | grep default', serial=serial)
            device_src_file = os.path.join('/data/b2g/mozilla/', profile_dir_name, 'prefs.js')
            dest_temp_file = os.path.join(tmp_dir, 'prefs.js.origin')
            try:
                logger.info('Pulling prefs.js file...')
                AdbWrapper.adb_pull(device_src_file, dest_temp_file, serial=serial)
            except:
                raise Exception('Error pulling prefs.js file.')

            dest_file = os.path.join(tmp_dir, 'prefs.js')
            with open(dest_temp_file, 'r') as fr:
                with open(dest_file, 'w') as fw:
                    match = False
                    is_forbid = 'false' if enable else 'true'
                    logger.debug('is_forbid: [{}]'.format(is_forbid))
                    for line in fr:
                        if 'devtools.debugger.forbid-certified-apps' in line:
                            logger.debug('line: [{}] to [{}]'.format(line, is_forbid))
                            if is_forbid in line:
                                # do not need to restart if the setting isn't changed
                                logger.info('The full privilege is already {}.'.format('enabled' if enable else 'disabled'))
                                need_restart = False
                                break
                            else:
                                logger.info('Changing setting of pref.js file...')
                                fw.write('user_pref("devtools.debugger.forbid-certified-apps", {});\n'.format(is_forbid))
                            match = True
                        else:
                            fw.write(line)
                    if not match:
                        if not enable:
                            # the forbid is true when there is no setting
                            logger.info('The full privilege is already disabled.')
                            need_restart = False
                        else:
                            # adding setting when there is no setting and need to enable certapps
                            logger.info('Adding setting of pref.js file...')
                            fw.write('user_pref("devtools.debugger.forbid-certified-apps", {});\n'.format(is_forbid))
            if need_restart:
                try:
                    logger.info('Pushing prefs.js file...')
                    AdbWrapper.adb_push(dest_file, device_src_file, serial=serial)
                except:
                    raise Exception('Error pushing prefs.js file.')
        finally:
            if need_restart:
                B2GHelper.stop_b2g(serial=serial)
                B2GHelper.start_b2g(serial=serial)
            shutil.rmtree(tmp_dir)

    def run(self):
        devices = AdbWrapper.adb_devices()

        is_enable = not self.args.disable
        if len(devices) == 0:
            raise Exception('No device.')
        elif len(devices) >= 1:
            final_serial = AdbHelper.get_serial(self.args.serial)
            if final_serial is None:
                if len(devices) == 1:
                    logger.debug('No serial, and only one device')
                    self.set_certapps(enable=is_enable, serial=final_serial)
                else:
                    logger.debug('No serial, but there are more than one device')
                    raise Exception('Please specify the device by --serial option.')
            else:
                print('Serial: {0} (State: {1})'.format(final_serial, devices[final_serial]))
                self.set_certapps(enable=is_enable, serial=final_serial)


def main():
    try:
        FullPrivilegeResetter().run()
    except Exception as e:
        logger.error(e)
        exit(1)


if __name__ == '__main__':
    main()
