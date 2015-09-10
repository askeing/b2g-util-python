b2g-util-python
===============
.. image:: https://travis-ci.org/askeing/b2g-util-python.svg?branch=master
    :target: https://travis-ci.org/askeing/b2g-util-python

B2G python utilities library, and some tools.


Installation
------------

To install **b2g_util**, simply running then following command.

Note: You might have to add **sudo** for getting more permission when install it into your system.

.. code-block:: bash

    $ pip install -U b2g_util

And the **pip** and **setuptools** should be upgraded to latest version before install.

.. code-block:: bash

    $ sudo pip install -U pip setuptools


Tools Usages
------------

There are some available b2g tools.

- b2g_backup_restore_profile
- b2g_check_versions
- b2g_enable_certapps_devtools
- b2g_get_crashreports
- b2g_reset_phone
- b2g_shallow_flash


b2g_backup_restore_profile
++++++++++++++++++++++++++

**Note**: This is a workaround backup/restore solution due to b2g doesn't have tool to backup/restore profile.

.. code-block:: bash

    usage: b2g_backup_restore_profile [-h] [-s SERIAL] (-b | -r) [--sdcard]
                                      [--no-reboot] [-p PROFILE_DIR]
                                      [--skip-version-check] [-v]

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
      --skip-version-check  Turn off version check between backup profile and
                            device. (default: False)
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


b2g_enable_certapps_devtools
++++++++++++++++++++++++++++

.. code-block:: bash

    usage: b2g_enable_certapps_devtools [-h] [-s SERIAL] [--disable] [-v]

    Enable/disable Certified Apps Debugging.

    optional arguments:
      -h, --help            show this help message and exit
      -s SERIAL, --serial SERIAL
                            Directs command to the device or emulator with the
                            given serial number. Overrides ANDROID_SERIAL
                            environment variable. (default: None)
      --disable             Disable the privileges. (default: False)
      -v, --verbose         Turn on verbose output, with all the debug logger.
                            (default: False)

    Please enable "ADB and Devtools" of device.
    Ref:
    - https://developer.mozilla.org/en-US/docs/Tools/WebIDE
    - https://developer.mozilla.org/en-US/docs/Tools/WebIDE/Running_and_debugging_apps#Debugging_apps


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


b2g_shallow_flash
+++++++++++++++++

.. code-block:: bash

    usage: b2g_shallow_flash [-h] [-s SERIAL] [-g GAIA] [-G GECKO]
                             [--keep-profile] [-v]

    Workaround for shallow flash Gaia or Gecko into device.

    optional arguments:
      -h, --help            show this help message and exit
      -s SERIAL, --serial SERIAL
                            Directs command to the device or emulator with the
                            given serial number. Overrides ANDROID_SERIAL
                            environment variable. (default: None)
      -g GAIA, --gaia GAIA  Specify the Gaia package. (zip format) (default: None)
      -G GECKO, --gecko GECKO
                            Specify the Gecko package. (tar.gz format) (default:
                            None)
      --keep-profile        Keep user profile of device. Only work with shallow
                            flash Gaia. (BETA) (default: False)
      -v, --verbose         Turn on verbose output, with all the debug logger.
                            (default: False)


Development
-----------

To develop the **b2g_util**, fork project from `Github <https://github.com/askeing/b2g-util-python.git>`_ and simply:

.. code-block:: bash

    $ git clone https://github.com/<YOUR_ACCOUNT>/b2g-util-python.git
    $ cd b2g-util-python
    $ make dev-env
    $ source env-python/bin/activate

Or you can run tests:

.. code-block:: bash

    $ make test

You also can create the document, and then you can open **docs/index.html** to access the document.

.. code-block:: bash

    $ make docs

