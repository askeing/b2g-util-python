b2g-util-python
===============
.. image:: https://travis-ci.org/askeing/b2g-util-python.svg?branch=master
    :target: https://travis-ci.org/askeing/b2g-util-python

B2G python utilities library, and some tools.


Installation
------------

To install **b2g_util**, simply:

.. code-block:: bash

    $ pip install b2g_util


Tools Usages
------------

There are some available b2g tools.

b2g_backup_restore_profile
++++++++++++++++++++++++++

**Note**: This is a workaround backup/restore solution due to b2g doesn't have tool to backup/restore profile.

.. code-block:: bash

    usage: b2g_backup_restore_profile [-h] [-s SERIAL] (-b | -r) [--sdcard]
                                      [--no-reboot] [-p PROFILE_DIR] [-v]

    Workaround for backing up and restoring Firefox OS profiles. (BETA)

    optional arguments:
      -h, --help            show this help message and exit
      -s SERIAL, --serial SERIAL
                            Directs command to the device or emulator with the
                            given serial number. Overrides ANDROID_SERIAL
                            environment variable. (default: None)
      -b, --backup          Backup user profile. (default: False)
      -r, --restore         Restore user profile. (default: False)
      --sdcard              Also backup/restore SD card. (default: False)
      --no-reboot           Do not reboot B2G after backup/restore. (default:
                            False)
      -p PROFILE_DIR, --profile-dir PROFILE_DIR
                            Specify the profile folder. (default: mozilla-profile)
      -v, --verbose         Turn on verbose output, with all the debug logger.
                            (default: False)


b2g_check_versions
++++++++++++++++++

.. code-block:: bash

    usage: b2g_check_versions [-h] [--no-color] [-s SERIAL] [--log-text LOG_TEXT]
                              [--log-json LOG_JSON] [-v]

    Check the version information of Firefox OS.

    optional arguments:
      -h, --help            show this help message and exit
      --no-color            Do not print with color. NO_COLOR will overrides this
                            option. (default: False)
      -s SERIAL, --serial SERIAL
                            Directs command to the device or emulator with the
                            given serial number. Overrides ANDROID_SERIAL
                            environment variable. (default: None)
      --log-text LOG_TEXT   Text ouput. (default: None)
      --log-json LOG_JSON   JSON output. (default: None)
      -v, --verbose         Turn on verbose output, with all the debug logger.
                            (default: False)


b2g_get_crashreports
++++++++++++++++++++

.. code-block:: bash

    usage: b2g_get_crashreports [-h] [-s SERIAL] [-v]

    Get the Crash Reports from Firefox OS Phone.

    optional arguments:
      -h, --help            show this help message and exit
      -s SERIAL, --serial SERIAL
                            Directs command to the device or emulator with the
                            given serial number. Overrides ANDROID_SERIAL
                            environment variable. (default: None)
      -v, --verbose         Turn on verbose output, with all the debug logger.
                            (default: False)


b2g_reset_phone
+++++++++++++++

.. code-block:: bash

    usage: b2g_reset_phone [-h] [-s SERIAL] [-v]

    Reset Firefox OS Phone.

    optional arguments:
      -h, --help            show this help message and exit
      -s SERIAL, --serial SERIAL
                            Directs command to the device or emulator with the
                            given serial number. Overrides ANDROID_SERIAL
                            environment variable. (default: None)
      -v, --verbose         Turn on verbose output, with all the debug logger.
                            (default: False)
