import os
from setuptools import setup, find_packages


VERSION='0.0.1'

install_requires = [
#  'taskcluster_util>=0.0.8',
]

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
        keywords='B2G utilities FirefoxOS FxOS ',
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
        backup_restore_profile = b2g_util.backup_restore_profile:main
        check_versions = b2g_util.check_versions:main
        reset_phone = b2g_util.reset_phone:main
        """,
    )

