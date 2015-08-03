
Wetterturnier Backend
=====================
This is the repository containing the backend scripts
for the new wetterturnier like migration scripts
and shit.

ComputePoints.py
----------------
Computes the points for the bets.

ComputePetrus.py
----------------
Computes Petrus auto bet. During the development
phase I called it Petros2014 (change this after
going online). Using mitteltip.py to compute.

ComputeMeanBets.py
------------------
Computes the group bets based on current active
members and their groups.
Using the same library as Petrus (mitteltip.py).

migrate.py
----------
Migrates different stuff. Currently groups, 
and their users.

current.py
----------
Downloading and parsing the wetterturnier webpage,
current tournament, and put everything into the
database. Also creates users if they do not exist.
Please run migrate.py before so that the gorup-users
are well known.

config.conf
-----------
The configuration file with database settings and
other information/flags.
