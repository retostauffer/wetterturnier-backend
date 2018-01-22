What  is "Wetterturnier"
-------------------------

The "Berliner Wetterturnier" as it has been known as in the beginning was
launched in the year 2000 at the Institute of Meteorology at the FU Berlin.
Since 2005 five cities in Central Europe are included.

`Wetterturnier <http://wetterturnier.de>`_ is a platform where *hobby meteorologists*,
*experts* and *statistical forecast model developer* battle against each other. The
goal is to predict a set of meteorological variables, such as sunshine duration, wind speed,
or temperature as good as possible for the consecutive two days.

*This plugin is the frontend core* of the whole system providing full wordpress integration
(user management, messaging services, forums) and the platform where our users can *submit
their forecasts/bets*. Furthermore this plugin provides live ranking tables, a leader-board,
a data archive, and access to a set of important data sets such as observations and forecast maps.

.. image:: docs/images/screenshot_frontend.png
   :width: 800px
   :height: 396px
   :scale: 100 %
   :alt: Screenshot Frontend
   :align: center

Please note that this is only one part of the system. To get the whole system running
the `Wetterturnier Wordpress Plugin <https://github.com/retostauffer/wp-wetterturnier>`_.
For more information please visit the `documentation on readthedocs <http://wetterturnier-backend.readthedocs.io/en/latest/overview.html>_`.

Wetterturnier Backend
=====================

.. todo: Show how to install the python package in a virtualenv
    or with pip. State that the setup script already takes care
    of the dependencies. Remove depencency-install-code below.

This is the repository containing the backend scripts
for the new wetterturnier like migration scripts
and other things. 

.. note:: I am using a python virtual environment. If you do so
    as well please keep that in mind.

Warning: there is a virtualenv in this directory.
The virtualenv was build without any site packages 
to be sure to conserve the versions which were running/tested
and to avoid auto-updates by the server OS.

Was built like this:

.. code-block:: bash

    virtualenv --no-site-packages venv

.. note:: This includes that you activate the correct
    virtual environment, even for cronjobs. Therefore
    a cronjob using one of the scripts in here has to look similar
    to this one:

.. code-block:: bash

    */10 * * * *  cd /home/retos/WTbackend && source venv/bin/activate && timeout 900 python Observations.py &> /home/retos/cronlog/Observations.log``
 
Installing necessary packages
------------------------------

If your virtualenv is activated (``source venv/bin/activate``)
you can try to install the *pywetterturnier* package. This
is locted within this repository in PythonPackage.

.. code-block:: bash

    python setup.py install

This should automatically install all necessary dependencies
for the *pywetterturnier* package. However, I had some troubles
as a package called *astral* could not be installed. In this case
you can easily install it manually:

.. code-block:: bash

    pip install astral

Some of the major script files and what they do
===============================================

The documentation is available on `read the docs <http://wetterturnier-backend.readthedocs.io>`_.
Please visit the `documentation <http://wetterturnier-backend.readthedocs.io>`_
where the different main scripts are ducumented in subsection
`getting started - The Scripts <http://wetterturnier-backend.readthedocs.io/en/latest/thescripts.html>`_.

License Information
===================

The software in this repository is free software: you can redistribute it
and/or modify it under the terms of the GNU General Public License as published
by the Free Software Foundation, either version 3 of the License, or (at your
option) any later version. The full :download:`LICENSE` file is included in the repository
and/or can be found on `gnu.org <https://www.gnu.org/licenses/gpl-3.0.txt>`_.

Code of Conduct
===============

We care about oterhs, their attitude, and their ideology wherefore we follow the
[Contributor Covenant][codhomepage] *code of conduct*. The full code of conduct
is included in the repository. If you wanna share ideas and/or contribute to this
repository please follow these rules.

[cochomepage]: http://contributor-covenant.org
[cocversion]: http://contributor-covenant.org/version/1/4/

