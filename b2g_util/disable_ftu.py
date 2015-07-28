#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os
import sys
import json
import shutil
import logging
import argparse
import tempfile
import subprocess
from util.adb_helper import AdbHelper


class FTUDisabler(object):
    def __init__(self, **kwargs):
        self.logger = logging.getLogger(__name__)
        self.arg_parser = argparse.ArgumentParser(description='Disable the FTU of Firefox OS.')
        self.arg_parser.add_argument('--debug', action='store_true', dest='debug', default=False, help='Debug mode.')
        self.args = self.arg_parser.parse_args()

    def load_settings_json(self, file):
        if file is None:
            print('No file {}'.format(file))
            exit(1)
        else:
            if not os.path.exists(file):
                print('No file {}'.format(file))
            print('Loading {}'.format(file))
        return json.load(open(file))

    def main(self):
        try:
            if not AdbHelper.adb_root():
                pass
            else:
                tmp_dir = tempfile.mkdtemp(prefix='FTUDisabler_')
                tmp_file = tmp_dir + os.sep + 'settings.json'

                # stop b2g
                AdbHelper.adb_shell('stop b2g')
                # Pulling the settings file from phone.
                print('Pulling the settings...')
                AdbHelper.adb_pull('/system/b2g/defaults/settings.json', tmp_file)

                # Loading the settings.
                print('Processing...')
                settings = self.load_settings_json(tmp_file)
                import pdb
                pdb.set_trace()
                settings['ftu.manifestURL'] = None
                settings_json = json.dumps(settings)
                f = open(tmp_file,'w')
                f.write(settings_json)
                f.close()

                # Pushing the settings file to phone.
                print('Pushing the settings...')
                AdbHelper.adb_shell('mount -o rw,remount /system')
                AdbHelper.adb_push(tmp_file, '/system/b2g/defaults/settings.json')
                AdbHelper.adb_shell('mount -o ro,remount /system')
                # start b2g
                AdbHelper.adb_shell('start b2g')
        finally:
            print('Removing [{0}] folder...'.format(tmp_dir))
            shutil.rmtree(tmp_dir)
            print('Done.')


if __name__ == '__main__':
    my_app = FTUDisabler()
    # setup logger
    formatter = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    if my_app.args.debug is True:
        logging.basicConfig(level=logging.DEBUG, format=formatter)
    else:
        logging.basicConfig(level=logging.INFO, format=formatter)
    # check adb
    if not AdbHelper.has_adb():
        print('There is no "adb" in your environment PATH.')
        exit(1)
    # run
    my_app.main()
