# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os
import types
import logging
import tarfile
import zipfile


logger = logging.getLogger(__name__)


class Decompressor(object):

    @classmethod
    def unzip(cls, source_file, dest_folder):
        try:
            logger.info('Unzip {} to {}'.format(source_file, dest_folder))
            zip_file = zipfile.ZipFile(source_file)
            zip_file.extractall(dest_folder)
            zip_file.close()
            logger.info('Unzip done')
        except Exception as e:
            logger.error('Unzip {} Error'.format(source_file))

    @classmethod
    def untar(cls, source_file, dest_folder):
        try:
            logger.info('Untar {} to {}'.format(source_file, dest_folder))
            tar_file = tarfile.open(source_file)
            tar_file.extractall(dest_folder)
            tar_file.close()
            logger.info('Untar done')
        except Exception as e:
            logger.error('Unzip {} Error'.format(source_file))

    @classmethod
    def ensure_folder(cls, folder):
        if not os.path.isdir(folder):
            os.makedirs(folder)
