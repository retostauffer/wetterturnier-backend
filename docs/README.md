
Documentation
=============

Create html pages
-----------------

This is the repository documentation. The documentation
is based on [sphinx-doc](http://www.sphinx-doc.org). To
create the documentation:

``make html``

This creates the html output files in ``_build/html``.

Create database description files
----------------------------------

The documentation contains database schemes inside
the folder ``dbtables``. These files are auto-generated
using the ``autodoc_dbtables.py`` script. To get this
running you need database access to the MySQL tables.
The configuration (database access, what to document)
is set in the ``autodoc_dbtables.conf`` file which is 
read by the python script. To get this thing running:

* Copy ``autodoc_dbtables.conf.template`` to ``autodoc_dbtables.conf``
    and add username and adjust the settings. At least
    usernames and passwords for the MySQL connections have
    to be set.

After that you can run:

``make dbtables``

This once calls ``autodoc_dbtables.py`` to create the
``.rst`` output files into the output file (``dbtables``).
