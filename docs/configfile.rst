Configfile
==========

All scripts in this repository use one shared configuration
file read using the `python ConfigParser <https://docs.python.org/2/library/configparser.html>`_
package. The config file is read by the :meth:`utils.readconfig` method
which returns a :obj:`dict` object containing all the required information.

[database]
    Database configuration containing specification for mysql server access,
    namely host, username, password and database name to the database where
    the `Wordpress <https://wordpress.org>`_ with the 
    `Wetterturnier Wordpress Plugin <https://github.com/retostauffer/wp-wetterturnier>`_
    is installed. Details see :doc:`database table documentation </dbtables>`.
    The argument ``mysql_prefix`` specifies the wordpress table prefix and can
    be different from ``wp_`` (wordpress defaulut) if needed.
    ``mysql_obstable`` specifies the database where the observations are stored
    (see :ref:`table description <table-live>`).
[migrate]
    **This is depricated**. Used to migrate the data from the old wetterturnier
    system to the new one on `Wetterturnier.de <http://www.wetterturnier.de>`_.
    Only ``datelock`` is still used.
    
    .. todo:: Remove in the near future. To keep the feature: move
        the datelock into the global config.
[judging]
    Defines (via :obj:`int`) which judging class should be used.
    The scripts will dynamically load the judgingclass object matching
    this specification. Can be used of the rules/judging are getting
    changed.
[system]
    **Depricated**, used for migration.

    .. todo:: Remove in the near future.
[stations]
    **Depricated**, used for migration.

    .. todo:: Remove in the near future.



The :file:`../config.conf.template` configuration file
-------------------------------------------------------

.. note:: The scripts expect the config file to be located in the
    root directory named :file:``config.conf``. This is the template,
    please read the :doc:`getting started <gettingstarted>` section for
    more information.

.. literalinclude:: ../config.conf.template
    :language: python
    :linenos:
