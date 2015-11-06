#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os
import sys
import stat
import shutil
import logging
import tarfile
import zipfile
import easygui
import tempfile
import textwrap
import argparse
from argparse import RawTextHelpFormatter
from sys import platform as _platform

from check_versions import VersionChecker
from shallow_flash import ShallowFlashHelper
from util.adb_helper import AdbWrapper
from util.decompressor import Decompressor
from taskcluster_util.taskcluster_traverse import TraverseRunner


logger = logging.getLogger(__name__)


class B2GTraverseRunner(TraverseRunner):

    def __init__(self, connection_options=None):
        self.has_image = False
        self.image_path = None
        self.image_magic_folder = 'b2g-distro/'

        self.has_gaia = False
        self.gaia_path = None
        self.gaia_magic_folder = 'gaia/profile/'

        self.has_gecko = False
        self.gecko_path = None
        self.gecko_magic_folder = 'b2g'

        super(B2GTraverseRunner, self).__init__(connection_options=connection_options)

    def parser(self):
        # argument parser
        parser = argparse.ArgumentParser(description='The simple GUI tool for flashing B2G from Taskcluster.',
                                         formatter_class=RawTextHelpFormatter,
                                         epilog=textwrap.dedent('''\
                                         For more information of Taskcluster, see:
                                         - http://docs.taskcluster.net/
                                         - https://pypi.python.org/pypi/taskcluster_util

                                         The tc_credentials.json Template:
                                             {
                                                 "clientId": "",
                                                 "accessToken": "",
                                                 "certificate": {
                                                     "version":1,
                                                     "scopes":["*"],
                                                     "start":xxx,
                                                     "expiry":xxx,
                                                     "seed":"xxx",
                                                     "signature":"xxx"
                                                 }
                                             }
                                         '''))
        parser.add_argument('--credentials', action='store', default=self.taskcluster_credentials, dest='credentials',
                            help='The credential JSON file\n(default: {})'.format(self.taskcluster_credentials))
        parser.add_argument('-n', '--namespace', action='store', dest='namespace', default='',
                            help='The namespace of task')
        parser.add_argument('-d', '--dest-dir', action='store', dest='dest_dir',
                            help='The dest folder (default: current working folder)')
        parser.add_argument('-v', '--verbose', action='store_true', dest='verbose', default=False,
                            help='Turn on verbose output, with all the debug logger.')
        return parser.parse_args(sys.argv[1:])

    def check_b2g_image(self, file_path):
        logger.debug('check image: {}'.format(file_path))
        if os.path.isfile(file_path) and file_path.endswith('.zip'):
            try:
                with zipfile.ZipFile(file_path, 'r') as f:
                    if self.image_magic_folder in f.namelist():
                        self.has_image = True
                        self.image_path = file_path
                        logger.info('Find B2G Image {}'.format(self.image_path))
                        return True
            except:
                logger.debug('cannot open: {}'.format(file_path))
                return False
        return False

    def check_gaia_package(self, file_path):
        logger.debug('check gaia: {}'.format(file_path))
        if os.path.isfile(file_path) and file_path.endswith('.zip'):
            try:
                with zipfile.ZipFile(file_path, 'r') as f:
                    if self.gaia_magic_folder in f.namelist():
                        self.has_gaia = True
                        self.gaia_path = file_path
                        logger.info('Find Gaia Package {}'.format(self.gaia_path))
                        return True
            except:
                logger.debug('cannot open: {}'.format(file_path))
                return False
        return False

    def check_gecko_package(self, file_path):
        logger.debug('check gecko: {}'.format(file_path))
        if os.path.isfile(file_path) and file_path.endswith('.tar.gz'):
            try:
                with tarfile.TarFile.open(file_path, 'r:gz') as f:
                    if self.gecko_magic_folder in f.getnames():
                        self.has_gecko = True
                        self.gecko_path = file_path
                        logger.info('Find Gecko Package {}'.format(self.gecko_path))
                        return True
            except:
                logger.debug('cannot open: {}'.format(file_path))
                return False
        return False

    def generate_flash_message(self):
        msg = 'What do you want to flash?\n\n' \
            '- Skip: do not want to flash any thing.\n'
        msg_footer = ''

        if _platform == "win32":
            logger.info('Flash B2G Image cannot run on Windows.')
        else:
            if self.has_image:
                msg = msg + '- Image: flash images into device.\n'
                msg_footer = msg_footer + '[Image] {}\n'.format(self.image_path)
        if self.has_gaia:
            msg = msg + '- Gaia: only shallow flash Gaia.\n'
            msg_footer = msg_footer + '[Gaia] {}\n'.format(self.gaia_path)
        if self.has_gecko:
            msg = msg + '- Gecko: only shallow flash Gecko.\n'
            msg_footer = msg_footer + '[Gecko] {}\n'.format(self.gecko_path)
        if self.has_gaia and self.has_gecko:
            msg = msg + '- Gaia_Gecko: shallow flash both Gaia and Gecko.\n'
        msg = msg + '\n' + msg_footer + '\nMake sure there is only ONE device connected to the computer!'
        return msg

    def generate_flash_choices(self):
        choices = ['Skip']
        if _platform == "win32":
            logger.info('Flash B2G Image cannot run on Windows.')
        else:
            if self.has_image:
                choices.append('Image')
        if self.has_gaia:
            choices.append('Gaia')
        if self.has_gecko:
            choices.append('Gecko')
        if self.has_gaia and self.has_gecko:
            choices.append('Gaia_Gecko')
        return choices

    def _flash_again(self):
        title = 'Flash Again?'
        msg = 'Would you like to flash next devcie with the same build?'
        return easygui.ynbox(msg, title)

    def flash_Skip(self):
        logger.info('Skip flash.')

    def flash_Image(self):
        logger.info('Run flash Image...')
        if self.image_path:
            self._flash_image(self.image_path)

    def _flash_image(self, image):
        try:
            self.temp_dir = tempfile.mkdtemp()
            logger.debug('Temporary folder: {}'.format(self.temp_dir))
            Decompressor().unzip(image, self.temp_dir)
            # set the permissions to rwxrwxr-x (509 in python's os.chmod)
            os.chmod(self.temp_dir + '/b2g-distro/flash.sh', stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR | stat.S_IRGRP | stat.S_IWGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)
            os.chmod(self.temp_dir + '/b2g-distro/load-config.sh', stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR | stat.S_IRGRP | stat.S_IWGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)
            while True:
                os.system('cd ' + self.temp_dir + '/b2g-distro; ./flash.sh -f')
                # wait for device, and then check version
                AdbWrapper.adb_wait_for_device(timeout=120)
                logger.info('Check versions.')
                checker = VersionChecker()
                checker.run()
                # flash more than one device
                if not self._flash_again():
                    break
        finally:
            try:
                shutil.rmtree(self.temp_dir)  # delete directory
            except OSError:
                logger.debug('Cannot remove temporary folder: {}'.format(self.temp_dir))

    def flash_Gaia(self):
        logger.info('Run flash Gaia...')
        if self.gaia_path:
            self._shallow_flash(gaia=self.gaia_path)

    def flash_Gecko(self):
        logger.info('Run flash Gecko...')
        if self.gecko_path:
            self._shallow_flash(gecko=self.gecko_path)

    def flash_Gaia_Gecko(self):
        logger.info('Run flash Gaia_Gecko...')
        if self.gaia_path and self.gecko_path:
            self._shallow_flash(gaia=self.gaia_path, gecko=self.gecko_path)

    def _shallow_flash(self, gaia=None, gecko=None):
        if gaia or gecko:
            logger.info('Shallow Flash...')
            while True:
                sfh = ShallowFlashHelper()
                if gaia:
                    logger.info('Gaia: {}'.format(gaia))
                    sfh.set_gaia(gaia)
                if gecko:
                    logger.info('Gecko: {}'.format(gecko))
                    sfh.set_gecko(gecko)
                title = 'Keep Profile'
                msg = 'Would you like to keep profile? (BETA)'
                keep_profile = easygui.ynbox(msg, title)
                if keep_profile:
                    logger.info('Keep Profile: {}'.format(keep_profile))
                    sfh.set_keep_profile(keep_profile)
                sfh.run()
                # flash more than one device
                if not self._flash_again():
                    break
        else:
            logger.warning('No Gaia and no Gecko for flashing.')

    def _reset_arguments(self):
        # reset image args
        self.has_image = False
        self.image_path = None
        # reset gaia args
        self.has_gaia = False
        self.gaia_path = None
        # reset gecko args
        self.has_gecko = False
        self.gecko_path = None
        logger.debug('Reset image/gaia/gecko path and flags.')
        super(B2GTraverseRunner, self)._reset_arguments()

    def do_after_download(self):
        """
        Do something after downloading finished.
        """
        # check the files
        for f in self.downloaded_file_list:
            if not self.check_b2g_image(os.path.abspath(f)):
                logger.debug('{} is not b2g image.'.format(f))
                if not self.check_gaia_package(os.path.abspath(f)):
                    logger.debug('{} is not gaia package.'.format(f))
                    if not self.check_gecko_package(os.path.abspath(f)):
                        logger.debug('{} is not gecko package.'.format(f))

        if (not self.has_image) and (not self.has_gaia) and (not self.has_gecko):
            # there is no any package found
            easygui.msgbox('Cannot found B2G Image, Gaia, and Gecko.', ok_button='I know')
        else:
            title = 'Flash B2G'
            msg = self.generate_flash_message()
            choices = self.generate_flash_choices()
            reply = easygui.buttonbox(msg, title, choices=choices)
            logger.info('Select: {}'.format(reply))
            # then call method by reply's string
            if reply:
                call_method = getattr(self, 'flash_' + reply)
                call_method()
        super(B2GTraverseRunner, self).do_after_download()


def main():
    try:
        B2GTraverseRunner().cli().run()
    except Exception as e:
        logger.error(e)
        exit(1)


if __name__ == '__main__':
    main()
