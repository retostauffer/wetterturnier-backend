Wetterturnier Wordpress Plugin
===============================

This is the documentation for the 
`wetterturnier.de <http://www.wetterturnier.de>`_
python backend. In combination with the
`Wetterturnier Wordpress Plugin <http://wetterturnier-wordpress-plugin.readthedocs.io/en/latest/>`_
this is the base for a functional Wetterturnier installation.
`This repository <https://github.com/retostauffer/wetterturnier-backend>`_ consists
of a python package and a set of configuration files and *modules*.


.. include:: ../README.rst


Software Dependencies
=====================

Tested with a `mysql 5.1.73 <https://www.mysql.com>`_.
and a `python 2.6.+ <https://python.org>`_ installation.

Python package dependency (see `python package setup script <https://github.com/retostauffer/wetterturnier-backend/blob/master/PythonPackage/setup.py>`_):

* ``numpy`` `numerical python <www.numpy.org>`_ (currently on 1.9.1)
* ``MySQL-python`` `database connection <https://pypi.python.org/pypi/MySQL-python/1.2.5>`_ (currently on 1.2.3c1)
* ``importlib`` `dynamically import modules <https://pypi.python.org/pypi/importlib/1.0.4>`_  (``judgingclass``; currently 1.0.3)
* ``astral`` `to compute sunrise/sunset  <https://pypi.python.org/pypi/astral>`_ (currently 0.8.1)

.. todo:: Astral is available on version 1.4, test and update. Also check
    the other ones on the devel machine, then migrate if all looks good.


Software Overview
=================

Important blocks
-----------------

.. toctree::
    :maxdepth: 1
    :hidden:

    gettingstarted.rst
    configfile.rst
    thescripts.rst

.. toctree::
    :maxdepth: 1
    :hidden:
    :caption: Functions

    function/utils_datelock.rst
    function/utils_inputcheck.rst
    function/utils_readconfig.rst
    function/mitteltip.rst

.. toctree::
    :maxdepth: 1
    :hidden:
    :caption: Classes

    class/database_database.rst
    class/getobs_getobs.rst
    class/stationclass_stationclass.rst
    class/migration.rst

.. toctree::
    :maxdepth: 1
    :caption: MySQL tables

    dbtables.rst



Known Issues
------------
.. _index-known-issues:

As the `<Wetterturnier Wordpress Plugin <https://github.com/retostauffer/wp-wetterturnier>`_
the backend was kept as generic as possible, however, as this is a very specific application
not everything might be fully generic.

.. note::
    * The wetterturnier plugin is designed to forecast the two consecutive days. While
      parts are ready to decrease/increase this number, others are not (e.g., the
      database design is not able to do so).
    * Currently only deterministic forecasts (e.g., 10 degrees celsius for tomorrow noon)
      are possible. Would be quite a bit of effort but cool to also allow for
      probabilistic forecasts/scorings (more state of the art for meteo community)



Full Todo List from The Whole Documentation
===========================================

Full list of all (often duplicated) todos found in the whole documentation.

.. todolist::

