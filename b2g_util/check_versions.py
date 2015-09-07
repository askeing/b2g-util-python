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
from util.adb_helper import AdbHelper
from util.adb_helper import AdbWrapper

logger = logging.getLogger(__name__)


class VersionChecker(object):
    def __init__(self):
        self.devices = None
        self.device_info_list = []
        self.no_color = False
        self.serial = None
        self.log_text = None
        self.log_json = None

    def set_serial(self, serial):
        """
        Setup the serial number.
        @param serial: the given serial number.
        """
        self.serial = serial
        logger.debug('Set serial: {}'.format(self.serial))

    def set_no_color(self, flag):
        """
        Setup the no_color flag.
        @param flag: True or Flas.
        """
        self.no_color = flag
        logger.debug('Set no_color: {}'.format(self.no_color))

    def set_log_text(self, log_text):
        """
        Setup the log_text file path.
        @param log_text: the output text file path.
        """
        self.log_text = log_text
        logger.debug('Set log_text: {}'.format(self.log_text))

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
        arg_parser = argparse.ArgumentParser(description='Check the version information of Firefox OS.',
                                             formatter_class=ArgumentDefaultsHelpFormatter)
        arg_parser.add_argument('--no-color', action='store_true', dest='no_color', default=False,
                                help='Do not print with color. NO_COLOR will overrides this option.')
        arg_parser.add_argument('-s', '--serial', action='store', dest='serial', default=None,
                                help='Directs command to the device or emulator with the given serial number. '
                                     'Overrides ANDROID_SERIAL environment variable.')
        arg_parser.add_argument('--log-text', action='store', dest='log_text', default=None, help='Text ouput.')
        arg_parser.add_argument('--log-json', action='store', dest='log_json', default=None, help='JSON output.')
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
        self.set_no_color(args.no_color)
        self.set_serial(args.serial)
        self.set_log_text(args.log_text)
        self.set_log_json(args.log_json)
        # return instance
        return self

    @staticmethod
    def get_device_info(serial=None):
        """
        Get the device information, include Gaia Version, Gecko Version, and so on.
        @param serial: device serial number. (optional)
        @return: the information dict object.
        """
        tmp_dir = None
        try:
            tmp_dir = tempfile.mkdtemp(prefix='checkversions_')
            # pull data from device
            try:
                AdbWrapper.adb_pull('/system/b2g/omni.ja', tmp_dir, serial=serial)
            except Exception as e:
                logger.debug(e)
                logger.error('Error pulling Gecko file.')
            try:
                AdbWrapper.adb_pull('/data/local/webapps/settings.gaiamobile.org/application.zip', tmp_dir,
                                    serial=serial)
            except Exception as e:
                logger.debug(e)
                try:
                    AdbWrapper.adb_pull('/system/b2g/webapps/settings.gaiamobile.org/application.zip', tmp_dir,
                                        serial=serial)
                except Exception as e:
                    logger.debug(e)
                    logger.error('Error pulling Gaia file.')
            try:
                AdbWrapper.adb_pull('/system/b2g/application.ini', tmp_dir, serial=serial)
            except Exception as e:
                logger.debug(e)
                logger.error('Error pulling application.ini file.')
            # get Gaia info
            gaia_rev = 'n/a'
            gaia_date = 'n/a'
            application_zip_file = os.path.join(tmp_dir, 'application.zip')
            if os.path.isfile(application_zip_file):
                with open(application_zip_file, 'rb') as f:
                    z = zipfile.ZipFile(f)
                    z.extract('resources/gaia_commit.txt', tmp_dir)
            else:
                logger.warning('Can not find application.zip file.')
            gaiacommit_file = os.path.join(tmp_dir, 'resources/gaia_commit.txt')
            if os.path.isfile(gaiacommit_file):
                with open(gaiacommit_file, "r") as f:
                    gaia_rev = re.sub(r'\n+', '', f.readline())
                    gaia_date_sec_from_epoch = re.sub(r'\n+', '', f.readline())
                gaia_date = datetime.utcfromtimestamp(int(gaia_date_sec_from_epoch)).strftime('%Y-%m-%d %H:%M:%S')
            else:
                logger.warning('Can not get gaia_commit.txt file from application.zip file.')
            # deoptimize omni.ja for Gecko info
            gecko_rev = 'n/a'
            if os.path.isfile(os.path.join(tmp_dir, 'omni.ja')):
                deopt_dir = os.path.join(tmp_dir, 'deopt')
                deopt_file = os.path.join(deopt_dir, 'omni.ja')
                deopt_exec = os.path.join(tmp_dir, 'optimizejars.py')
                os.makedirs(deopt_dir)
                # TODO rewrite optimizejars.py if possible
                current_dir = os.path.dirname(os.path.abspath(__file__))
                current_exec = os.path.join(current_dir, 'misc', 'optimizejars.py')
                shutil.copyfile(current_exec, deopt_exec)
                cmd = 'python %s --deoptimize %s %s %s' % (deopt_exec, tmp_dir, tmp_dir, deopt_dir)
                p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                output = p.communicate()[0]
                logger.debug('optimizejars.py stdout: {}'.format(output))
                # unzip omni.ja to get Gecko info
                if os.path.isfile(deopt_file):
                    with open(deopt_file, 'rb') as f:
                        z = zipfile.ZipFile(f)
                        z.extract('chrome/toolkit/content/global/buildconfig.html', tmp_dir)
                else:
                    logger.warning('Can not deoptimize omni.ja file.')
                    gecko_rev = 'n/a'
                # get Gecko info from buildconfig.html file
                buildconfig_file = os.path.join(tmp_dir, 'chrome/toolkit/content/global/buildconfig.html')
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
            build_id = 0
            version = 0
            if os.path.isfile(os.path.join(tmp_dir, 'application.ini')):
                for line in open(os.path.join(tmp_dir, 'application.ini'), "r"):
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
            device_name = re.sub(r'\r+|\n+', '', AdbWrapper.adb_shell('getprop ro.product.device', serial=serial)[0])
            firmware_release = re.sub(r'\r+|\n+', '',
                                      AdbWrapper.adb_shell('getprop ro.build.version.release', serial=serial)[0])
            firmware_incremental = re.sub(r'\r+|\n+', '',
                                          AdbWrapper.adb_shell('getprop ro.build.version.incremental', serial=serial)[
                                              0])
            firmware_date = re.sub(r'\r+|\n+', '', AdbWrapper.adb_shell('getprop ro.build.date', serial=serial)[0])
            firmware_bootloader = re.sub(r'\r+|\n+', '',
                                         AdbWrapper.adb_shell('getprop ro.boot.bootloader', serial=serial)[0])
            # prepare the return information
            device_info = {'Serial': serial,
                           'Build ID': build_id,
                           'Gaia Revision': gaia_rev,
                           'Gaia Date': gaia_date,
                           'Gecko Revision': gecko_rev,
                           'Gecko Version': version,
                           'Device Name': device_name,
                           'Firmware(Release)': firmware_release,
                           'Firmware(Incremental)': firmware_incremental,
                           'Firmware Date': firmware_date,
                           'Bootloader': firmware_bootloader}
        finally:
            if tmp_dir:
                shutil.rmtree(tmp_dir)
                logger.debug('Remove {}.'.format(tmp_dir))
        return device_info

    @staticmethod
    def _print_device_info_item(title, value, title_color=None, value_color=None):
        console_utilities.print_color('{0:22s}'.format(title), fg_color=title_color, newline=False)
        console_utilities.print_color(value, fg_color=value_color)

    def print_device_info(self, device_info, no_color=False):
        """
        Print the device information.
        @param device_info: The information dict object.
        @param no_color: Print with color. Default is False.
        """
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
        self._print_device_info_item('Gaia Revision', device_info['Gaia Revision'], title_color=title_color,
                                     value_color=sw_color)
        self._print_device_info_item('Gaia Date', device_info['Gaia Date'], title_color=title_color,
                                     value_color=sw_color)
        self._print_device_info_item('Gecko Revision', device_info['Gecko Revision'], title_color=title_color,
                                     value_color=sw_color)
        self._print_device_info_item('Gecko Version', device_info['Gecko Version'], title_color=title_color,
                                     value_color=sw_color)
        self._print_device_info_item('Device Name', device_info['Device Name'], title_color=title_color,
                                     value_color=hw_color)
        self._print_device_info_item('Firmware(Release)', device_info['Firmware(Release)'], title_color=title_color,
                                     value_color=hw_color)
        self._print_device_info_item('Firmware(Incremental)', device_info['Firmware(Incremental)'],
                                     title_color=title_color, value_color=hw_color)
        self._print_device_info_item('Firmware Date', device_info['Firmware Date'], title_color=title_color,
                                     value_color=hw_color)
        if device_info['Bootloader'] is not '':
            self._print_device_info_item('Bootloader', device_info['Bootloader'], title_color=title_color,
                                         value_color=hw_color)
        print ''

    def _output_log(self):
        """
        Write the information into file.
        Enable it by I{--log-text} and I{--log-json} arguments.
        """
        if self.log_json is None and self.log_text is None:
            return
        # prepare the result dict for parsing
        result = self.get_output_dict()
        # output
        if self.log_text is not None:
            with open(self.log_text, 'w') as outfile:
                for device_serial, device_info in result.items():
                    outfile.write('# %s\n' % device_serial)
                    if 'Skip' in device_info and device_info['Skip'] is True:
                        outfile.write('%s=%s\n' % ('Skip', device_info['Skip']))
                    else:
                        for key, value in device_info.items():
                            outfile.write('%s=%s\n' % (re.sub(r'\s+|\(|\)', '', key), re.sub(r'\s+', '_', value)))
                        outfile.write('\n')
        if self.log_json is not None:
            with open(self.log_json, 'w') as outfile:
                json.dump(result, outfile, indent=4)

    def get_output_dict(self):
        """
        Can get the devices' information dict object after run().
        """
        result = {}
        unknown_serial_index = 1
        for device_info in self.device_info_list:
            if device_info['Serial'] is None:
                device_serial = 'unknown_serial_' + str(unknown_serial_index)
                unknown_serial_index += 1
            else:
                device_serial = device_info['Serial']
            result[device_serial] = device_info
        return result

    def run(self):
        """
        Entry point.
        """
        self.devices = AdbWrapper.adb_devices()
        is_no_color = self.no_color
        if 'NO_COLOR' in os.environ:
            try:
                is_no_color = bool(util.strtobool(os.environ['NO_COLOR'].lower()))
            except Exception as e:
                logger.debug(e)
                logger.error('Invalid NO_COLOR value [{0}].'.format(os.environ['NO_COLOR']))

        if len(self.devices) == 0:
            raise Exception('No device.')
        elif len(self.devices) >= 1:
            final_serial = AdbHelper.get_serial(self.serial)
            if final_serial is None:
                self.device_info_list = []
                for device, state in self.devices.items():
                    print('Serial: {0} (State: {1})'.format(device, state))
                    if state == 'device':
                        device_info = self.get_device_info(serial=device)
                        self.print_device_info(device_info, no_color=is_no_color)
                        self.device_info_list.append(device_info)
                    else:
                        print('Skipped.\n')
                        self.device_info_list.append({'Serial': device, 'Skip': True})
            else:
                print('Serial: {0} (State: {1})'.format(final_serial, self.devices[final_serial]))
                device_info = self.get_device_info(serial=final_serial)
                self.device_info_list = [device_info]
                self.print_device_info(device_info, no_color=is_no_color)
            self._output_log()


def main():
    try:
        VersionChecker().cli().run()
    except Exception as e:
        logger.error(e)
        exit(1)


if __name__ == "__main__":
    main()
