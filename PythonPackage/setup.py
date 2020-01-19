# -------------------------------------------------------------------
# - NAME:        setup.py
# - AUTHOR:      Reto Stauffer
# - DATE:        2015-08-03
# - LICENSE: GPL-3, Reto Stauffer, copyright 2014
# -------------------------------------------------------------------
# - DESCRIPTION: I have created a python package for more propper
#                update/version handling.
#                This is the setuptool setup script for
#                the package called pywetterturnier. All dependencies
#                should be included - after the installation
#                you should be ready.
#
#                Note that if you would like to work on a virtual
#                environment: be sure that you have activated the
#                correct virtualenv. Then call
#                - python setup.py install
#
#                Should install a package called pywetterturnier
#                plus the necessary dependencies.
# -------------------------------------------------------------------
# - EDITORIAL:   2015-08-03, RS: Created file on thinkreto.
# -------------------------------------------------------------------
# - L@ST MODIFIED: 2015-08-03 16:21 on prognose2.met.fu-berlin.de
# -------------------------------------------------------------------
from setuptools import setup

setup(name='pywetterturnier',     # This is the package name
      version='0.1-0',            # Current package version, what else
      description='The Wetterturnier Python Backend Package',
      long_description='This is only the backend code.',
      classifiers=[
        'Development Status :: 4 - Beta',
        'GNU Lesser General Public License v3 or later (LGPLv3+)',
        'Programming Language :: Python :: 2.7',
      ],
      keywords='wetterturnier wetter tippspiel',
      url='https://bitbucket.org/retos/prognose2-www-repository',
      author='Reto Stauffer',
      author_email='reto.stauffer@uibk.ac.at',
      license='GPL-3',
      packages=['pywetterturnier'],
      install_requires=[
          'numpy',        # everyone needs it!
          'matplotlib',   # plotting nice graphs
          'scipy',        # curve fitting
          'MySQL-python', # MySQL connection
          #MySQL-python not supported anymore in python3!
          #'mysqlclient',  # new client version 1.4.4 since 1.4.5 didn't work
          'importlib',    # Used to load the judgingclasses dynamically
          'python-dateutil',
          'pytz',         # Required by astral
          'astral',       # Used to compute astronomic sunshine duration
          'pandas',       # exporting data frames
          'xlwt',         # to excel (.xls)
      ],
      czip_safe=False)
