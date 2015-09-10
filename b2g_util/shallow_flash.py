#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import re
import os
import shutil
import logging
import tempfile
import argparse
import ConfigParser
from argparse import ArgumentDefaultsHelpFormatter
from reset_phone import PhoneReseter
from check_versions import VersionChecker
from backup_restore_profile import BackupRestoreHelper
from util.adb_helper import AdbHelper
from util.adb_helper import AdbWrapper
from util.b2g_helper import B2GHelper
from util.decompressor import Decompressor

logger = logging.getLogger(__name__)


class ShallowFlashHelper(object):
    """
    Workaround for shallow flash Gaia or Gecko into device.
    """

    def __init__(self):
        # default settings
        self.serial = None
        self.gaia = None
        self.gecko = None
        self.keep_profile = False

    def set_serial(self, serial):
        """
        Setup the serial number.
        @param serial: the given serial number.
        """
        self.serial = serial
        logger.debug('Set serial: {}'.format(self.serial))

    def set_gaia(self, gaia):
        """
        Setup the Gaia package path.
        @param gaia: the given Gaia package path.
        """
        self.gaia = gaia
        logger.debug('Set gaia: {}'.format(self.gaia))

    def set_gecko(self, gecko):
        """
        Setup the Gecko package path.
        @param gecko: the given Gecko package path.
        """
        self.gecko = gecko
        logger.debug('Set gecko: {}'.format(self.gecko))

    def set_keep_profile(self, flag):
        """
        Setup the serial number.
        @param flag: True or False.
        """
        self.keep_profile = flag
        logger.debug('Set keep_profile: {}'.format(self.keep_profile))

    def cli(self):
        """
        Handle the argument parse, and the return the instance itself.
        """
        # argument parser
        arg_parser = argparse.ArgumentParser(
            description='Workaround for shallow flash Gaia or Gecko into device.',
            formatter_class=ArgumentDefaultsHelpFormatter)
        arg_parser.add_argument('-s', '--serial', action='store', dest='serial', default=None,
                                help='Directs command to the device or emulator with the given serial number. '
                                     'Overrides ANDROID_SERIAL environment variable.')
        arg_parser.add_argument('-g', '--gaia', action='store', dest='gaia', default=None,
                                help='Specify the Gaia package. (zip format)')
        arg_parser.add_argument('-G', '--gecko', action='store', dest='gecko', default=None,
                                help='Specify the Gecko package. (tar.gz format)')
        arg_parser.add_argument('--keep-profile', action='store_true', dest='keep_profile', default=False,
                                help='Keep user profile of device. Only work with shallow flash Gaia. (BETA)')
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
        # assign the variable
        self.set_serial(args.serial)
        if args.gaia:
            if self._is_gaia_package(args.gaia):
                self.set_gaia(args.gaia)
        if args.gecko:
            if self._is_gecko_package(args.gecko):
                self.set_gecko(args.gecko)
        self.set_keep_profile(args.keep_profile)
        # return instance
        return self

    @staticmethod
    def _is_gaia_package(gaia_pkg):
        return os.path.isfile(gaia_pkg) and gaia_pkg.endswith('.zip')

    @staticmethod
    def _is_gecko_package(gecko_pkg):
        return os.path.isfile(gecko_pkg) and gecko_pkg.endswith('.tar.gz')

    def _clean_gaia(self):
        logger.info('Cleaning Gaia profile: Start')
        command_list = ['rm -r /cache/*',
                        'rm -r /data/b2g/*',
                        'rm -r /data/local/storage/persistent/*',
                        'rm -r /data/local/svoperapps',
                        'rm -r /data/local/webapps',
                        'rm -r /data/local/user.js',
                        'rm -r /data/local/permissions.sqlite*',
                        'rm -r /data/local/OfflineCache',
                        'rm -r /data/local/indexedDB',
                        'rm -r /data/local/debug_info_trigger',
                        'rm -r /system/b2g/webapps']
        for cmd in command_list:
            AdbWrapper.adb_shell(cmd, serial=self.serial)
        logger.info('Cleaning Gaia profile: Done')

    def _push_gaia(self, source_dir):
        # push into device
        logger.info('Pushing Gaia: Start')
        unziped_gaia_dir = os.path.join(source_dir, 'gaia')

        # push user.js
        source_user_pref_path = os.path.join(unziped_gaia_dir, 'profile', 'user.js')
        user_pref_path = os.path.join(source_dir, 'user.js')
        # prepare the user.js
        logger.debug('Prepare user.js file')
        with open(source_user_pref_path, 'r') as fin:
            with open(user_pref_path, 'w') as fout:
                for line in fin:
                    fout.write(line.replace('user_pref', 'pref'))
        user_pref_target_path = '/system/b2g/defaults/pref/'
        logger.info('push user.js...')
        logger.debug('adb push {} to {}'.format(user_pref_path, user_pref_target_path))
        AdbWrapper.adb_push(user_pref_path, user_pref_target_path, serial=self.serial)

        # push webapps
        webapps_path = os.path.join(unziped_gaia_dir, 'profile', 'webapps')
        webapps_target_path = '/system/b2g/webapps'
        logger.info('push webapps...')
        logger.debug('adb push {} to {}'.format(webapps_path, webapps_target_path))
        AdbWrapper.adb_push(webapps_path, webapps_target_path, serial=self.serial)

        # push settings.json
        settings_path = os.path.join(unziped_gaia_dir, 'profile', 'settings.json')
        settings_target_path = '/system/b2g/defaults/'
        logger.info('push settings.json...')
        logger.debug('adb push {} to {}'.format(settings_path, settings_target_path))
        AdbWrapper.adb_push(settings_path, settings_target_path, serial=self.serial)
        logger.info('Pushing Gaia: Done')

    def _backup_profile(self):
        """
        @return: backup profile's folder.
        """
        profile_dir = tempfile.mkdtemp(prefix='b2gprofile_')
        logger.debug('TEMP profile Folder: {}'.format(profile_dir))
        logger.info('Backup profile to [{}].'.format(profile_dir))
        backup = BackupRestoreHelper()
        backup.set_serial(self.serial)
        backup.set_backup(True)
        backup.set_no_reboot(True)
        backup.set_profile_dir(profile_dir)
        backup.run()
        #backup.backup_profile(local_dir=profile_dir, serial=self.serial)
        return profile_dir

    def _restore_profile(self, profile_dir):
        """
        @param profile_dir: the backup profile's folder.
        """
        if profile_dir:
            logger.info('Restore profile from [{}].'.format(profile_dir))
            backup = BackupRestoreHelper()
            backup.set_serial(self.serial)
            backup.set_restore(True)
            backup.set_no_reboot(True)
            backup.set_skip_version_check(True)
            backup.set_profile_dir(profile_dir)
            backup.run()

    def shallow_flash_gaia(self):
        """
        Shallow flash Gaia.
        """
        logger.info('Shallow flash Gaia: Start')
        tmp_dir = None
        try:
            # keep user profile only work with shallow flash Gaia
            profile_dir = None
            if self.keep_profile:
                profile_dir = self._backup_profile()
            # Create temp folder
            tmp_dir = tempfile.mkdtemp(prefix='shallowflash_')
            logger.debug('TEMP Gaia Folder: {}'.format(tmp_dir))
            # check the Gaia package
            if not self._is_gaia_package(self.gaia):
                raise Exception(
                    '[{}] is not Gaia package. Please check again.'.format(os.path.abspath(self.gaia)))
            # unzip Gaia zip to tmp
            Decompressor().unzip(self.gaia, tmp_dir)
            # clean and push gaia profile
            self._clean_gaia()
            self._push_gaia(tmp_dir)
            # retore profile
            if self.keep_profile:
                self._restore_profile(profile_dir)
        finally:
            if tmp_dir:
                logger.debug('Removing [{0}] folder...'.format(tmp_dir))
                shutil.rmtree(tmp_dir)
                logger.debug('TEMP Gaia Folder was removed: {}'.format(tmp_dir))
        logger.info('Shallow flash Gaia: Done')

    def _clean_gecko(self, source_dir):
        logger.info('Cleaning Gecko profile: Start')
        command_list = ['rm -r /system/media']
        for cmd in command_list:
            AdbWrapper.adb_shell(cmd, serial=self.serial)

        gecko_dir = os.path.join(source_dir, 'b2g')
        source_files = os.listdir(gecko_dir)
        logger.debug('The files which will push into device: {}'.format(source_files))
        adb_stdout, adb_retcode = AdbWrapper.adb_shell('ls /system/b2g/')
        device_files = adb_stdout.split()
        logger.debug('The files which on device /system/b2g/: {}'.format(device_files))
        removed_files = sorted(list(set(source_files + device_files)))
        removed_files.remove('defaults')
        removed_files.remove('webapps')
        logger.debug('Remove files list: {}'.format(removed_files))
        for file in removed_files:
            AdbWrapper.adb_shell('rm -r /system/b2g/{}'.format(file), serial=self.serial)

        logger.info('Cleaning Gecko profile: Done')

    def _push_gecko(self, source_dir):
        # push into device
        logger.info('Pushing Gecko: Start')
        gecko_dir = os.path.join(source_dir, 'b2g')
        # push
        target_path = '/system/b2g/'
        logger.debug('adb push {} to {}'.format(gecko_dir, target_path))
        AdbWrapper.adb_push(gecko_dir, target_path, serial=self.serial)
        # set excutable
        source_files = os.listdir(gecko_dir)
        executable_files = [os.path.join('/system/b2g/', f) for f in source_files if os.access(os.path.join(gecko_dir, f), os.X_OK)]
        logger.debug('Add executed permission on device: {}'.format(executable_files))
        for file in executable_files:
            AdbWrapper.adb_shell('chmod 777 {}'.format(file), serial=self.serial)
        logger.info('Pushing Gecko: Done')

    def shallow_flash_gecko(self):
        """
        Shallow flash Gecko.
        """
        logger.info('Shallow flash Gecko: Start')
        tmp_dir = None
        try:
            # Create temp folder
            tmp_dir = tempfile.mkdtemp(prefix='shallowflash_')
            logger.debug('TEMP Gecko Folder: {}'.format(tmp_dir))
            # check the Gaia package
            if not self._is_gecko_package(self.gecko):
                raise Exception(
                    '[{}] is not Gecko package. Please check again.'.format(os.path.abspath(self.gecko)))
            # unzip Gecko tar.gz to tmp
            Decompressor().untar(self.gecko, tmp_dir)
            # clean and push gecko profile
            self._clean_gecko(tmp_dir)
            self._push_gecko(tmp_dir)
        finally:
            if tmp_dir:
                logger.debug('Removing [{0}] folder...'.format(tmp_dir))
                shutil.rmtree(tmp_dir)
                logger.debug('TEMP Gecko Folder was removed: {}'.format(tmp_dir))
        logger.info('Shallow flash Gecko: Done')

    def prepare_step(self):
        # checking the adb root
        if not AdbWrapper.adb_root(serial=self.serial):
            raise Exception('No root permission for shallow flashing.')
        # checking the adb remount
        if not AdbWrapper.adb_remount(serial=self.serial):
            raise Exception('No permission to remount for shallow flashing.')
        # Stop B2G
        B2GHelper.stop_b2g(serial=self.serial)

    def final_step(self):
        if self.gaia and not self.keep_profile:
            # reset phone when flash gaia and not keep profile
            logger.info('Reset device after shallow flash the Gaia.')
            PhoneReseter().reset_phone(serial=self.serial)
        else:
            # adb shell reboot
            logger.info('Reboot device.')
            AdbWrapper.adb_shell('sync', serial=self.serial)
            AdbWrapper.adb_shell('reboot', serial=self.serial)
        # wait for device, and then check version
        AdbWrapper.adb_wait_for_device(timeout=120)
        logger.info('Check versions.')
        checker = VersionChecker()
        checker.set_serial(self.serial)
        checker.run()

    def run(self):
        """
        Entry point.
        """
        # get the device's serial number
        devices = AdbWrapper.adb_devices()
        if len(devices) == 0:
            raise Exception('No device.')
        else:
            self.serial = AdbHelper.get_serial(self.serial)
            if self.serial is None:
                if len(devices) == 1:
                    logger.debug('No serial, and only one device')
                else:
                    logger.debug('No serial, but there are more than one device')
                    raise Exception('Please specify the device by --serial option.')
            else:
                logger.debug('Setup serial to [{0}]'.format(self.serial))

        if self.gaia or self.gecko:
            self.prepare_step()
            if self.serial:
                logger.info('Target device [{0}]'.format(self.serial))
            if self.gecko:
                self.shallow_flash_gecko()
            if self.gaia:
                self.shallow_flash_gaia()
            self.final_step()


def main():
    try:
        ShallowFlashHelper().cli().run()
    except Exception as e:
        logger.error(e)
        exit(1)


if __name__ == '__main__':
    main()
