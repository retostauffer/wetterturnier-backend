The Scripts
===========

The backend consists of a set of scripts performing different tasks like
computing the reference players, mean bets, Sleepy, and judge the forecasts
by pacing the points used for the Wetterturnier ranking.
There is one script called :ref:`Chain.py <script-Chain>` which is the one script
triggered every X minutes. The chain summarizes all (most) of the other scripts
and executes the scripts in the correct order.

The order is important (but not critical) as e.g., the computation of the points
requires valid group bets.

.. todo:: If I would put all code from the modules into a class
    the code the scripts would look way smoother and the chain script
    could be a simple sequential call (obj.dothis,obj.dothat,obj.done).

TestPoints
-----------

.. _script-TestPoints:

Is interfaced by the webserver (needs to be executable for the apache user).
Computes the points and returns them. Can be used by the users to see how
much points they would get given a certain forecast/observation.

Chain
-----

.. _script-Chain:


This is the *main script* used on the operational server.
What :ref:`Chain.py <script-Chain>` does:

* Compute mean group bets (:ref:`ComputeMeanBets <script-MeanBets>`)
* compute :ref:`Petrus <script-Petrus>`
* compute :ref:`Moses <script-Moses>` (only if latest tournament)
* compute :ref:`Persistenz <script-Persistenz>` (only if latest tournament)
* compute :ref:`Points <script-Points>`
* And compute the points for :ref:`Sleepy <script-Sleepy>`.

The scritps (see below) are executed using subprocesses wherefore
:ref:`Chain.py <script-Chain>` has to be started with an active python virtual
environment (if a virtual environment is used) as, if not, the child-nodes
would use the system python installation and might not find the required
packages.

.. code-block:: bash

    source virtualenv/bin/activate
    python Chain.py


Petrus
-------

.. _script-Petrus:

After reading the :doc:`/configfile` the user ID for Petrus is loaded.
If the user does not exist it will be created using a small php script
and the wordpress ``wp_create_user()`` function (see :meth:`database.database.create_user`).

After that the script loops trough all active cities and computes the
overall mean bet (which is Petrus) and saves this reference forecast
into the database.

Persistenz
-----------

.. _script-Persistenz:

After reading the :doc:`/configfile` the user ID for Persistenz is loaded.
If the user does not exist it will be created using a small php script
and the wordpress ``wp_create_user()`` function (see :meth:`database.database.create_user`).

When user created or found the script loads past observations from the
:ref:`wetterturnier_obs <table-wetterturnier-obs>` database table, computes
mean, and submits these values as new reference forecast for Persistenz.


Moses
------

.. _script-Moses:

Moses is a weighted mean of one or more players using some linear
regression approach. The coefficients are computed by Meteo Service.
These files are submitted via ssh to the wetterturnier server in our
live system.

The :ref:`ComputeMoses.py <script-Moses>` searches for the latest coefficient
files, load the required forecasts (per city and parameter) from the database,
loads the forecasted values from the
:ref:`wetterturnier_bets <table-wetterturnier-bets>` database table and computes
the corresponding mean bets which are submitted as Moses.

Sleepy
-------

.. _script-Sleepy:

Sleepy is a non-human player which contains no forecasts but points. These
points are used when computing rankings (e.g., yearly ranking) for players
which have not participated. The Sleepy points are relatively low, wherefore
not participating in the tournament and getting the points Sleepy got is
a penalty.

The script :ref:`ComputeSleepy.py <script-Sleepy>` loops trough the cities,
loads the points via :meth:`database.database.get_sleepy_points`, computes
the mean and saves the mean into the :ref:`wetterturnier_betstat <table-wetterturnier-betstat>`
database table.

Mean Bets
---------

.. _script-MeanBets:

Compute mean forecasts for groups. Loops over all active groups and cities and
extracts the member list from the :ref:`wetterturnier_groupusers <table-wetterturnier-groupusers>`
database table. Only active users.

If more than two group members have submitted a valid forecast for a specific
city the mean bet for this group is computed and stored in the 
:ref:`wetterturnier_bets <table-wetterturnier-bets>` and 
:ref:`wetterturnier_betstat <table-wetterturnier-betstat>` database tables.


Compute Points
--------------

.. _script-Points:

Compute the points for each specific city and parameter for all forecasts
(user forecasts, but also group forecasts/mean bets and reference forecasts).
:ref:`ComputePoints.py <script-Points>` makes use of the :doc:`/judgingclass`
containing the rules.

Requires the bets from the :ref:`wetterturnier_bets <table-wetterturnier-bets>`
database table and the observations from the
:ref:`wetterturnier_obs <table-wetterturnier-obs>` table to compute the residuals
and, based on them, the points.
Which :doc:`judgingclass` is used can be defined via :doc:`/configfile`, the
file is dynamically loaded within :ref:`ComputePoints.py <script-Points>` using
the python `importlib <https://docs.python.org/3/library/importlib.html#module-importlib>` package.
See :doc:`judgingclass` for more details about the judging-class.

At the end of the routine (after all parameter-specifc individual points) are computed
the sum is computed using :meth:`ComputeSumPoints.CSP` method located inside
:file:`../ComputeSumPoints.py`.


Sumpoints
---------

.. _script-SumPoints:

