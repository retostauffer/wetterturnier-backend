utils.datelock
================

There is a special mechanism to avoid the Wetterturnier backend to compute
or re-compute historical tournaments. This feature has been added due to 
unknown or only partially known changes in the judingclass (how the points
have been computed in the past).

The :doc:`../configfile` has a special ``datelock`` entry. Whenever a script
is triggered for a certain tournament date (days since 1970-01-01) the
:py:meth:`datelock` function evaluates whether you are allowed to perform
the action or not.

.. automodule:: utils
    :members: datelock
