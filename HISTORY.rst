Release History
---------------

0.0.7 (2015-08-20)
++++++++++++++++++

**Features and Improvements**

- Stop backup profil when the folder already exists.
- Refactoring all tools, move prepare() method from __init__() to run().
- Add new argument "--skip-version-check" for backup_restore_profile.
- Extract compare_version(), get_profile_path(), and get_version_from_profile() methods.
- Add docstring for creating the document.
- Add unittest for backup_restore_profile, and adb_helper.
- Update README.

**bugfixes**

- Remove unused code.
- Remove the logger from downloader and decompressor.


0.0.6 (2015-08-14)
++++++++++++++++++

**Features and Improvements**

- Use B2GHelper in b2g_backup_restore_profile.
- Refactoring the check_versions.
- Refactoring the backup_restore_profile

**bugfixes**

- Skip adding setting of enable_certapps_devtools when it doesn't need to restart.


0.0.5 (2015-08-13)
++++++++++++++++++

**Features and Improvements**

- Add **b2g_enable_certapps_devtools** tool.
- Add B2GHelper class for Firefox OS operations.

**bugfixes**

- some command will stop device with no returncode. e.g. adb shell reboot recovery.

0.0.4 (2015-08-12)
++++++++++++++++++
**Features and Improvements**

- Add **b2g_get_crashreports** tool
- Refactoring the ADBWrapper, it will raise exception when command failed.
- Return stdout and return code from device when running adb shell command.

**bugfixes**

- Set backup/restore arguments as required and put them into same group.
- Wait a moment when restarting adbd.

0.0.3 (2015-08-06)
++++++++++++++++++
**Features and Improvements**

- Added the method **AdbHelper.get_serial()** for getting the adb serial number
- Modified the classes of adb_helper
- Modified the code of tools for making them clear

**bugfixes**

- Fixed the **list index out of range** when adb server doesn't start
- Fixed the logger handle issue of tools


0.0.2 (2015-08-05)
++++++++++++++++++
- Rename the tools
    - Added the prefix **b2g_** of tools
- Write the README file


0.0.1 (2015-08-05)
++++++++++++++++++
- Initiate the project
    - Basic ADB commands support
    - The **b2g_backup_restore_profile** (workaround) tool
    - The **b2g_check_versions** tool
    - The **b2g_reset_phone** tool
