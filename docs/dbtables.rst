Database Tables
===============

.. _database-obs:

.. _tables:

live
----

.. _table-live:

The ``live`` table is used to store incoming observations.  Please note that
only a subset of all columns is shown in the table below. The script processing
the observations and saving them into this database table automatically creates
additional columns if there are data. ``...`` in the table indicate the data
columns (e.g,. temperature observations, cloud cover observations, ...).

The ``live`` table is a rolling database containing the latest observations for
all incoming stations. The script :ref:`Concuela.py <script-Concuela>` cleans the database from time
to time moving the observations for some specific stations into the
:ref:`archive <table-archive>` database table and deletes all others.

.. todo:: Rename Concuela!


.. include:: dbtables/live.rsx


archive
-------

.. _table-archive:

The archive table has the same structure as the :ref:`live <table-live>`
database table and contains long-term archive data for a set of specified
stations. We keep the data for the tournament stations and drop all others
as we don't want to keep a copy of all observations (would be a huge database
and an unnecessary and unused copy of everything).

.. include:: dbtables/archive.rsx


.. _database-wetterturnier:

wp_wetterturnier_obs
--------------------

.. _table-wetterturnier-obs:

The script :ref:`Observations.py <script-Observations>` is reading the observations from the 
:ref:`live <table-live>` database table and :py:meth:`prepares <getobs.getobs.prepare>`
the observations as they will be used for the ranking. These observations
are stored in this table used by the
`Wetterturnier Wordpress Plugin <https://github.com/retostauffer/wp-wetterturnier>`_
plugin to display the latest observations and by :ref:`Persistenz.py <script-Persistenz>` to submit the
*Persistence reference forecast*.

.. include:: dbtables/wp_wetterturnier_obs.rsx


wp_wetterturnier_param
----------------------

.. _table-wetterturnier-param:

.. include:: dbtables/wp_wetterturnier_param.rsx

wp_wetterturnier_bets
----------------------

.. _table-wetterturnier-bets:

.. include:: dbtables/wp_wetterturnier_bets.rsx

wp_wetterturnier_betstat
------------------------

.. _table-wetterturnier-betstat:

.. include:: dbtables/wp_wetterturnier_betstat.rsx

wp_wetterturnier_stations
-------------------------

.. _table-wetterturnier-stations:

.. include:: dbtables/wp_wetterturnier_stations.rsx

wp_wetterturnier_stationparams
------------------------------

.. _table-wetterturnier-stationparams:

.. include:: dbtables/wp_wetterturnier_stationparams.rsx

wp_wetterturnier_groups
-----------------------

.. _table-wetterturnier-groups:

.. include:: dbtables/wp_wetterturnier_groups.rsx

wp_wetterturnier_groupusers
----------------------------

.. _table-wetterturnier-groupusers:

.. include:: dbtables/wp_wetterturnier_groupusers.rsx














