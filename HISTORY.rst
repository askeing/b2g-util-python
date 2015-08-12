Release History
---------------

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
