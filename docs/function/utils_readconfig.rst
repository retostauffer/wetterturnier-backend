utils.readconfig
================

This is the function which reads/parses the config file which contains all necessary
parameters such as database configuration.

.. todo:: The ``config.conf.template`` and the :py:meth:`utils.readconfig` method
    contain some settings and code lines which were only used to migrate the data
    from the old Wetterturnier system into the new version. Should be cleaned
    somewhen in the near future.

.. note:: Function for reading/parsing the config file. This method is used
    in all :doc:`../thescripts` within the Wetterturnier backend script library.
    This repository contains a `config.conf.template <https://github.com/retostauffer/wetterturnier-backend/blob/master/config.conf.template>`_ 
    template which can be used to produce a custom ``config.conf`` file which is,
    by default, used by the :py:meth:`utils.readconfig` method.
    More details on how to setup the local ``config.conf`` file can be found on the
    :doc:`Getting Started <../gettingstarted>` page in section
    :ref:`Setting up the config.conf file <config-conf-template>`.

.. automodule:: utils
    :members: readconfig
