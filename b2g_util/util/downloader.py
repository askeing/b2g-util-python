# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os
import logging
import urllib2
import console_utilities


logger = logging.getLogger(__name__)


class Downloader(object):

    def download(self, source_url, dest_folder, status_callback=None, progress_callback=None):
        try:
            console_utilities.hide_cursor()
            f = urllib2.urlopen(source_url)
            logger.info('Downloading {} ...'.format(os.path.basename(source_url)))
            self.ensure_folder(dest_folder)
            filename_with_path = os.path.join(dest_folder, os.path.basename(source_url))
            with open(filename_with_path, "wb") as local_file:
                total_size = int(f.info().getheader('Content-Length').strip())
                pc = 0
                chunk_size = 8192
                while 1:
                    chunk = f.read(chunk_size)
                    pc += len(chunk)
                    if not chunk:
                        break
                    if progress_callback:
                        progress_callback(current_byte=pc, total_size=total_size)
                    local_file.write(chunk)
            logger.info('Download to {}'.format(filename_with_path))
            console_utilities.show_cursor()
            return filename_with_path
        except urllib2.HTTPError as e:
            logger.error(e)
        except urllib2.URLError as e:
            logger.error(e)

    def ensure_folder(self, folder):
        if not os.path.isdir(folder):
            os.makedirs(folder)
