import glob
import os
import sys
from setuptools import setup
from configparser import ConfigParser

# Get some values from the setup.cfg
conf = ConfigParser()
conf.read(['setup.cfg'])
options = dict(conf.items('options'))

install_requires = [s.strip() for s in options.get('install_requires').split('\n')]

# Check if pyqt5 is already installed, whether by pip or some other manager.
# If so, avoid trying to install it again.
try:
    import PyQt5  # noqa
    hasPyQt = True
except ImportError:
    hasPyQt = False
    pass
is_conda = os.path.exists(os.path.join(sys.prefix, 'conda-meta'))
print('is_conda, hasPyQt')
print(is_conda)
print(hasPyQt)
# pyqt5 is named pyqt5 on pypi and pyqt on conda
# due to possible conflicts, skip the pyqt5 requirement in conda environments
# that already have pyqt
# See: https://github.com/biolab/orange3/pull/5593/commits/816f623dd8ffc530e617928eeac67821cd6c3075
if not (hasPyQt and is_conda):
    install_requires.append('PyQt5')
else:
    print('Conda version of PyQt5 already installed')
    if 'PyQt5' in install_requires:
        install_requires.remove('PyQt5')

setup(install_requires=install_requires)