See also :ref:`Compute Points <script-Points>`. This script computes the sum of the
points only. Does not have to be executed when :ref:`ComputePoints.py <script-Points>`
has been executed before as :ref:`ComputePoints.py <script-Points>` automatically
computes the sum points using :meth:`ComputeSumPoints.CSP` from :file:`../ComputeSumPoints.py`.

Ranks Only
-----------

.. _script-RanksOnly:

Computes the rank for a given tournament. Ranks are based on sum points from
`ComputeSumPoints.py <script-SumPoints>`. Stores the rank for each individual
valid forecast into the :ref:`wetterturnier_betstat <table-wetterturnier-betstat>`
table.

Observations
------------

.. _script-Observations:

This script build the bridge between the raw observations stored in the
:ref:`Observation database <database-obs>` talbe 
:ref:`live <table-live>` and the wetterturnier plugin database
:ref:`wetterturnier_obs <table-wetterturnier-obs>`.

Uses the raw observations from :ref:`live <table-live>` to compute the
observations as used for the wetterturnier. Note that this script is also
responsible for the live-ranking. Stores aggregated/derived/selected observations
into the :ref:`wetterturnier_obs <table-wetterturnier-obs>` table.

This script is responsible for the observations which are used for
:ref:`Persistenz <script-Persistenz>` and to compute the 
:ref:`Points <script-Points>` and :ref:`Sum Points <script-SumPoints>` respectively.

**Live-ranking:** for some parameters we are using a live-ranking system.
One of the forecast parameters is the maximum air temperature between
06 and 18 UTC which is reported after 18 UTC. Until we receive the final
'maximum temperature' report we use the 'maximum over the hourly air temperature
observations between 06 and 18 UTC' as a best guess for the maximum temperature.
As soon as the final observation is available we will use the final value.

AstralTable
-----------

.. _script-AstralTable:

Small script to procude the "maximum possible daylength table" for all stations
defined in the database. Procudes an output file containing the day length in hours
for each station for each day of the year (takes 2016, as 2016 was a leap year, such
that also February 29th is included). Uses the same method
:meth:`getobs.get_maximum_Sd` as the backend to convert the observed sunshine duration
into relative sunshine duration.

Creates an output file :file:`AstralTable.txt` alongside the python script which can then
be published/uploaded whereever you want to have it.

.. code-block:: bash

    ## Simply call the script
    ## Keep care of using the python virtualenv if you do use one
    python AstralTable.py

The following astral call is used (excerpt from 
:meth:`getobs.get_maximum_Sd`:

.. code-block:: bash

    ## Setting up location using station longitude/latitude
    loc = astral.Location( (nam,'Region',lat,lon,'Europe/London',elevation) )
    ## Compute sunshine/daylength duration for a specific date
    res = loc.sun(local=True,date=date)
    ## Extract daylength as maximum sunshine duration possible between
    ## sunrise and sunset.
    daylen = int(res['sunset'].strftime('%s')) - int(res['sunrise'].strftime('%s'))
    daylen = daylen / 60.



PrepareMOS
-----------

Klaus Knuepffer is submitting some MOS forecasts for some
stations to the wetterturnier server on ``knuepffer@prognose2.met.fu-berlin.de``.
This small script checks for the latest MOS forecast files,
takes the latest 3 forecast runs, parses the ASCII data and creates
a `json` file. The output is written to the `referrerdata/mos` directory
on the webserver where the frontend acesses the data and provides the
MOS forecasts to our users.

## Who it runs

The job is triggered once an hour via cronjob on ``retos@prognose2``.
The corresponding call is:

.. code-block:: bash
    */60 * * * * cd /home/retos/MOS && timeout 120 python PrepareMOS.py &> /home/retos/cronlog/MOS.log

The following input files will be considered, parsed, prepared ...

* ``/home/knuepffer/abgabe/all.YYmmddHH``

... and stored into the following json file.

* ``/var/www/html/referrerdata/mos/mos.json``

The output file contains a single JSON string of the following form:

.. code-block:: python

    [parameters] (
       [0] => N
       [1] => rSd
       [2] => dd
       [3] => ff
       [4] => fx
       [5] => Wv
       [6] => Wn
       [7] => PPP
       [8] => TTm
       [9] => TTn
       [10] => TTd
       [11] => RR
    )
    [data_1499936400] (
       [WIEN] (
          [DWD-ICON-MOS] (
             [TTm] (
                     [0] => 21.5
                     [1] => 24.9
             )
             [Wv] (
                     [0] => 8
                     [1] => 0
             )
             ...
          )
          [<next model>] ( ... )
          [<next model>] ( ... )
       )
       [<next city] ( ... )
    )
    [<next mos run>] ( ... )

``[parameters]`` contains a list of all parameters and the order they should be
displayed. The data consists of a set of 4-layer nexted data. The first layer
``[data_1499936400]`` indicates the data block with MOS initial time
``1499936400`` (unix timestamp).

Each data block consists of a set of locations (``[WIEN]``) which can contain
one or more different MOS forecasts (``[DWD-ICON-MOS]``).  Each MOS
(``[data_XXXXX][LOCATION][MOS]``) then contains the forecasts given the
parameter name (e.g., ``[TTm]``, ``[Wv]``) and the corresponding values.  On
the frontend the JSON-file is parsed within the script
``wp-wetterturnier/user/views/mosforecasts.php`` and displayed as a table.


