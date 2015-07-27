import os
from setuptools import setup, find_packages


VERSION='0.0.1'

install_requires = [
#  'taskcluster_util>=0.0.8',
]

here = os.path.dirname(os.path.abspath(__file__))
# get documentation from the README
try:
    with open(os.path.join(here, 'README.rst')) as doc:
        long_description = doc.read()
except:
    long_description = ''


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
    )

