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
- b2g_flash_taskcluster
- b2g_get_crashreports
- b2g_quick_flash
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


b2g_flash_taskcluster
+++++++++++++++++++++

.. code-block:: bash

    usage: b2g_flash_taskcluster [-h] [--credentials CREDENTIALS] [-n NAMESPACE]
                                 [-d DEST_DIR] [-v]

    The simple GUI tool for flashing B2G from Taskcluster.

    optional arguments:
      -h, --help            show this help message and exit
      --credentials CREDENTIALS
                            The credential JSON file
                            (default: /home/askeing/tc_credentials.json)
      -n NAMESPACE, --namespace NAMESPACE
                            The namespace of task
      -d DEST_DIR, --dest-dir DEST_DIR
                            The dest folder (default: current working folder)
      -v, --verbose         Turn on verbose output, with all the debug logger.

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

Temporary Credentials
*********************

You can get your temporary credentials from https://auth.taskcluster.net/ (using Persona with LDAP account).

The temporary credentials will remain valid for 31 days.

Or you can just run **taskcluster_login** to get your credentials. (Note: it will remove your old credentials file.)

tc_credentials.json
~~~~~~~~~~~~~~~~~~~

You can put the credentials into **tc_credentials.json** file under your home folder.

.. code-block:: bash

    $ <YOUR_EDITOR> ~/tc_credentials.json

The file format will be:

.. code-block::

    {
		"clientId": "<YOUR_CLIENTID>",
		"accessToken": "<YOUR_ACCESSTOKEN>",
		"certificate": <YOUR_CERTIFICATE>
	}


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


b2g_quick_flash
+++++++++++++++

.. code-block:: bash

    usage: b2g_quick_flash [-h] [-l] [-v]

    Simply flash B2G into device. Ver. 0.0.1

    optional arguments:
      -h, --help     show this help message and exit
      -l, --list     List supported devices and branches. (default: False)
      -v, --verbose  Turn on verbose output, with all the debug logger. (default:
                     False)


Temporary Credentials
*********************

See **b2g_flash_taskcluster** session.


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


SSL InsecurePlatformWarning
---------------------------

If you got the following error message when running the tools, please install **requests[security]** package.

.. code-block:: bash

    InsecurePlatformWarning: A true SSLContext object is not available.
    This prevents urllib3 from configuring SSL appropriately and may cause certain SSL connections to fail.
    For more information, see https://urllib3.readthedocs.org/en/latest/security.html#insecureplatformwarning.


Install package by pip install. Please note it's not required for Python 2.7.9+.

.. code-block:: bash

    pip install requests[security]

If you got **Setup script exited with error: command 'gcc' failed with exit status 1** error when install **requests[security]**, please install **libffi-dev**. (Ubuntu)

.. code-block:: bash

    sudo apt-get install libffi-dev


The Other Issues
----------------

If you meet any issues related to urllib3, SSL, or tk, please install following packages. (Ubuntu)

.. code-block:: bash

    sudo apt-get install python python-dev python-setuptools libffi-dev libssl-dev python-tk
    sudo easy_install pip
    sudo pip install -U pip setuptools
    sudo pip install -U requests
    sudo pip install -U requests[security]
