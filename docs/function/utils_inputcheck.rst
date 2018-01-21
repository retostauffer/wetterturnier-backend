utils.inputcheck
================

All :doc:`../thescripts` provide a set of more or less identical
command line input arguments. The function :py:meth:`utils.inputcheck`
parses these input arguments using pythons `getopt <https://docs.python.org/2/library/getopt.html>`_
package and, if required or requested, shows the correspondingi usage (:py:meth:`utils.usage`).

This method returns a :obj:`list` object with all necessary arguments which
are then used as input for :py:meth:`utils.readconfig`.

.. automodule:: utils
    :members: inputcheck
