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
from util.adb_helper import AdbHelper
from util.adb_helper import AdbWrapper
from util.b2g_helper import B2GHelper

logger = logging.getLogger(__name__)


class BackupRestoreHelper(object):
    """
    Workaround for backing up and restoring Firefox OS profiles. (BETA)
    """

    def __init__(self):
        self._FILE_PROFILE_INI = 'profiles.ini'
        self._FILE_COMPATIBILITY_INI = 'compatibility.ini'
        self._FILE_PERF_JS = 'prefs.js'
        self._LOCAL_DIR_SDCARD = 'sdcard'
        self._LOCAL_DIR_WIFI = 'wifi'
        self._LOCAL_FILE_WIFI = 'wifi/wpa_supplicant.conf'
        self._LOCAL_DIR_B2G = 'b2g-mozilla'
        self._LOCAL_DIR_DATA = 'data-local'
        self._LOCAL_DIR_DATA_APPS = 'webapps'
        self._REMOTE_DIR_SDCARD = '/sdcard/'
        self._REMOTE_FILE_WIFI = '/data/misc/wifi/wpa_supplicant.conf'
        self._REMOTE_FILE_WIFI_OWNER = 'system:wifi'
        self._REMOTE_DIR_B2G = '/data/b2g/mozilla'
        self._REMOTE_DIR_DATA = '/data/local'
        # default settings
        self.serial = None
        self.backup = False
        self.restore = False
        self.sdcard = False
        self.no_reboot = False
        self.profile_dir = 'mozilla-profile'
        self.skip_version_check = False

    def set_serial(self, serial):
        """
        Setup the serial number.
        @param serial: the given serial number.
        """
        self.serial = serial
        logger.debug('Set serial: {}'.format(self.serial))

    def set_backup(self, flag):
        """
        Setup the backup flag. If backup is enabled, then resotre will be disable.
        @param flag: True or Flase.
        """
        if flag:
            self.backup = True
            logger.debug('Set backup: {}'.format(self.backup))
            if self.restore:
                self.restore = False
                logger.debug('Set restore: {}, due to backup is enabled'.format(self.restore))
        else:
            self.backup = False
            logger.debug('Set backup: {}'.format(self.backup))

    def set_restore(self, flag):
        """
        Setup the restore flag. If restore is enabled, then backup will be disable.
        @param flag: True or Flase.
        """
        if flag:
            self.restore = True
            logger.debug('Set restore: {}'.format(self.restore))
            if self.backup:
                self.backup = False
                logger.debug('Set backup: {}, due to restore is enabled'.format(self.backup))
        else:
            self.restore = False
            logger.debug('Set restore: {}'.format(self.restore))

    def set_sdcard(self, flag):
        """
        Setup backup or resotre SDCard flag.
        @param flag: True or Flase.
        """
        self.sdcard = flag
        logger.debug('Set sdcard: {}'.format(self.sdcard))

    def set_no_reboot(self, flag):
        """
        Setup no_reboot flag.
        @param flag: True or Flase.
        """
        self.no_reboot = flag
        logger.debug('Set no_reboot: {}'.format(self.no_reboot))

    def set_profile_dir(self, profile_dir):
        """
        Setup profile_dir path.
        @param profile_dir: The path of profile folder.
        """
        self.profile_dir = profile_dir
        logger.debug('Set profile_dir: {}'.format(self.profile_dir))

    def set_skip_version_check(self, flag):
        """
        Setup skip_version_check flag.
        @param flag: True or Flase.
        """
        self.skip_version_check = flag
        logger.debug('Set skip_version_check: {}'.format(self.skip_version_check))

    def cli(self):
        """
        Handle the argument parse, and the return the instance itself.
        """
        # argument parser
        arg_parser = argparse.ArgumentParser(
            description='Workaround for backing up and restoring Firefox OS profiles. (BETA)',
            formatter_class=ArgumentDefaultsHelpFormatter)
        arg_parser.add_argument('-s', '--serial', action='store', dest='serial', default=None,
                                help='Directs command to the device or emulator with the given serial number. '
                                     'Overrides ANDROID_SERIAL environment variable.')
        br_group = arg_parser.add_mutually_exclusive_group(required=True)
        br_group.add_argument('-b', '--backup', action='store_true', dest='backup', default=False,
                              help='Backup user profile.')
        br_group.add_argument('-r', '--restore', action='store_true', dest='restore', default=False,
                              help='Restore user profile.')
        arg_parser.add_argument('--sdcard', action='store_true', dest='sdcard', default=False,
                                help='Also backup/restore SD card.')
        arg_parser.add_argument('--no-reboot', action='store_true', dest='no_reboot', default=False,
                                help='Do not reboot B2G after backup/restore.')
        arg_parser.add_argument('-p', '--profile-dir', action='store', dest='profile_dir', default='mozilla-profile',
                                help='Specify the profile folder.')
        arg_parser.add_argument('--skip-version-check', action='store_true', dest='skip_version_check', default=False,
                                help='Turn off version check between backup profile and device.')
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
        if args.backup:
            self.set_backup(args.backup)
        elif args.restore:
            self.set_restore(args.restore)
        self.set_sdcard(args.sdcard)
        self.set_no_reboot(args.no_reboot)
        self.set_profile_dir(args.profile_dir)
        self.set_skip_version_check(args.skip_version_check)
        # return instance
        return self

    def backup_sdcard(self, local_dir, serial=None):
        """
        Backup data from device's SDCard to local folder.

        @param local_dir: the target local folder, will store data from device's SDCard to this folder.
        """
        logger.info('Backing up SD card...')
        # try to get the /sdcard folder on device
        output, retcode = AdbWrapper.adb_shell('ls -d {0}; echo $?'.format(self._REMOTE_DIR_SDCARD), serial=serial)
        output_list = [item for item in re.split(r'\n+', re.sub(r'\r+', '', output)) if item]
        ret_code = output_list[-1]
        output_list.remove(output_list[-1])
        ret_msg = '\n'.join(output_list)
        if ret_code == '0':
            target_dir = os.path.join(local_dir, self._LOCAL_DIR_SDCARD)
            os.makedirs(target_dir)
            logger.info('Backup: {0} to {1}'.format(self._REMOTE_DIR_SDCARD, target_dir))
            try:
                AdbWrapper.adb_pull(self._REMOTE_DIR_SDCARD, target_dir, serial=serial)
            except Exception as e:
                logger.debug(e)
                logger.error('Can not pull files from {0} to {1}.'.format(self._REMOTE_DIR_SDCARD, target_dir))
            logger.info('Backup SD card done.')
        else:
            logger.info(ret_msg)

    def restore_sdcard(self, local_dir, serial=None):
        """
        Restore data from local folder to device's SDCard.

        @param local_dir: the source local folder, will get data from this folder and than restore to device's SDCard.
        """
        logger.info('Restoring SD card...')
        target_dir = os.path.join(local_dir, self._LOCAL_DIR_SDCARD)
        if os.path.isdir(target_dir):
            logger.info('Restore: {0} to {1}'.format(target_dir, self._REMOTE_DIR_SDCARD))
            try:
                AdbWrapper.adb_push(target_dir, self._REMOTE_DIR_SDCARD, serial=serial)
            except Exception as e:
                logger.debug(e)
                logger.error('Can not push files from {0} to {1}.'.format(target_dir, self._REMOTE_DIR_SDCARD))
            logger.info('Restore SD card done.')
        else:
            logger.info('{0}: No such file or directory'.format(target_dir))

    def backup_profile(self, local_dir, serial=None):
        """
        Backup B2G user profile from device to local folder.

        @param local_dir: the target local folder, the backup data will store to this folder.
        @param serial: device serial number. (optional)
        """
        logger.info('Backing up profile...')
        # Backup Wifi
        wifi_dir = os.path.join(local_dir, self._LOCAL_DIR_WIFI)
        wifi_file = os.path.join(local_dir, self._LOCAL_FILE_WIFI)
        os.makedirs(wifi_dir)
        logger.info('Backing up Wifi information...')
        try:
            AdbWrapper.adb_pull(self._REMOTE_FILE_WIFI, wifi_file, serial=serial)
        except Exception as e:
            logger.debug(e)
            logger.error('If you don\'t have root permission, you cannot backup Wifi information.')
        # Backup profile
        b2g_mozilla_dir = os.path.join(local_dir, self._LOCAL_DIR_B2G)
        os.makedirs(b2g_mozilla_dir)
        logger.info('Backing up {0} to {1} ...'.format(self._REMOTE_DIR_B2G, b2g_mozilla_dir))
        try:
            AdbWrapper.adb_pull(self._REMOTE_DIR_B2G, b2g_mozilla_dir, serial=serial)
        except Exception as e:
            logger.debug(e)
            logger.error('Can not pull files from {0} to {1}'.format(self._REMOTE_DIR_B2G, b2g_mozilla_dir))
        # Backup data/local
        datalocal_dir = os.path.join(local_dir, self._LOCAL_DIR_DATA)
        os.makedirs(datalocal_dir)
        logger.info('Backing up {0} to {1} ...'.format(self._REMOTE_DIR_DATA, datalocal_dir))
        try:
            AdbWrapper.adb_pull(self._REMOTE_DIR_DATA, datalocal_dir, serial=serial)
        except Exception as e:
            logger.debug(e)
            logger.error('Can not pull files from {0} to {1}'.format(self._REMOTE_DIR_DATA, datalocal_dir))

        # remove gecko.mstone value, so that gecko can check the apps under /system/b2g/webapps again.
        # (Thanks SC Chien's help!)
        local_profile_path = self._get_profile_path(os.path.join(b2g_mozilla_dir, self._FILE_PROFILE_INI))
        local_perf = os.path.join(b2g_mozilla_dir, local_profile_path, self._FILE_PERF_JS)
        perf_contents = []
        with open(local_perf, 'r') as f:
            for line in f.readlines():
                if 'gecko.mstone' not in line:
                    perf_contents.append(line)
                else:
                    logger.debug('Remove from {}: {}'.format(local_perf, line))
        with open(local_perf, 'w') as f:
            for line in perf_contents:
                f.write(line)
        logger.info('Backup profile done.')

    @staticmethod
    def _compare_version(version_of_backup, version_of_device):
        """
        Compare two B2G versions.

        @param version_of_backup: the local backup profile's version string.
        @param version_of_device: the device profile's version string.

        @return: True if the backup profile's version less than or equal to device's version.

        @raise exception: if  the backup profile's version large than device's version.
        """
        version_of_backup_float = float(version_of_backup.split('.')[0])
        version_of_device_float = float(version_of_device.split('.')[0])
        if version_of_backup_float <= version_of_device_float:
            logger.info(
                'Backup Profile {} <= Device Profile {}'.format(version_of_backup_float, version_of_device_float))
            return True
        else:
            raise Exception(
                'Backup Profile {} > Device Profile {}'.format(version_of_backup_float, version_of_device_float))

    @staticmethod
    def _get_profile_path(ini_file_path):
        """
        Get the B2G profile's folder name from profile.ini file.
        (e.g. /data/b2g/mozilla/profiles.ini on device.)

        @param ini_file_path: the profile.ini file.

        @return: the profile folder name.

        @raise exception: if cannot get the profile folder name.
        """
        ini_config = ConfigParser.ConfigParser()
        try:
            ini_config.read(ini_file_path)
            profile_path = ini_config.get('Profile0', 'Path')
            logger.debug('Load [{}]: {}'.format(ini_file_path, ini_config._sections))
            return profile_path
        except:
            raise Exception(
                'Can not get profile path from [{}], content: {}'.format(ini_file_path, ini_config._sections))

    @staticmethod
    def _get_version_from_profile(ini_file_path):
        """
        Get the B2G last version from compatibility.ini file.
        (e.g. /data/b2g/mozilla/<PROFILE_FOLDER>/compatibility.ini on device.)

        @param ini_file_path: the compatibility.ini file.

        @return: the last version.

        @raise exception: if cannot get the version.
        """
        ini_config = ConfigParser.ConfigParser()
        try:
            ini_config.read(ini_file_path)
            last_version = ini_config.get('Compatibility', 'LastVersion')
            logger.debug('Load [{}]: {}'.format(ini_file_path, ini_config._sections))
            logger.info('The LastVersion of [{}] is [{}]'.format(ini_file_path, last_version))
            return last_version
        except:
            raise Exception(
                'Can not get last version from [{}], content: {}'.format(ini_file_path, ini_config._sections))

    def _check_profile_version(self, local_dir, serial=None):
        """
        Check the versions of backup and device.
        The lower backup can restore to device. However the higher backup cannot.

        @param local_dir: the local backup folder.
        @param serial: device serial number. (optional)

        @return: True if backup version is lower than device's.

        @raise exception: if cannot load profiles or versions.
        """
        if self.skip_version_check:
            logger.info('Skip version check.')
            return True
        logger.info('Checking profile...')
        # get local version
        if os.path.isdir(local_dir):
            local_profile_path = self._get_profile_path(
                os.path.join(local_dir, self._LOCAL_DIR_B2G, self._FILE_PROFILE_INI))
            version_of_backup = self._get_version_from_profile(
                os.path.join(local_dir, self._LOCAL_DIR_B2G, local_profile_path, self._FILE_COMPATIBILITY_INI))
        else:
            raise Exception('Can not load profile from [{}]'.format(os.path.abspath(local_dir)))
        tmp_dir = None
        try:
            # get remote version
            tmp_dir = tempfile.mkdtemp(prefix='backup_restore_')
            logger.debug('TEMP Folder for check profile: {}'.format(tmp_dir))
            try:
                AdbWrapper.adb_pull(os.path.join(self._REMOTE_DIR_B2G, self._FILE_PROFILE_INI), tmp_dir, serial=serial)
            except:
                raise Exception(
                    'Can not pull {2} from {0} to {1}. '
                    'Please run with --skip-version-check if you want to restore.'.format(
                        self._REMOTE_DIR_B2G, tmp_dir, self._FILE_PROFILE_INI))
            remote_profile_path = self._get_profile_path(os.path.join(tmp_dir, self._FILE_PROFILE_INI))
            try:
                AdbWrapper.adb_pull(
                    os.path.join(self._REMOTE_DIR_B2G, remote_profile_path, self._FILE_COMPATIBILITY_INI), tmp_dir,
                    serial=serial)
            except:
                raise Exception(
                    'Can not pull {2} from {0} to {1}. '
                    'Please run with --skip-version-check if you want to restore.'.format(
                        self._REMOTE_DIR_B2G, tmp_dir, self._FILE_COMPATIBILITY_INI))
            version_of_device = self._get_version_from_profile(
                os.path.join(os.path.join(tmp_dir, self._FILE_COMPATIBILITY_INI)))
            # compare
            return self._compare_version(version_of_backup, version_of_device)
        finally:
            if tmp_dir:
                logger.debug('Removing [{0}] folder...'.format(tmp_dir))
                shutil.rmtree(tmp_dir)
                logger.debug('TEMP Folder for check profile removed: {}'.format(tmp_dir))

    def restore_profile(self, local_dir, serial=None):
        """
        Restore B2G user profile from local folder to device.

        @param local_dir: the source local folder, the backup data will restore from this folder.
        @param serial: device serial number. (optional)
        """
        logger.info('Restoring profile...')
        if os.path.isdir(local_dir):
            # Restore Wifi
            wifi_file = os.path.join(local_dir, self._LOCAL_FILE_WIFI)
            if os.path.isfile(wifi_file):
                logger.info('Restoring Wifi information...')
                try:
                    AdbWrapper.adb_push(wifi_file, self._REMOTE_FILE_WIFI, serial=serial)
                except Exception as e:
                    logger.debug(e)
                    logger.error('If you don\'t have root permission, you cannot restore Wifi information.')
                AdbWrapper.adb_shell('chown {0} {1}'.format(self._REMOTE_FILE_WIFI_OWNER, self._REMOTE_FILE_WIFI))
            # Restore profile
            b2g_mozilla_dir = os.path.join(local_dir, self._LOCAL_DIR_B2G)
            if os.path.isdir(b2g_mozilla_dir):
                logger.info('Restore from {0} to {1} ...'.format(b2g_mozilla_dir, self._REMOTE_DIR_B2G))
                AdbWrapper.adb_shell('rm -r {0}'.format(self._REMOTE_DIR_B2G))
                try:
                    AdbWrapper.adb_push(b2g_mozilla_dir, self._REMOTE_DIR_B2G, serial=serial)
                except Exception as e:
                    logger.debug(e)
                    logger.error('Can not push files from {0} to {1}'.format(b2g_mozilla_dir, self._REMOTE_DIR_B2G))
            # Restore data/local
            datalocal_dir = os.path.join(local_dir, self._LOCAL_DIR_DATA)
            if os.path.isdir(datalocal_dir):
                logger.info('Restore from {0} to {1} ...'.format(datalocal_dir, self._REMOTE_DIR_DATA))
                AdbWrapper.adb_shell('rm -r {0}'.format(self._REMOTE_DIR_DATA))
                try:
                    AdbWrapper.adb_push(datalocal_dir, self._REMOTE_DIR_DATA, serial=serial)
                except Exception as e:
                    logger.debug(e)
                    logger.error('Can not push files from {0} to {1}'.format(datalocal_dir, self._REMOTE_DIR_DATA))
            logger.info('Restore profile done.')
        else:
            logger.info('{0}: No such file or directory'.format(local_dir))

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

        # checking the adb root for backup/restore
        if not AdbWrapper.adb_root(serial=self.serial):
            raise Exception('No root permission for backup and resotre.')

        if self.serial:
            logger.info('Target device [{0}]'.format(self.serial))
        # Backup
        if self.backup:
            tmp_dir = None
            try:
                # Create temp folder
                tmp_dir = tempfile.mkdtemp(prefix='backup_restore_')
                logger.debug('TEMP Foler: {}'.format(tmp_dir))
                # check the local profile folder
                if os.path.isdir(self.profile_dir):
                    if len(os.listdir(self.profile_dir)) == 0:
                        logger.debug('{} is empty. Clean it.')
                        shutil.rmtree(self.profile_dir)
                    else:
                        raise Exception(
                            '[{0}] folder already exists. Please check again.'.format(os.path.abspath(self.profile_dir)))
                # Stop B2G
                B2GHelper.stop_b2g(serial=self.serial)
                # Backup User Profile
                self.backup_profile(local_dir=tmp_dir, serial=self.serial)
                # Backup SDCard
                if self.sdcard:
                    self.backup_sdcard(local_dir=tmp_dir, serial=self.serial)
                # Copy backup files from temp folder to target folder
                logger.info('Copy profile from [{0}] to [{1}].'.format(tmp_dir, self.profile_dir))
                shutil.copytree(tmp_dir, self.profile_dir)
                # Start B2G
                if not self.no_reboot:
                    B2GHelper.start_b2g(serial=self.serial)
            finally:
                if tmp_dir:
                    logger.debug('Removing [{0}] folder...'.format(tmp_dir))
                    shutil.rmtree(tmp_dir)
                    logger.debug('TEMP Folder for backup removed: {}'.format(tmp_dir))
        # Restore
        elif self.restore:
            # Checking the Version of Profile
            if self._check_profile_version(local_dir=self.profile_dir, serial=self.serial):
                # Stop B2G
                B2GHelper.stop_b2g(serial=self.serial)
                # Restore User Profile
                self.restore_profile(local_dir=self.profile_dir, serial=self.serial)
                # Restore SDCard
                if self.sdcard:
                    self.restore_sdcard(local_dir=self.profile_dir, serial=self.serial)
                # Start B2G
                if not self.no_reboot:
                    B2GHelper.start_b2g(serial=self.serial)
            else:
                logger.error('The version on device is smaller than backup\'s version.')


def main():
    try:
        BackupRestoreHelper().cli().run()
    except Exception as e:
        logger.error(e)
        exit(1)


if __name__ == '__main__':
    main()
