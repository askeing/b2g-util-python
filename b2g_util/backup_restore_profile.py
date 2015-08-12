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
from datetime import datetime
from argparse import ArgumentDefaultsHelpFormatter
from util.adb_helper import AdbHelper
from util.adb_helper import AdbWrapper


logger = logging.getLogger(__name__)


class BackupRestoreHelper(object):
    def __init__(self, **kwargs):
        self._FILE_PROFILE_INI = 'profiles.ini'
        self._FILE_COMPATIBILITY_INI = 'compatibility.ini'
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

        self.arg_parser = argparse.ArgumentParser(description='Workaround for backing up and restoring Firefox OS profiles. (BETA)',
                                                  formatter_class=ArgumentDefaultsHelpFormatter)
        self.arg_parser.add_argument('-s', '--serial', action='store', dest='serial', default=None, help='Directs command to the device or emulator with the given serial number. Overrides ANDROID_SERIAL environment variable.')
        br_group = self.arg_parser.add_mutually_exclusive_group(required=True)
        br_group.add_argument('-b', '--backup', action='store_true', dest='backup', default=False, help='Backup user profile.')
        br_group.add_argument('-r', '--restore', action='store_true', dest='restore', default=False, help='Restore user profile.')
        self.arg_parser.add_argument('--sdcard', action='store_true', dest='sdcard', default=False, help='Also backup/restore SD card.')
        self.arg_parser.add_argument('--no-reboot', action='store_true', dest='no_reboot', default=False, help='Do not reboot B2G after backup/restore.')
        self.arg_parser.add_argument('-p', '--profile-dir', action='store', dest='profile_dir', default='mozilla-profile', help='Specify the profile folder.')
        self.arg_parser.add_argument('-v', '--verbose', action='store_true', dest='verbose', default=False, help='Turn on verbose output, with all the debug logger.')
        self.args = self.arg_parser.parse_args()
        # setup the logging config
        if self.args.verbose is True:
            verbose_formatter = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            logging.basicConfig(level=logging.DEBUG, format=verbose_formatter)
        else:
            formatter = '%(levelname)s: %(message)s'
            logging.basicConfig(level=logging.INFO, format=formatter)
        AdbWrapper.check_adb()

    def stop_b2g(self, serial=None):
        logger.info('Stop B2G.')
        output, retcode = AdbWrapper.adb_shell('stop b2g', serial=serial)

    def start_b2g(self, serial=None):
        logger.info('Start B2G.')
        output, retcode = AdbWrapper.adb_shell('start b2g', serial=serial)

    def backup_sdcard(self, local_dir, serial=None):
        logger.info('Backing up SD card...')
        # try to get the /sdcard folder on device
        output, retcode = AdbWrapper.adb_shell('ls -d {0}; echo $?'.format(self._REMOTE_DIR_SDCARD), serial=serial)
        output_list = [item for item in re.split(r'\n+', re.sub(r'\r+', '', output)) if item]
        ret_code = output_list[-1]
        output_list.remove(output_list[-1])
        ret_msg = '\n'.join(output_list)
        if ret_code == '0':
            target_dir = local_dir + os.sep + self._LOCAL_DIR_SDCARD + os.sep
            os.makedirs(target_dir)
            logger.info('Backup: {0} to {1}'.format(self._REMOTE_DIR_SDCARD, target_dir))
            try:
                AdbWrapper.adb_pull(self._REMOTE_DIR_SDCARD, target_dir, serial=serial)
            except:
                logger.warning('Can not pull files from {0} to {1}'.format(self._REMOTE_DIR_SDCARD, target_dir))
        else:
            logger.info(ret_msg)
        logger.info('Backup SD card done.')

    def restore_sdcard(self, local_dir, serial=None):
        logger.info('Restoring SD card...')
        target_dir = local_dir + os.sep + self._LOCAL_DIR_SDCARD
        if os.path.isdir(target_dir):
            logger.info('Restore: {0} to {1}'.format(target_dir, self._REMOTE_DIR_SDCARD))
            try:
                AdbWrapper.adb_push(target_dir, self._REMOTE_DIR_SDCARD, serial=serial)
            except:
                logger.warning('Can not push files from {0} to {1}'.format(target_dir, self._REMOTE_DIR_SDCARD))
        else:
            logger.info('{0}: No such file or directory'.format(target_dir))
            return
        logger.info('Restore SD card done.')

    def backup_profile(self, local_dir, serial=None):
        logger.info('Backing up profile...')
        # Backup Wifi
        wifi_dir = local_dir + os.sep + self._LOCAL_DIR_WIFI + os.sep
        wifi_file = local_dir + os.sep + self._LOCAL_FILE_WIFI
        os.makedirs(wifi_dir)
        logger.info('Backing up Wifi information...')
        try:
            AdbWrapper.adb_pull(self._REMOTE_FILE_WIFI, wifi_file, serial=serial)
        except:
            logger.warning('If you don\'t have root permission, you cannot backup Wifi information.')
        # Backup profile
        b2g_mozilla_dir = local_dir + os.sep + self._LOCAL_DIR_B2G + os.sep
        os.makedirs(b2g_mozilla_dir)
        logger.info('Backing up {0} to {1} ...'.format(self._REMOTE_DIR_B2G, b2g_mozilla_dir))
        try:
            AdbWrapper.adb_pull(self._REMOTE_DIR_B2G, b2g_mozilla_dir, serial=serial)
        except:
            logger.warning('Can not pull files from {0} to {1}'.format(self._REMOTE_DIR_B2G, b2g_mozilla_dir))
        # Backup data/local
        datalocal_dir = local_dir + os.sep + self._LOCAL_DIR_DATA + os.sep
        os.makedirs(datalocal_dir)
        logger.info('Backing up {0} to {1} ...'.format(self._REMOTE_DIR_DATA, datalocal_dir))
        try:
            AdbWrapper.adb_pull(self._REMOTE_DIR_DATA, datalocal_dir, serial=serial)
        except:
            logger.warning('Can not pull files from {0} to {1}'.format(self._REMOTE_DIR_DATA, datalocal_dir))
        # Remove "marketplace" app and "gaiamobile.org" apps from webapps
        webapps_dir = datalocal_dir + self._LOCAL_DIR_DATA_APPS
        for root, dirs, files in os.walk(webapps_dir):
            if (os.path.basename(root).startswith('marketplace') or
                os.path.basename(root).endswith('gaiamobile.org') or
                os.path.basename(root).endswith('allizom.org')):
                logger.info('Removing Mozilla webapps: [{0}]'.format(root))
                shutil.rmtree(root)
        logger.info('Backup profile done.')

    def check_profile_version(self, local_dir, serial=None):
        logger.info('Checking profile...')
        # get local version
        if os.path.isdir(local_dir):
            local_config = ConfigParser.ConfigParser()
            local_config.read(local_dir + os.sep + self._LOCAL_DIR_B2G + os.sep + self._FILE_PROFILE_INI)
            local_profile_path = local_config.get('Profile0', 'Path')
            local_config.read(local_dir + os.sep + self._LOCAL_DIR_B2G + os.sep + local_profile_path + os.sep + self._FILE_COMPATIBILITY_INI)
            version_of_backup = local_config.get('Compatibility', 'LastVersion')
            logger.info('The Version of Backup Profile: {}'.format(version_of_backup))
        else:
            return False
        try:
            # get remote version
            tmp_dir = tempfile.mkdtemp(prefix='backup_restore_')
            try:
                AdbWrapper.adb_pull(self._REMOTE_DIR_B2G + os.sep + self._FILE_PROFILE_INI, tmp_dir, serial=serial)
            except:
                logger.warning('Can not pull {2} from {0} to {1}'.format(self._REMOTE_DIR_B2G, tmp_dir, self._FILE_PROFILE_INI))
                return False
            remote_config = ConfigParser.ConfigParser()
            remote_config.read(tmp_dir + os.sep + self._FILE_PROFILE_INI)
            remote_profile_path = remote_config.get('Profile0', 'Path')
            try:
                AdbWrapper.adb_pull(self._REMOTE_DIR_B2G + os.sep + remote_profile_path + os.sep + self._FILE_COMPATIBILITY_INI, tmp_dir, serial=serial)
            except:
                logger.warning('Can not pull {2} from {0} to {1}'.format(self._REMOTE_DIR_B2G, tmp_dir, self._FILE_COMPATIBILITY_INI))
                return False
            remote_config.read(tmp_dir + os.sep + self._FILE_COMPATIBILITY_INI)
            version_of_device = remote_config.get('Compatibility', 'LastVersion')
            logger.info('The Version of Device Profile: {}'.format(version_of_device))
            # compare
            version_of_backup_float = float(version_of_backup.split('.')[0])
            version_of_device_float = float(version_of_device.split('.')[0])
            if version_of_device_float >= version_of_backup_float:
                return True
            else:
                return False
        finally:
            logger.debug('Removing [{0}] folder...'.format(tmp_dir))
            shutil.rmtree(tmp_dir)

    def restore_profile(self, local_dir, serial=None):
        logger.info('Restoring profile...')
        if os.path.isdir(local_dir):
            # Restore Wifi
            wifi_file = local_dir + os.sep + self._LOCAL_FILE_WIFI
            if os.path.isfile(wifi_file):
                logger.info('Restoring Wifi information...')
                try:
                    AdbWrapper.adb_push(wifi_file, self._REMOTE_FILE_WIFI, serial=serial)
                except:
                    logger.warning('If you don\'t have root permission, you cannot restore Wifi information.')
                AdbWrapper.adb_shell('chown {0} {1}'.format(self._REMOTE_FILE_WIFI_OWNER, self._REMOTE_FILE_WIFI))
            # Restore profile
            b2g_mozilla_dir = local_dir + os.sep + self._LOCAL_DIR_B2G
            if os.path.isdir(b2g_mozilla_dir):
                logger.info('Restore from {0} to {1} ...'.format(b2g_mozilla_dir, self._REMOTE_DIR_B2G))
                AdbWrapper.adb_shell('rm -r {0}'.format(self._REMOTE_DIR_B2G))
                try:
                    AdbWrapper.adb_push(b2g_mozilla_dir, self._REMOTE_DIR_B2G, serial=serial)
                except:
                    logger.warning('Can not push files from {0} to {1}'.format(b2g_mozilla_dir, self._REMOTE_DIR_B2G))
            # Restore data/local
            datalocal_dir = local_dir + os.sep + self._LOCAL_DIR_DATA
            if os.path.isdir(datalocal_dir):
                logger.info('Restore from {0} to {1} ...'.format(datalocal_dir, self._REMOTE_DIR_DATA))
                AdbWrapper.adb_shell('rm -r {0}'.format(self._REMOTE_DIR_DATA))
                try:
                    AdbWrapper.adb_push(datalocal_dir, self._REMOTE_DIR_DATA, serial=serial)
                except:
                    logger.warning('Can not push files from {0} to {1}'.format(datalocal_dir, self._REMOTE_DIR_DATA))
            logger.info('Restore profile done.')
        else:
            logger.info('{0}: No such file or directory'.format(local_dir))
            return

    def run(self):
        # get the device's serial number
        devices = AdbWrapper.adb_devices()
        if len(devices) == 0:
            raise Exception('No device.')
        else:
            device_serial = AdbHelper.get_serial(self.args.serial)
            if device_serial is None:
                if len(devices) == 1:
                    logger.debug('No serial, and only one device')
                else:
                    logger.debug('No serial, but there are more than one device')
                    raise Exception('Please specify the device by --serial option.')
            else:
                logger.debug('Setup serial to [{0}]'.format(device_serial))

        # checking the adb root for backup/restore
        if not AdbWrapper.adb_root(serial=device_serial):
            raise Exception('No root permission for backup and resotre.')

        # Backup
        if self.args.backup:
            try:
                logger.info('Target device [{0}]'.format(device_serial))
                # Create temp folder
                tmp_dir = tempfile.mkdtemp(prefix='backup_restore_')
                # Stop B2G
                self.stop_b2g(serial=device_serial)
                # Backup User Profile
                self.backup_profile(local_dir=tmp_dir, serial=device_serial)
                # Backup SDCard
                if self.args.sdcard:
                    self.backup_sdcard(local_dir=tmp_dir, serial=device_serial)
                # Copy backup files from temp folder to target folder
                if os.path.isdir(self.args.profile_dir):
                    logger.warning('Removing [{0}] folder...'.format(self.args.profile_dir))
                    shutil.rmtree(self.args.profile_dir)
                logger.info('Copy profile from [{0}] to [{1}].'.format(tmp_dir, self.args.profile_dir))
                shutil.copytree(tmp_dir, self.args.profile_dir)
                # Start B2G
                if not self.args.no_reboot:
                    self.start_b2g(serial=device_serial)
            finally:
                logger.debug('Removing [{0}] folder...'.format(tmp_dir))
                shutil.rmtree(tmp_dir)
        # Restore
        elif self.args.restore:
            logger.info('Target device [{0}]'.format(device_serial))
            # Checking the Version of Profile
            if self.check_profile_version(local_dir=self.args.profile_dir, serial=device_serial):
                # Stop B2G
                self.stop_b2g(serial=device_serial)
                # Restore User Profile
                self.restore_profile(local_dir=self.args.profile_dir, serial=device_serial)
                # Restore SDCard
                if self.args.sdcard:
                    self.restore_sdcard(local_dir=self.args.profile_dir, serial=device_serial)
                # Start B2G
                if not self.args.no_reboot:
                    self.start_b2g(serial=device_serial)
            else:
                logger.warning('The version on device is smaller than backup\'s version.')


def main():
    try:
        BackupRestoreHelper().run()
    except Exception as e:
        logger.error(e)
        exit(1)


if __name__ == '__main__':
    main()
