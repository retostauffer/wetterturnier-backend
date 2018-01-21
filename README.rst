
This README.md is fully out of date and has to be rewritten.

E-Mail and SMTP Settings
========================

php sendmail does not work on this server as the FU forces
us to use their STMP server (securety issue). The following
e-mail account is therefore used:

Hallo Reto,

wir haben euch die mail-Adresse : wetterturnier@met.fu-berlin.de eingerichtet.
Unser mailserver ist : mail.met.fu-berlin.de
Das P W ist : Di****************

In wordpress nutze ich (Reto) WP-Mail-SMTP mit folgenden Settings:
* SMTP Host:         mail.met.fu-berlin.de
* SMTP Port:         25
* Encryption:        Ust TLS encryption
* Authentication:    Yes, USE SMTP authentication
* Username:          wetterturnier
* Password:          <wie oben>

Benoetigt eine saubere PHPMailer installation am Server.

viele Gruessee

Thomas 

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
