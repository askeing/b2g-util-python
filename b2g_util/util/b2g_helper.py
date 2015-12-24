# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os
import logging
import tarfile
import zipfile
from adb_helper import AdbWrapper

logger = logging.getLogger(__name__)


class B2GHelper(object):
    @classmethod
    def stop_b2g(cls, serial=None):
        """
        Stop B2G process.
        @return: The stdout and return code. e.g. (stdout, retcode)
        """
        logger.info('Stop B2G.')
        output, retcode = AdbWrapper.adb_shell('stop b2g', serial=serial)
        logger.debug('RetCode: {}, Stdout: {}'.format(retcode, output))

    @classmethod
    def start_b2g(cls, serial=None):
        """
        Start B2G process.
        @return: The stdout and return code. e.g. (stdout, retcode)
        """
        logger.info('Start B2G.')
        output, retcode = AdbWrapper.adb_shell('start b2g', serial=serial)
        logger.debug('RetCode: {}, Stdout: {}'.format(retcode, output))

    @classmethod
    def check_b2g_image(cls, file_path):
        image_magic_folder = 'b2g-distro/'
        logger.debug('check image: {}'.format(file_path))
        if os.path.isfile(file_path) and file_path.endswith('.zip'):
            try:
                with zipfile.ZipFile(file_path, 'r') as f:
                    if image_magic_folder in f.namelist():
                        logger.info('Check B2G image passed: {}'.format(file_path))
                        return True
            except Exception as e:
                logger.debug(e)
                return False
        return False

    @classmethod
    def check_gaia_package(cls, file_path):
        gaia_magic_folder = 'gaia/profile/'
        logger.debug('check gaia: {}'.format(file_path))
        if os.path.isfile(file_path) and file_path.endswith('.zip'):
            try:
                with zipfile.ZipFile(file_path, 'r') as f:
                    if gaia_magic_folder in f.namelist():
                        logger.info('Check Gaia package passed: {}'.format(file_path))
                        return True
            except Exception as e:
                logger.debug(e)
                return False
        return False

    @classmethod
    def check_gecko_package(cls, file_path):
        gecko_magic_folder = 'b2g'
        logger.debug('check gecko: {}'.format(file_path))
        if os.path.isfile(file_path) and file_path.endswith('.tar.gz'):
            try:
                with tarfile.TarFile.open(file_path, 'r:gz') as f:
                    if gecko_magic_folder in f.getnames():
                        logger.info('Check Gecko package passed: {}'.format(file_path))
                        return True
            except Exception as e:
                logger.debug(e)
                return False
        return False
