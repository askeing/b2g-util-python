#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import re
import os
import json
import shutil
import logging
import zipfile
import tempfile
import argparse
import subprocess
from distutils import util
from datetime import datetime
from argparse import ArgumentDefaultsHelpFormatter
from util import console_utilities
from util.adb_helper import AdbWrapper
from util.adb_helper import AdbHelper
from util.adb_helper import AdbWrapper


logger = logging.getLogger(__name__)


class VersionChecker(object):
    def __init__(self, **kwargs):
        self.arg_parser = argparse.ArgumentParser(description='Check the version information of Firefox OS.',
                                                  formatter_class=ArgumentDefaultsHelpFormatter)
        self.arg_parser.add_argument('--no-color', action='store_true', dest='no_color', default=False, help='Do not print with color. NO_COLOR will overrides this option.')
        self.arg_parser.add_argument('-s', '--serial', action='store', dest='serial', default=None, help='Directs command to the device or emulator with the given serial number. Overrides ANDROID_SERIAL environment variable.')
        self.arg_parser.add_argument('--log-text', action='store', dest='log_text', default=None, help='Text ouput.')
        self.arg_parser.add_argument('--log-json', action='store', dest='log_json', default=None, help='JSON output.')
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

    def get_device_info(self, serial=None):
        try:
            tmp_dir = tempfile.mkdtemp(prefix='checkversions_')
            # pull data from device
            if not AdbWrapper.adb_pull('/system/b2g/omni.ja', tmp_dir, serial=serial):
                logger.error('Error pulling Gecko file.')
            if not AdbWrapper.adb_pull('/data/local/webapps/settings.gaiamobile.org/application.zip', tmp_dir, serial=serial):
                if not AdbWrapper.adb_pull('/system/b2g/webapps/settings.gaiamobile.org/application.zip', tmp_dir, serial=serial):
                    logger.error('Error pulling Gaia file.')
            if not AdbWrapper.adb_pull('/system/b2g/application.ini', tmp_dir, serial=serial):
                logger.error('Error pulling application.ini file.')
            # get Gaia info
            gaia_rev = 'n/a'
            gaia_date = 'n/a'
            application_zip_file = tmp_dir + os.sep + 'application.zip'
            if os.path.isfile(application_zip_file):
                f = open(application_zip_file, 'rb')
                z = zipfile.ZipFile(f)
                z.extract('resources/gaia_commit.txt', tmp_dir)
                f.close()
            else:
                logger.warning('Can not find application.zip file.')
            gaiacommit_file = tmp_dir + os.sep + 'resources/gaia_commit.txt'
            if os.path.isfile(gaiacommit_file):
                f = open(gaiacommit_file, "r")
                gaia_rev = re.sub(r'\n+', '', f.readline())
                gaia_date_sec_from_epoch = re.sub(r'\n+', '', f.readline())
                f.close()
                gaia_date = datetime.utcfromtimestamp(int(gaia_date_sec_from_epoch)).strftime('%Y-%m-%d %H:%M:%S')
            else:
                logger.warning('Can not get gaia_commit.txt file from application.zip file.')
            # deoptimize omni.ja for Gecko info
            gecko_rev = 'n/a'
            if os.path.isfile(tmp_dir + os.sep + 'omni.ja'):
                deopt_dir = tmp_dir + os.sep + 'deopt'
                deopt_file = deopt_dir + os.sep + 'omni.ja'
                deopt_exec = tmp_dir + os.sep + 'optimizejars.py'
                os.makedirs(deopt_dir)
                # TODO rewrite optimizejars.py if possible
                current_dir = cur = os.path.dirname(os.path.abspath(__file__))
                current_exec = os.path.join(current_dir, 'misc', 'optimizejars.py')
                shutil.copyfile(current_exec, deopt_exec)
                cmd = 'python %s --deoptimize %s %s %s' % (deopt_exec, tmp_dir, tmp_dir, deopt_dir)
                p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                output = p.communicate()[0]
                # unzip omni.ja to get Gecko info
                if os.path.isfile(deopt_file):
                    f = open(deopt_file, 'rb')
                    z = zipfile.ZipFile(f)
                    z.extract('chrome/toolkit/content/global/buildconfig.html', tmp_dir)
                    f.close()
                else:
                    logger.warning('Can not deoptimize omni.ja file.')
                    gecko_rev = 'n/a'
                # get Gecko info from buildconfig.html file
                buildconfig_file = tmp_dir + os.sep + 'chrome/toolkit/content/global/buildconfig.html'
                if os.path.isfile(buildconfig_file):
                    for line in open(buildconfig_file, "r"):
                        if re.search(r'Built from', line):
                            ret = re.findall(r'>(.*?)<', line)
                            gecko_rev = ret[1]
                            break
                else:
                    logger.warning('Can not get buildconfig.html file from omni.ja file.')
            else:
                print 'Can not find omni.ja file.'
            # get Gecko version, and B2G BuildID from application.ini file
            if os.path.isfile(tmp_dir + os.sep + 'application.ini'):
                for line in open(tmp_dir + os.sep + 'application.ini', "r"):
                    if re.search(r'^\s*BuildID', line):
                        ret = re.findall(r'.*?=(.*)', line)
                        build_id = ret[0]
                    if re.search(r'^\s*Version', line):
                        ret = re.findall(r'.*?=(.*)', line)
                        version = ret[0]
            else:
                build_id = 'n/a'
                version = 'n/a'
            # get device information by getprop command
            device_name = re.sub(r'\r+|\n+', '', AdbWrapper.adb_shell('getprop ro.product.device', serial=serial))
            firmware_release = re.sub(r'\r+|\n+', '', AdbWrapper.adb_shell('getprop ro.build.version.release', serial=serial))
            firmware_incremental = re.sub(r'\r+|\n+', '', AdbWrapper.adb_shell('getprop ro.build.version.incremental', serial=serial))
            firmware_date = re.sub(r'\r+|\n+', '', AdbWrapper.adb_shell('getprop ro.build.date', serial=serial))
            firmware_bootloader = re.sub(r'\r+|\n+', '', AdbWrapper.adb_shell('getprop ro.boot.bootloader', serial=serial))
            # prepare the return information
            device_info = {}
            device_info['Serial'] = serial
            device_info['Build ID'] = build_id
            device_info['Gaia Revision'] = gaia_rev
            device_info['Gaia Date'] = gaia_date
            device_info['Gecko Revision'] = gecko_rev
            device_info['Gecko Version'] = version
            device_info['Device Name'] = device_name
            device_info['Firmware(Release)'] = firmware_release
            device_info['Firmware(Incremental)'] = firmware_incremental
            device_info['Firmware Date'] = firmware_date
            device_info['Bootloader'] = firmware_bootloader
        finally:
            shutil.rmtree(tmp_dir)
        return device_info

    def _print_device_info_item(self, title, value, title_color=None, value_color=None):
        console_utilities.print_color('{0:22s}'.format(title), fg_color=title_color, newline=False)
        console_utilities.print_color(value, fg_color=value_color)

    def print_device_info(self, device_info, no_color=False):
        # setup the format by platform
        if no_color:
            title_color = None
            sw_color = None
            hw_color = None
        else:
            title_color = console_utilities.COLOR_LIGHT_BLUE
            sw_color = console_utilities.COLOR_LIGHT_GREEN
            hw_color = console_utilities.COLOR_LIGHT_YELLOW
        # print the device information
        self._print_device_info_item('Build ID', device_info['Build ID'], title_color=title_color, value_color=sw_color)
        self._print_device_info_item('Gaia Revision', device_info['Gaia Revision'], title_color=title_color, value_color=sw_color)
        self._print_device_info_item('Gaia Date', device_info['Gaia Date'], title_color=title_color, value_color=sw_color)
        self._print_device_info_item('Gecko Revision', device_info['Gecko Revision'], title_color=title_color, value_color=sw_color)
        self._print_device_info_item('Gecko Version', device_info['Gecko Version'], title_color=title_color, value_color=sw_color)
        self._print_device_info_item('Device Name', device_info['Device Name'], title_color=title_color, value_color=hw_color)
        self._print_device_info_item('Firmware(Release)', device_info['Firmware(Release)'], title_color=title_color, value_color=hw_color)
        self._print_device_info_item('Firmware(Incremental)', device_info['Firmware(Incremental)'], title_color=title_color, value_color=hw_color)
        self._print_device_info_item('Firmware Date', device_info['Firmware Date'], title_color=title_color, value_color=hw_color)
        if device_info['Bootloader'] is not '':
            self._print_device_info_item('Bootloader', device_info['Bootloader'], title_color=title_color, value_color=hw_color)
        print ''

    def output_log(self, device_info_list):
        if self.args.log_json is None and self.args.log_text is None:
            return
        # prepare the result dict for parsing
        result = {}
        unknown_serial_index = 1
        for device_info in device_info_list:
            if device_info['Serial'] == None:
                device_serial = 'unknown_serial_' + str(unknown_serial_index)
                unknown_serial_index = unknown_serial_index + 1
            else:
                device_serial = device_info['Serial']
            result[device_serial] = device_info
        # output
        if self.args.log_text is not None:
            with open(self.args.log_text, 'w') as outfile:
                for device_serial, device_info in result.items():
                    outfile.write('# %s\n' % device_serial)
                    if 'Skip' in device_info and device_info['Skip'] is True:
                        outfile.write('%s=%s\n' % ('Skip', device_info['Skip']))
                    else:
                        for key, value in device_info.items():
                            outfile.write('%s=%s\n' % (re.sub(r'\s+|\(|\)', '', key), re.sub(r'\s+', '_', value)))
                        outfile.write('\n')
        if self.args.log_json is not None:
            with open(self.args.log_json, 'w') as outfile:
                json.dump(result, outfile, indent=4)

    def run(self):
        devices = AdbWrapper.adb_devices()
        is_no_color = self.args.no_color
        if 'NO_COLOR' in os.environ:
            try:
                is_no_color = bool(util.strtobool(os.environ['NO_COLOR'].lower()))
            except:
                logger.error('Invalid NO_COLOR value [{0}].'.format(os.environ['NO_COLOR']))

        if len(devices) == 0:
            raise Exception('No device.')
        elif len(devices) >= 1:
            final_serial = AdbHelper.get_serial(self.args.serial)
            if final_serial is None:
                device_info_list = []
                for device, state in devices.items():
                    print('Serial: {0} (State: {1})'.format(device, state))
                    if state == 'device':
                        device_info = self.get_device_info(serial=device)
                        self.print_device_info(device_info, no_color=is_no_color)
                        device_info_list.append(device_info)
                    else:
                        print('Skipped.\n')
                        device_info_list.append({'Serial': device, 'Skip': True})
                self.output_log(device_info_list)
            else:
                print('Serial: {0} (State: {1})'.format(final_serial, devices[final_serial]))
                device_info = self.get_device_info(serial=final_serial)
                self.print_device_info(device_info, no_color=is_no_color)
                self.output_log([device_info])


def main():
    try:
        VersionChecker().run()
    except Exception as e:
        logger.error(e)
        exit(1)


if __name__ == "__main__":
    main()
