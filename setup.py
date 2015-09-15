import os
from setuptools import setup, find_packages


VERSION = '0.0.12'

install_requires = []

here = os.path.dirname(os.path.abspath(__file__))
# get documentation from the README and HISTORY
try:
    with open(os.path.join(here, 'README.rst')) as doc:
        readme = doc.read()
except:
    readme = ''

try:
    with open(os.path.join(here, 'HISTORY.rst')) as doc:
        history = doc.read()
except:
    history = ''

long_description = readme + '\n\n' + history

if __name__ == '__main__':
    setup(
        name='b2g_util',
        version=VERSION,
        description='B2G Utilities',
        long_description=long_description,
        keywords='mozilla b2g firefoxos fxos firefox utilities ',
        author='Askeing Yen',
        author_email='askeing@gmail.com',
        url='https://github.com/askeing/b2g-util-python',
        packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
        package_data={},
        install_requires=install_requires,
        zip_safe=False,
        entry_points="""
        # -*- Entry points: -*-
        [console_scripts]
        b2g_backup_restore_profile = b2g_util.backup_restore_profile:main
        b2g_check_versions = b2g_util.check_versions:main
        b2g_enable_certapps_devtools = b2g_util.enable_certapps_devtools:main
        b2g_get_crashreports = b2g_util.get_crashreports:main
        b2g_reset_phone = b2g_util.reset_phone:main
        b2g_shallow_flash = b2g_util.shallow_flash:main
        """,
    )
