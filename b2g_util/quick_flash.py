#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os
import stat
import shutil
import logging
import argparse
import tempfile
from argparse import ArgumentDefaultsHelpFormatter
from time import strftime

from check_versions import VersionChecker
from util.decompressor import Decompressor
from util.adb_helper import AdbWrapper
from util.b2g_helper import B2GHelper
from taskcluster_util.taskcluster_download import DownloadRunner


logger = logging.getLogger(__name__)


class QuickFlashHelper(object):
    LAST_UPDATE = '2016-03-04'

    SUPPORT_DEVICES = {'flame': {'name': 'flame-kk', 'image': 'flame-kk.zip'},
                       'aries': {'name': 'aries', 'image': 'aries.zip'},
                       'D5833': {'name': 'aries', 'image': 'aries.zip'}}
    SUPPORT_BRANCHES = ['mozilla-central', 'mozilla-b2g44_v2_5']
    SUPPORT_BUILDS = {'Engineer Build': '-eng-opt', 'User Build': '-opt'}

    BUILD_PATH = 'private/build/'
    NAMESPACE_FORMAT = 'gecko.v2.{branch}.latest.b2g.{device}{postfix}'.format
    ARTIFACT_FORMAT = '{build_path}{image}'.format

    def __init__(self):
        self.devices = None

    def show_support_devices(self):
        print('Supported Devices:')
        for device in self.SUPPORT_DEVICES.keys():
            print('\t{}'.format(device))

    def show_support_branches(self):
        print('Supported Branches:')
        for branch in self.SUPPORT_BRANCHES:
            print('\t{}'.format(branch))

    def cli(self):
        """
        Handle the argument parse, and the return the instance itself.
        """
        # argument parser
        arg_parser = argparse.ArgumentParser(description='Simply flash B2G into device. Last update: {}'.format(self.LAST_UPDATE),
                                             formatter_class=ArgumentDefaultsHelpFormatter)
        arg_parser.add_argument('-l', '--list', action='store_true', dest='list', default=False,
                                help='List supported devices and branches.')
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
        if args.list is True:
            self.show_support_devices()
            self.show_support_branches()
            exit(0)
        # check ADB
        AdbWrapper.check_adb()
        # return instance
        return self

    def select_branch(self):
        message = ''
        for item in self.SUPPORT_BRANCHES:
            message += '\t{}) {}\n'.format(self.SUPPORT_BRANCHES.index(item), item)
        message += '\tq) Exit'

        while True:
            try:
                ret = raw_input('\nWhat would you like to do?\n{}\nPlease select [ENTER]:'.format(message))[0]
                logger.debug('input: {}'.format(ret))
                if ret == 'q':
                    exit(0)
                elif int(ret) < len(self.SUPPORT_BRANCHES):
                    item = self.SUPPORT_BRANCHES[int(ret)]
                    logger.debug('Select {}'.format(item))
                    return item
            except (ValueError, IndexError):
                continue

    def select_build(self):
        message = ''
        for item in self.SUPPORT_BUILDS.keys():
            message += '\t{}) {}\n'.format(self.SUPPORT_BUILDS.keys().index(item), item)
        message += '\tq) Exit'

        while True:
            try:
                ret = raw_input('\nWhat would you like to do?\n{}\nPlease select [ENTER]:'.format(message))[0]
                logger.debug('input: {}'.format(ret))
                if ret == 'q':
                    exit(0)
                elif int(ret) < len(self.SUPPORT_BUILDS):
                    item = self.SUPPORT_BUILDS.values()[int(ret)]
                    logger.debug('Select {}'.format(item))
                    return item
            except (ValueError, IndexError):
                continue

    @staticmethod
    def download(namesapce, artifact):
        date = strftime('%Y-%m-%d')
        dl_path = os.path.abspath(os.path.join('.', date))
        dl_file = os.path.join(dl_path, os.path.basename(artifact))
        if os.path.isfile(dl_file):
            ret = raw_input('\nThe image file "{}" already exist.\n(Note: We don\'t know is it Engineer or User build.)\nSkip download and flash this image? [Y/n]'.format(dl_file))
            if len(ret) <= 0 or ret.lower()[0] != 'n':
                logger.info('Skip download, using exist file {}'.format(dl_file))
                return dl_file
        dl = DownloadRunner()
        dl.check_crendentials_file(None)
        dl.dest_dir = dl_path
        dl.namespace = namesapce
        dl.artifact_name = artifact
        dl.run()
        if os.path.isfile(dl_file):
            return dl_file
        else:
            raise Exception('Downlaod failed.')

    @staticmethod
    def _flash_again():
        ret = raw_input('\nWould you want to flash the same image to other device?? [y/N]')
        if len(ret) > 0 and ret.lower()[0] == 'y':
            logger.info('Flash image again.')
            return True
        return False

    def flash_image(self, image):
        try:
            temp_dir = tempfile.mkdtemp()
            logger.debug('Temporary folder: {}'.format(temp_dir))
            Decompressor().unzip(image, temp_dir)
            # set the permissions to rwxrwxr-x (509 in python's os.chmod)
            os.chmod(temp_dir + '/b2g-distro/flash.sh', stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR | stat.S_IRGRP | stat.S_IWGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)
            os.chmod(temp_dir + '/b2g-distro/load-config.sh', stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR | stat.S_IRGRP | stat.S_IWGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)
            while True:
                os.system('cd ' + temp_dir + '/b2g-distro; ./flash.sh -f')
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
                shutil.rmtree(temp_dir)  # delete directory
            except OSError:
                logger.debug('Cannot remove temporary folder: {}'.format(temp_dir))

    def run(self):
        """
        Entry point.
        """
        self.devices = AdbWrapper.adb_devices()
        logger.debug('Devices: {}'.format(self.devices))
        if len(self.devices) < 1:
            raise Exception('Can not find device, please connect your device.')
        elif len(self.devices) > 1:
            raise Exception('Find more than one device, please only connect one device.')

        # get device name
        device_name = AdbWrapper.adb_shell('getprop ro.product.device')[0]
        logger.info('Device found: {}'.format(device_name))
        if device_name not in self.SUPPORT_DEVICES.keys():
            raise Exception('The {} device is not supported.'.format(device_name))

        # select branch
        branch = self.select_branch()
        # select build type
        postfix = self.select_build()

        # get namespace and image artifact
        device_info = self.SUPPORT_DEVICES.get(device_name)
        namespace = self.NAMESPACE_FORMAT(branch=branch, device=device_info.get('name'), postfix=postfix)
        artifact = self.ARTIFACT_FORMAT(build_path=self.BUILD_PATH, image=device_info.get('image'))
        logger.info('Device: {}'.format(device_name))
        logger.info('Namespace: {}'.format(namespace))
        logger.info('Artifact: {}'.format(artifact))

        ret = raw_input('\nDownload "{artifact}" from "{namespace}".\nRight? [Y/n]'.format(artifact=artifact, namespace=namespace))
        if len(ret) > 0 and ret.lower()[0] == 'n':
            logger.info('Stop.')
            exit(0)
        # downloading image
        logger.info('Downloading image...')
        local_image = self.download(namespace, artifact)
        logger.debug('Image file: {}'.format(local_image))
        # checking file
        logger.info('Checking file...')
        if not B2GHelper.check_b2g_image(local_image):
            raise Exception('This is not B2G image file: {}'.format(local_image))
        # flashing image
        logger.info('Flashing image...')
        self.flash_image(local_image)


def main():
    try:
        QuickFlashHelper().cli().run()
    except Exception as e:
        logger.error(e)
        exit(1)


if __name__ == "__main__":
    main()
