getobs.getobs
=================

Class to handle requests to the observation database.
Incoming observations are stored in a raw format in the
database, this class is used to :meth:`prepare <getobs.getobs.prepare>`
or compute the observations as needed for the Wetterturnier (the
parameters forecasted). 

.. todo:: Link to repos containing the observation parser.

.. autoclass:: getobs::getobs
    :members:
    :special-members:
    :private-members:


Nested class :class:`getobs.getobs.special_obs_object`
------------------------------------------------------

The :class:`getobs.getobs` contains a nested class called
:class:`getobs.getobs.special_obs_object` to handle ``special`` input
arguments for :meth:`getobs.getobs.get_speical_obs`.

.. autoclass:: getobs::getobs.special_obs_object
    :members:

