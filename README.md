
# Wetterturnier Backend

This is the repository containing the backend scripts
for the new wetterturnier like migration scripts
and shit.

##WARNING: python in virtualenv

Warning: there is a virtualenv in this directory.
The virtualenv was build without any site packages 
to be sure to conserve the versions which were running/tested
and to avoid auto-updates by the server OS.

Was built like this:
> virtualenv --no-site-packages venv

Note: this includes that you activate the correct
virtual environment, even for cronjobs. Therefore
a cronjob using one of the scripts in here has to look similar
to this one:
> '*/10 * * * *  cd /home/retos/WTbackend && source venv/bin/activate && timeout 900 python Observations.py &> /home/retos/cronlog/Observations.log'
 
###Installing necessary packages

If your virtualenv is activated (_source venv/bin/activate_)
you can try to install the *pywetterturnier* package. This
is locted within this repository in PythonPackage.

> 'python setup.py install'

This should automatically install all necessary dependencies
for the *pywetterturnier* package. However, I had some troubles
as a package called *astral* could not be installed. In this case
you can easily install it manually:

> 'pip install astral'

## Some of the major script files and what they do

### ComputePoints.py

Computes the points for the bets.

### ComputePetrus.py

Computes Petrus auto bet. During the development
phase I called it Petros2014 (change this after
going online). Using mitteltip.py to compute.

### ComputeMeanBets.py

Computes the group bets based on current active
members and their groups.
Using the same library as Petrus (mitteltip.py).

### migrate.py

Migrates different stuff. Currently groups, 
and their users.

### current.py

Downloading and parsing the wetterturnier webpage,
current tournament, and put everything into the
database. Also creates users if they do not exist.
Please run migrate.py before so that the gorup-users
are well known.

### config.conf

The configuration file with database settings and
other information/flags.
