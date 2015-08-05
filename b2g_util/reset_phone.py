#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os
import argparse
from argparse import ArgumentDefaultsHelpFormatter
from util.adb_helper import AdbHelper


class PhoneReseter(object):
    def __init__(self, **kwargs):
        self.arg_parser = argparse.ArgumentParser(description='Reset Firefox OS Phone.',
                                                  formatter_class=ArgumentDefaultsHelpFormatter)
        self.arg_parser.add_argument('-s', '--serial', action='store', dest='serial', default=None, help='Directs command to the device or emulator with the given serial number. Overrides ANDROID_SERIAL environment variable.')
        self.args = self.arg_parser.parse_args()

    def print_log(self, msg):
        print '###', msg

    def reset_phone(self, serial=None):
        self.print_log('Starting to Reset Firefox OS Phone...')
        AdbHelper.adb_shell('rm -r /cache/*', serial=serial)
        AdbHelper.adb_shell('mkdir /cache/recovery', serial=serial)
        AdbHelper.adb_shell('echo "--wipe_data" > /cache/recovery/command', serial=serial)
        AdbHelper.adb_shell('reboot recovery', serial=serial)
        self.print_log('Reset Firefox OS Phone done.')

    def run(self):
        devices = AdbHelper.adb_devices()

        if len(devices) == 0:
            print 'No device.'
            exit(1)
        elif len(devices) >= 1:
            # has --serial, then skip ANDROID_SERIAL
            # then reset one device by --serial
            if (self.args.serial is not None):
                if self.args.serial in devices:
                    serial = self.args.serial
                    print 'Serial: {0} (State: {1})'.format(serial, devices[serial])
                    ret = self.reset_phone(serial=serial)
                else:
                    print 'Can not found {0}.\nDevices:'.format(self.args.serial)
                    for device, state in devices.items():
                        print 'Serial: {0} (State: {1})'.format(device, state)
                    exit(1)
            # no --serial, but has ANDROID_SERIAL
            # then reset one device by ANDROID_SERIAL
            elif (self.args.serial is None) and ('ANDROID_SERIAL' in os.environ):
                if os.environ['ANDROID_SERIAL'] in devices:
                    serial = os.environ['ANDROID_SERIAL']
                    print 'Serial: {0} (State: {1})'.format(serial, devices[serial])
                    ret = self.reset_phone(serial=serial)
                else:
                    print 'Can not found {0}.\nDevices:'.format(os.environ['ANDROID_SERIAL'])
                    for device, state in devices.items():
                        print 'Serial: {0} (State: {1})'.format(device, state)
                    exit(1)
            # no --serial, no ANDROID_SERIAL
            # more than ONE devices, then reset NO devices
            # only ONE devices, then reset this device
            if (self.args.serial is None) and (not 'ANDROID_SERIAL' in os.environ):
                if len(devices) > 1:
                    print 'More than one device.'
                    print 'Please specify ANDROID_SERIAL by "--serial" option.\n'
                    device_info_list = []
                    for device, state in devices.items():
                        print 'Serial: {0} (State: {1})'.format(device, state)
                    exit(1)
                elif len(devices) == 1:
                    for device, state in devices.items():
                        print 'Serial: {0} (State: {1})'.format(device, state)
                        ret = self.reset_phone(serial=device)


def main():
    if not AdbHelper.has_adb():
        print 'There is no "adb" in your environment PATH.'
        exit(1)

    my_app = PhoneReseter()
    my_app.run()


if __name__ == '__main__':
    main()
