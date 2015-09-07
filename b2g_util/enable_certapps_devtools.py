#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os
import shutil
import logging
import argparse
import tempfile
import textwrap
from argparse import RawTextHelpFormatter
from util.adb_helper import AdbHelper
from util.adb_helper import AdbWrapper
from util.b2g_helper import B2GHelper

logger = logging.getLogger(__name__)


class FullPrivilegeResetter(object):
    """
    Enable/disable Certified Apps Debugging.
    """

    def __init__(self):
        self.serial = None
        self.disable = False

    def set_serial(self, serial):
        """
        Setup the serial number.
        @param serial: the given serial number.
        """
        self.serial = serial
        logger.debug('Set serial: {}'.format(self.serial))

    def set_disable(self, flag):
        """
        Setup the disable flag.
        @param flag: True or False.
        """
        self.disable = flag
        logger.debug('Set disable: {}'.format(self.disable))

    def cli(self):
        """
        Handle the argument parse, and the return the instance itself.
        """
        # argument parser
        arg_parser = argparse.ArgumentParser(description='Enable/disable Certified Apps Debugging.',
                                             formatter_class=RawTextHelpFormatter,
                                             epilog=textwrap.dedent("""\
                                                  Please enable "ADB and Devtools" of device.
                                                  Ref:
                                                  - https://developer.mozilla.org/en-US/docs/Tools/WebIDE
                                                  - https://developer.mozilla.org/en-US/docs/Tools/WebIDE/Running_and_debugging_apps#Debugging_apps
                                                  """))
        arg_parser.add_argument('-s', '--serial', action='store', dest='serial', default=None,
                                help=textwrap.dedent("""\
                                     Directs command to the device or emulator with the
                                     given serial number. Overrides ANDROID_SERIAL
                                     environment variable. (default: %(default)s)
                                     """))
        arg_parser.add_argument('--disable', action='store_true', dest='disable', default=False,
                                help='Disable the privileges. (default: %(default)s)')
        arg_parser.add_argument('-v', '--verbose', action='store_true', dest='verbose', default=False,
                                help=textwrap.dedent("""\
                                     Turn on verbose output, with all the debug logger.
                                     (default: %(default)s)
                                     """))
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
        self.set_disable(args.disable)
        # return instance
        return self

    @staticmethod
    def setup_certapps(enable=True, serial=None):
        """
        Set the devtools permission for certapps.
        @param enable: True will turn on the permission. False will turn off the permission.
        @param serial: device serial number. (optional)
        @raise exception: When it cannot pulling/pushing the pref.js file of device.
        """
        AdbWrapper.adb_root(serial=serial)
        logger.info('{} Full Privilege for WebIDE...'.format('Enabling' if enable else 'Disabling'))

        need_restart = True
        tmp_dir = None
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
                                logger.info(
                                    'The full privilege is already {}.'.format('enabled' if enable else 'disabled'))
                                need_restart = False
                                break
                            else:
                                logger.info('Changing setting of pref.js file...')
                                fw.write(
                                    'user_pref("devtools.debugger.forbid-certified-apps", {});\n'.format(is_forbid))
                            match = True
                        else:
                            fw.write(line)
                    if not match:
                        if not enable:
                            # the forbid is true when there is no setting
                            logger.info('The full privilege is already disabled.')
                            need_restart = False
                        else:
                            if need_restart:
                                # adding setting when there is no setting and need to enable certapps
                                logger.info('Adding setting of pref.js file...')
                                fw.write(
                                    'user_pref("devtools.debugger.forbid-certified-apps", {});\n'.format(is_forbid))
            if need_restart:
                B2GHelper.stop_b2g(serial=serial)
                try:
                    logger.info('Pushing prefs.js file...')
                    AdbWrapper.adb_push(dest_file, device_src_file, serial=serial)
                except:
                    raise Exception('Error pushing prefs.js file.')
        finally:
            if need_restart:
                B2GHelper.start_b2g(serial=serial)
            if tmp_dir:
                shutil.rmtree(tmp_dir)
                logger.debug('Remove {}.'.format(tmp_dir))

    def run(self):
        """
        Entry point.
        """
        devices = AdbWrapper.adb_devices()

        is_enable = not self.disable
        if len(devices) == 0:
            raise Exception('No device.')
        elif len(devices) >= 1:
            final_serial = AdbHelper.get_serial(self.serial)
            if final_serial is None:
                if len(devices) == 1:
                    logger.debug('No serial, and only one device')
                    self.setup_certapps(enable=is_enable, serial=final_serial)
                else:
                    logger.debug('No serial, but there are more than one device')
                    raise Exception('Please specify the device by --serial option.')
            else:
                print('Serial: {0} (State: {1})'.format(final_serial, devices[final_serial]))
                self.setup_certapps(enable=is_enable, serial=final_serial)


def main():
    try:
        FullPrivilegeResetter().cli().run()
    except Exception as e:
        logger.error(e)
        exit(1)


if __name__ == '__main__':
    main()
