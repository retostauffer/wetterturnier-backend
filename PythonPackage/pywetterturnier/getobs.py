# -------------------------------------------------------------------
# - NAME:        getobs.py
# - AUTHOR:      Reto Stauffer
# - DATE:        2015-07-23
# -------------------------------------------------------------------
# - DESCRIPTION: A class which picks observations from the
#                'raw' observation table and prepares the inserts
#                we need to compute the points for the tournament.
# -------------------------------------------------------------------
# - EDITORIAL:   2015-07-23, RS: Created file on thinkreto.
# -------------------------------------------------------------------
# - L@ST MODIFIED: 2018-01-24 12:50 on marvin
# -------------------------------------------------------------------

import sys, os
import datetime as dt
import numpy as np

class getobs( object ):
   """
   Main observation handling class. Loading observations from the
   'raw' database (Obsdatabase) and computes the observations required
   for the tournament (e.g, daily sunshine duration or precipitation sums
   (sum over 24h between pre-specified times).
   These values are stored into the `Wetterturnier Wordpress Plugin <https://github.com/retostauffer/wp-wetterturnier>`_
   and used for the penalties/judging.
 
   Args:
      config (:obj:`list`): Contains all necessary configs for the
             pywetterturnier package. Please have a look into 
             See :py:meth:`utils.readconfig` for more details. 
      db (:py:class:`database.database`): A pywetterturnier 
             (:py:class:`database.database` object handling the database I/O.
      city (:obj:`int`): Numeric city ID.
      date (:obj:`datetime.datetime.date` object with the date for which
             the request should be made.
      wmoww (:obj:`utils.wmowwConversion`): Or None. If None, no conversion will
             be performed. If set the :meth:`utils.wmowwConversion.convert` method is used to convert observed weather codes into the required ones.
   """


   def __init__(self, config, db, city, date, wmoww = None ):
      """
      Initialization of the @ref getobs.getobs class.
      """
      
      import numpy as np

      # -------------------------------------------------------------
      # Public attributes
      # -------------------------------------------------------------
      ## @ref database.database object handling the db I/O.
      self.db     = db
      ## Will contain data. Intitialized as None, will be a
      #  2-level deep dict at the end of the form: 
      #  data[wmo station number][parameter] = observation value.
      self.data     = None
      ## List of stationclass objects
      from .utils import datetime2tdate
      self.tdate = datetime2tdate( date )
      self.stations = self.db.get_stations_for_city( city['ID'], tdate = self.tdate )
      ## Store wmoww input arg
      self.wmoww    = wmoww

      # -------------------------------------------------------------
      # - Private attributes
      # -------------------------------------------------------------
      ## Copy of the input config list
      self._config_  = config
      ## Database table name.
      self._table_   = config['mysql_obstable'] 
      ## City ID for which we are loading the observations.
      self._city_    = city
      ## Date of the observations.
      self._date_    = date
      ## Columns available in in self._table_
      self._columns_ = self.get_columns( self._table_ )
      if len(self.stations) == 0: return False
      ## Dict with astronomic day length per station.
      self._maxSd_    = self.get_maximum_Sd(self.stations,self._date_)


   # ----------------------------------------------------------------
   # - Compute maximum day length using the python astral package.
   # ----------------------------------------------------------------
   def get_maximum_Sd( self, stations, date ):
      """Computes astronomic (maximum) sun shine duration for a set
      of stations. Note that the station has to be stored in the database
      table ``obs.stations``. If not, we dont know the position of the   
      station and therefore we can't compute astronomical sunshine
      duration resulting in a None value.
      Uses external python package @astral.

      Args:
         stations (:obj:`list`): of :py:obj:`stationclass.stationclass` objects.
         date (:obj:`datetime.datetime.date`): Date object for which the data should
            be retrieved or for which date the day length should be computed.
      
      Returns:
         dict: A dict consisting of WMO station number and
         the length of the astronomic day in seconds. 
      """

      import astral
      #needed for astral version 2+
      from astral.sun import sun
      from datetime import datetime as dt

      # - self._maxSd_ used to store the info based on the wmo number
      maxSd = {}
      cur = self.db.cursor()
      sql = "SELECT name, lon, lat, hoehe, hbaro FROM obs.stations WHERE statnr = %s"
      for station in stations:
         cur.execute( sql % station.wmo )
         res = cur.fetchone()

         # - no info? Skip
         if res == None:
            maxSd[station.wmo] = None
            print("[!] ERROR: Problems in get_maximum_Sd. Reason: \n" + \
                  "    there is no entry for wmo station %d in table\n" % station.wmo + \
                  "    obs.stations and I can't compute the astronomic\n" + \
                  "    sunshine duration.")
            maxSd[station.wmo] = None
      
         # - Else
         else:

            # - Else compute day length
            nam = str(   res[0] )
            lon = float( res[1] )
            lat = float( res[2] )
            hoehe = int( res[3] )
            hbaro = int( res[4] )
            if int( hoehe ) == None:
               if int( hbaro ) in [None,-999]:
                  elevation = 0
               else:
                  elevation = int( hbaro )
            else:
               elevation = int( hoehe )
            
            print(elevation)

            #old pre astral2 version
            #loc = astral.Location( (nam,'Region',lat,lon,'Europe/London',elevation) )
            #res = loc.sun(local=True,date=date)
            
            # - Define location (no elevation)
            loc = astral.LocationInfo( nam,'Europe','UTC',latitude=lat,longitude=lon )
            res = sun(loc.observer,date=date)
            
            # - Define observer (station with elevation)
            #obs = astral.Observer(lat, lon, elevation)
            #res = sun(obs, date=date)

            daylen = int(res['sunset'].strftime('%s')) - int(res['sunrise'].strftime('%s'))
            daylen = daylen / 60.

            maxSd[station.wmo] = daylen

            print("    WMO station %7d: daylength %5.2f min (%5.2f h)" % \
                   (station.wmo,daylen,daylen/60.))

      return maxSd


   # ----------------------------------------------------------------
   # - Loading 
   # ----------------------------------------------------------------
   def get_columns( self, table ):
      """Returns database table columns.

      Args:
         table (:obj:`str`): Name of the database table.

      Results:
         list: A list of all available table columns.

      .. todo:: reference to database required here.
      """

      sql = "SHOW COLUMNS FROM %s" % table
      cur = self.db.cursor()
      cur.execute(sql)

      return [str( i[0] ).lower() for i in cur.fetchall()]

   # ----------------------------------------------------------------
   # - Loading observations
   # ----------------------------------------------------------------
   def load_obs( self, wmo, hour, parameter, min50=0 ):
      """Loading a specific observation from the database.
      The date for which the observation should be valid and the
      name of the database are coming from the public attributes of the
      class (@ref getobs.getobs).

      Args:
         wmo (:obj:`int`):  Numeric WMO station number.
         hour (:obj:`int`): Hour for which the observation should
                            be valid [0,...,24], in UTC.
         parameter (:obj:`str`): Parameter name (short name) for which
                            observations should be loaded.

      Returns:
         :obj:`float` or None: None will be returned if the database
            is empty or the parameter could not have been found, Else
            the numeric value is returned by this method.
      """

      from pywetterturnier import utils

      parameter = parameter.lower()
      if not parameter in self._columns_:
         #print("Parameter %s does not exist in database table %s. Stop in getobs.load_obs" % \
         #         (parameter, self._table_))
         return None

      tmp    = self._date_ + dt.timedelta( 0, hour*3600 )
      datum  = int( tmp.strftime('%Y%m%d') )
      stdmin = int( tmp.strftime('%H%M')   )
      #print( "    - For station %6d: %d %04d try to load %s" % (wmo,datum,stdmin,parameter) )
      
      # for some parameters we prefer the obs at minute 50 (SYNOP)
      if min50: stdmin -= 50

      # - Load from db
      sql = "SELECT %s FROM %s WHERE statnr=%d AND datum=%d AND stdmin=%d"
      cur = self.db.cursor()
      cur.execute( sql % (parameter, self._table_, wmo, datum, stdmin) )
      data = cur.fetchall()

      # - No row in database at all or None value
      if len(data) == 0 or data[0][0] == None:
         # if no obs at minute 50 try :00 obs (SYNOP)
         if min50:
            stdmin += 50
            cur.execute( sql % (parameter, self._table_, wmo, datum, stdmin) )
            data = cur.fetchall()
         else:
            return None
         
      elif len(data) > 1:
         for i in range(len(data)):
            try:
               return data[i][0]
            except:
               continue
         #utils.exit("got more than one row - thats not good. Stop.")
      
      # - Else return value
      try: return data[0][0]
      except: return None


   # ----------------------------------------------------------------
   # - Loading special observations 
   # ----------------------------------------------------------------
   def load_special_obs( self, wmo, special ):
      """Loading a specific observation from the database.
      The date for which the observation should be valid and the
      name of the database are coming from the public attributes of the
      class (see :class:`getobs.getobs`).

      Args:
         wmo (:obj:`int`): WMO station number.
         special (:class:`getobs.getobs.special_obs_class`): Selector for handling
                special requests (modifies the time-selector).
      
      Returns:
         float: Either a numeric value or None if the cell in the
         database was empty (NULL).
      """

      from pywetterturnier import utils

      parameter = special.parameter.lower()
      if not parameter in self._columns_:
         utils.exit("Parameter %s does not exist in database table %s. Stop in getobs.load_obs" % \
                  (parameter, self._table_))

      # If both (from and to) are from the same day
      if special.from_date.strftime("%Y-%m-%d") == special.to_date.strftime("%Y-%m-%d"):
         # - Load from db
         sql = "SELECT {0:s} FROM {1:s} WHERE msgtyp='bufr' AND statnr={2:d} AND datum={3:d} AND stdmin>={4:d} AND stdmin <= {5:d}".format(
               special.parameter, self._table_, wmo,
               int(special.from_date.strftime("%Y%m%d")),
               int(special.from_date.strftime("%H%M")), int(special.to_date.strftime("%H%M"))
               )
      else:
         # - Load from db
         sql = "SELECT {0:s} FROM {1:s} WHERE msgtyp='bufr' AND statnr={2:d} AND ((datum={3:d} AND stdmin>={4:d}) OR (datum={5:d} AND stdmin <= {6:d}))".format(
               special.parameter, self._table_, wmo,
               int(special.from_date.strftime("%Y%m%d")), int(special.from_date.strftime("%H%M")),
               int(special.to_date.strftime("%Y%m%d")), int(special.to_date.strftime("%H%M"))
               )

      cur = self.db.cursor()
      cur.execute( sql )
      data = cur.fetchall()

      # Keep non-None values
      res = []
      for i in data:
         if i[0] is None: continue
         res.append( int( i[0] ) )

      # Return 'None' if no result has been found or a list of integers else.
      if len(res) == 0:
         return None
      else:
         return res




   # ----------------------------------------------------------------
   # - Checks if a a certain observation at leas has a row in the
   #   database (wmo/time/date) row exits - do not check the
   #   content of the colums. 
   # ----------------------------------------------------------------
   def check_record( self, wmo, hour ):
      """Checks if database record exists. Just checks if for the   
      current date/time/station combination a row exists in the database
      and not what a specific cell contains. Note: date, and table name
      are coming from the public attributes of @ref getobs.getobs .

      Args:
         wmo (:obj:`int`): WMO station number.
         hour (:obj:`int`): Hour time shift relative to the 'date', 00:00 UTC.
              As an example: hour=30 means that we are checking 'tomorrow 06:00 UTC'.

      Returns:
         bool: False if no such row exists, else True.
      """

      datumsec   = self._date_ + dt.timedelta( 0, hour*3600 )
      datumsec   = int( datumsec.strftime('%s') )
      sql = "SELECT count(*) FROM %s WHERE msgtyp='bufr' AND statnr=%d AND datumsec = %d" % \
            (self._table_, wmo, datumsec )
      cur = self.db.cursor()
      cur.execute( sql )

      # - Else return value
      return (int( cur.fetchone()[0] ) > 0)


   # ----------------------------------------------------------------
   # - Adding value
   # ----------------------------------------------------------------
   def _add_obs_value_(self,parameter,wmo,value):
      """Adds a loaded observation to the final data object stored on the
      parent :class:`getobs.getobs` object. Appends all data to the
      public attribute :attr:`getobs.getobs.data`.

      Args:
         parameter (:obj:`str`): Parameter shortname.
         wmo (:obj:`int`): WMO station number.
         value (:obj:`float`): Either a numeric value or None.
      """

      if   wmo == 2878 and parameter in ["Sd1","Sd24"]:  wmo = 10471
      elif wmo == 11121 and parameter == "Sd1": wmo = 11120
      #TODO add dd12 from 11121 only if not already observed from 11120

      # - If value is none: return
      if value == None: return
      # - Initialize data object and add new dict with key wmo
      if not self.data:
         self.data = {wmo:{}}
      # - Adding new dict with key wmo
      elif not wmo in list(self.data.keys()):
         self.data[wmo] = {}
      # - Adding value
      self.data[wmo][parameter] = value


   # ----------------------------------------------------------------
   # - Prepare T2m 12z
   # ----------------------------------------------------------------
   def _prepare_fun_T12_(self,station,special):
      return self.load_obs( station.wmo, 12, "t", min50=1 )


   # ----------------------------------------------------------------
   # - Prepare ff12 (m/s)
   # ----------------------------------------------------------------
   def _prepare_fun_ff12_(self,station,special):
      ff12 = self.load_obs( station.wmo, 24, "ff12" )
      if ff12:
         return ff12
      else:
         return self.load_obs( station.wmo, 12, "ff", min50=1 )


   def none_filter(self, values):
      #replace all occurences of -1 by 0
      values[:] = [x if x != -1 else 0 for x in values]
      return list(filter(lambda x : x != None, values))


   def observed(self, values, func = np.max ):
      if len(values) > 0:
         return func(values)
      return 0

   # ----------------------------------------------------------------
   # - Prepare fx24 (m/s)
   # ----------------------------------------------------------------
   def _prepare_fun_fx24_(self,station,special):
     
      ffx24 = self.load_obs( station.wmo, 24, "fx24" )
      if ffx24:
         return ffx24

      ffx12 = self.none_filter([self.load_obs( station.wmo, i, "ffx12" ) for i in range(12,25,6)])
      if len(ffx12) == 2:
         return self.observed( ffx12 )

      ffx6 = self.none_filter([self.load_obs( station.wmo, i, "ffx6" ) for i in range(6,25,6)])
      if len(ffx6) == 4:
         return self.observed( ffx6 )

      ffx3 = self.none_filter([self.load_obs( station.wmo, i, "ffx3" ) for i in range(3,25,3)])
      if len(ffx3) == 8:
         return self.observed( ffx3 )

      ffx1 = self.none_filter([self.load_obs( station.wmo, i, "ffx1" ) for i in range(1,25)])
      if len(ffx1) == 24:
         return self.observed( ffx1 )
      
      ffx = self.none_filter([self.load_obs( station.wmo, i, "ffx" ) for i in range(1,25)])
      if len(ffx) == 24:
         return self.observed( ffx1 )

      ff1 = self.none_filter([self.load_obs( station.wmo, i, "ff" ) for i in range(1,25)])
      if len(ff1) == 24:
         return self.observed( ffx1 )

      return None

   # ----------------------------------------------------------------
   # - Prepare Sd 1h @12z
   # ----------------------------------------------------------------
   def _prepare_fun_Sd1_(self,station,special):
      try: return self.load_obs( station.wmo, 12, "sun", min50=0 ) * 10
      except: return None


   # ----------------------------------------------------------------
   # - Prepare RR1 (max 1h precipitation of day)
   # ----------------------------------------------------------------
   def _prepare_fun_RR1_(self,station,special):
      
      RR1 = self.none_filter([self.load_obs( station.wmo, i, "rrr1" ) for i in range(1,25)])
     
      from .utils import today_tdate
      today = today_tdate()
      if len(RR1) == 24 or today > self.tdate:
         return self.observed(RR1)
      else: return None


   # ----------------------------------------------------------------
   # - Prepare RR24 (sum precipitation of day)
   # ----------------------------------------------------------------
   def _prepare_fun_RR24_(self,station,special):
     
      RR24 = self.load_obs( station.wmo, 24, "rr24" )
      if RR24:
         return RR24

      RR12 = self.none_filter([self.load_obs( station.wmo, i, "rrr12" ) for i in range(12,25,6)])
      if len(RR12) == 2:
         return self.observed( RR12, np.sum )

      RR6 = self.none_filter([self.load_obs( station.wmo, i, "rrr6" ) for i in range(6,25,6)])
      if len(RR6) == 4:
         return self.observed( RR6, np.sum )

      RR3 = self.none_filter([self.load_obs( station.wmo, i, "rrr3" ) for i in range(3,25,3)])
      if len(RR3) == 8:
         return self.observed( RR3, np.sum )

      RR1 = self.none_filter([self.load_obs( station.wmo, i, "rrr1" ) for i in range(1,25)])
      from .utils import today_tdate
      today = today_tdate()
      if len(RR1) == 24 or today > self.tdate:
         return self.observed( RR1, np.sum )

      return None


   # ----------------------------------------------------------------
   # - Prepare TTm
   # ----------------------------------------------------------------
   def _prepare_fun_TTm_(self,station,special):
      """Helper function for TTM, maximum temperature. Returns 18 UTC maximum
      temperature, either from column tmax12 or - if tmax12 not available
      but tmax24 exists - maximum temperature from tmax24.
      Temperature will be in 1/10 degrees Celsius.

      Args:
         station (:obj:`stationclass.stationclass`): Station handler.
         special (:obj:`str`): See :meth:`getobs.getobs.prepare` for more details.
      
      Returns:
        float: Returns observed value if loading data was successful
        or None if observation not available or nor recorded.
      """

      # - Loading tmax24 and tmax12 (12h/24 period maximum)
      #   valid for 18 UTC in the evening for the current date 
      tmax12 = self.load_obs( station.wmo, 18, 'tmax12' )
      if not tmax12:
         tmax12 = self.load_obs( station.wmo, 18, 't2max12' )
      
      tmax24 = self.load_obs( station.wmo, 18, 'tmax24' )
      if not tmax24:
         tmax24 = self.load_obs( station.wmo, 18, 't2max24' )

      # - If tmax12 is valid: take this one
      if not tmax12 == None:
         value = tmax12
      # - Else if tmax24 is valid, take this one
      elif not tmax24 == None:
         value = tmax24
      # - Else value is None
      else: 
         value = None

      # Live procedure
      if special is not None and value is None:
         special = self.special_obs_object( special, self._date_ )

         # If parsing was ok
         if not special.error:
            # Loading special data from database
            spvalue = self.load_special_obs( station.wmo, special ) 
            # If spvalue is not None take maximum of these
            # observations as the 'best known maximum'.
            if spvalue is not None:
               value = np.max(spvalue)
         else:
            print("[!] Had problems parsing the special argument! Skip!")


      # - Return value
      return value

   _prepare_fun_Tmax_ = lambda self,station,special : self._prepare_fun_TTm_(station,special)

   # ----------------------------------------------------------------
   # - Prepare TTn
   # ----------------------------------------------------------------
   def _prepare_fun_TTn_(self,station,special):
      """Helper function for TTN, minimum temperature. Returns 06 UTC minimum
      temperature. Simply the tmin12 column at 06 UTC in 1/10 degrees Celsius.

      Args:
         station (:obj:`stationclass.stationclass`): Station handler.
         special (:obj:`str`): See :meth:`getobs.getobs.prepare` for more details.
      
      Returns:
         float: Returns observed value if loading data was successful
         or None if observation not available or nor recorded.
      """

      # - Loading tmax24 and tmax12 (12h/24 period maximum)
      #   valid for 18 UTC in the evening for the current date 
      value = self.load_obs( station.wmo,  6, 'tmin12' )
      if not value:
         value = self.load_obs( station.wmo, 6 , 't2min12' )

      if special is not None and value is None:
         special = self.special_obs_object( special, self._date_ )

         # If parsing was ok
         if not special.error:
            # Loading special data from database
            spvalue = self.load_special_obs( station.wmo, special ) 
            # If spvalue is not None take minimum of these
            # observations as the 'best known minimum'.
            if spvalue is not None:
               value = np.min(spvalue)
         else:
            print("[!] Had problems parsing the special argument! Skip!")
            
      # - Return value
      return value 

   _prepare_fun_Tmin_ = lambda self,station,special : self._prepare_fun_TTn_(station,special)

   # ----------------------------------------------------------------
   # - Prepare TTd
   # ----------------------------------------------------------------
   def _prepare_fun_TTd_(self,station,special,min50=False):
      """Helper function for dew point temperature. Returns 12 UTC observed
      dew point temperature from database column td in 1/10 degrees Celsius.

      Args:
         station (:obj:`stationclass.stationclass`): Station handler.
         special (:obj:`str`): See :meth:`getobs.getobs.prepare` for more details.
      
      Returns:
         float: Returns observed value if loading data was successful
         or None if observation not available or nor recorded.
      """

      # - Loading td valid at 12 UTC 
      value = self.load_obs( station.wmo, 12, 'td', min50=min50 )
      # - Return value
      return value

   _prepare_fun_Td12_ = lambda self,station,special : self._prepare_fun_TTd_(station,special,min50=1)

   # ----------------------------------------------------------------
   # - Prepare PPP
   # ----------------------------------------------------------------
   def _prepare_fun_PPP_(self,station,special,min50=False):
      """Helper function for mean sea level pressure at 12 UTC.
      Based on database column pmsl. Return value will be in 1/10 hPa.

      Args:
         station (:obj:`stationclass.stationclass`): Station handler.
         special (:obj:`str`): See :meth:`getobs.getobs.prepare` for more details.
      
      Returns:
         float: Returns observed value if loading data was successful
         or None if observation not available or nor recorded.
      """
      import numpy as np
      # - Loading td valid at 12 UTC 
      value = self.load_obs( station.wmo, 12, 'pmsl', min50=min50 )
      # - Original value is in 1/100 hPa. Convert.
      if value == None:
         cur = self.db.cursor()
         sql = "SELECT hoehe, hbaro FROM obs.stations WHERE statnr = %d"
         cur.execute( sql % station.wmo )
         data = cur.fetchall()
         if not data: h = 0
         elif len(data[0]) > 0:
            h = data[0][0]
         else:
            h = data[0][1]
         p = self.load_obs( station.wmo, 12, 'psta', min50=min50 )
         T = self.load_obs( station.wmo, 12, 't', min50=min50 )

         #calculate reduced MSL pressure via international barometric height formula if no reduced pressure is given
         if not (p == None or T == None or h == None):
            T /= 10.; p /= 10.
            T += 273.15
            value = p * ( T / (T + 0.0065*h) )**(-5.255)
            return value

      if not value == None:
         value = np.round( value/10. )

      # Return value 
      return value

   _prepare_fun_PPP12_ = lambda self,station,special : self._prepare_fun_PPP_(station,special,min50=1)

   # ----------------------------------------------------------------
   # - Prepare dd
   # ----------------------------------------------------------------
   def _prepare_fun_dd_(self,station,special,min50=False):
      """Helper function for the wind direction at 12 UTC from database
      column dd. Values will be returned in 1/10 degrees but rounded
      to full 10 degrees. E.g., observed '138' degrees will be converted
      into '1400' (1/10 degrees, rounded to full 10 degrees). 
      Special case: also depends on database column ff. The following
      cases will be used:

      1) if dd not observed/received: **return None**

      2) if dd==0 and ff==0:          **return 0.0**

      3) if dd==0 and ff>0:           **return None (variable wind direction)**

      4) else:                        **return value**

      Args:
         station (:obj:`stationclass.stationclass`): Station handler.
         special (:obj:`str`): See :meth:`getobs.getobs.prepare` for more details.

      Returns:
         float: Returns observed value if loading data was successful
         or None if observation not available or nor recorded.
      """
      #helper function to implement round half up (bankers rounding)
      #https://stackoverflow.com/questions/33019698/how-to-properly-round-up-half-float-numbers
      HalfRoundUp = lambda value: int(value + 0.5)
      
      # - Loading td valid at 12 UTC 
      dd = self.load_obs( station.wmo, 12, 'dd', min50=min50 )
      ff = self.load_obs( station.wmo, 12, 'ff', min50=min50 )
      # - If dd is valid: take this one
      if dd == None:
         value = None
      # - if wind direction is 0 (variable)
      elif dd == 0:
         # - No wind (ff <= 0.2 m/s)
         if ff <= 2:
            value = 0
         #else wind direction is not defined
         else:
            value = None
      # - Else take dd as it is
      else:
         value = HalfRoundUp( float(dd) / 10 ) * 100.
         # - North wind will be 360, not 0 (no wind!). Change if 0 occurs
         if value == 0.:
            value = 3600.
      # - Return value
      return value

   _prepare_fun_dd12_ = lambda self,station,special : self._prepare_fun_dd_(station,special,min50=True)


   # ----------------------------------------------------------------
   # - Prepare ff
   # ----------------------------------------------------------------
   def _prepare_fun_ff_(self,station,special):
      """Helper function for the wind speed at 12 UTC. Based on database
      column ff. Values will be in 1/10 knots but rounded to full knots.
      E.g., if 3.2m/s observed -> 6.22kt -> Return value will be 60. 

      Args:
         station (:obj:`stationclass.stationclass`): Station handler.
         special (:obj:`str`): See :meth:`getobs.getobs.prepare` for more details.

      Returns:
         float: Returns observed value if loading data was successful
         or None if observation not available or nor recorded.
      """

      # - first we check if a converted obs for dd is available (maybe it has been set zero by admin)
      from pywetterturnier import database, utils
      import numpy as np

      inputs = utils.inputcheck('GetObs')
      # - Read configuration file
      config = utils.readconfig('config.conf', inputs)

      # - Initializing class and open database connection
      db     = database.database(config)

      bdate = utils.datetime2tdate( self._date_ )
      #calculate tdate from date of observation (Saturday = bdate -1; Sunday = bdate - 2)
      tdate = bdate - np.round( 7 * ( ( bdate/7 - np.floor( bdate/7 ) ) - 1/7 ) )

      dd = db.get_obs_data( station.cityID, db.get_parameter_id("dd"), tdate, bdate, wmo=station.wmo )

      #no converted obs yet? get obs from obstable
      if dd is False:
         dd = self.load_obs( station.wmo, 12, 'dd' )
      if type(dd) == None:
         # - Fallback that we probably never need:
         #   If no dd observation take max gust direction
         dd = self.load_obs( station.wmo, 12, 'ddx' )

      #if no wind direction is determined there can be no wind
      if dd is 0:
         value = 0
      else:
         # - Loading ff valid at 12 UTC 
         value = self.load_obs( station.wmo, 12, 'ff' )
         if value:
            value = np.round( np.float( value ) * (900/463) / 10 ) * 10

      # - Return value  
      return value


   # ----------------------------------------------------------------
   # - Loading fx (maximum wind gust over last 1h, 6 to 6 UTC)
   # ----------------------------------------------------------------
   def _prepare_fun_fx_(self,station,special):
      """Helper function for the maximum gust speed (fx > 25kt).
      Based on database column fx1. Return value will be in 1/10 knots but
      rounded to full knots. 
      E.g., if 21.2m/s observed -> 41.21kt -> Return value will be 410. 
      Special cases:

      1) no observation available but +30h
         observation (row) is in database:
         Assume that there were no gusts at all:   **return 0**

      2) no observations available and +30h
         observation (row) not yet in database:    **return None**

      3) observation available, below 25 knots:    **return 0**

      4) observation available, >= 25 knots:       **return value**

      Args:
         station (:obj:`stationclass.stationclass`): Station handler.
         special (:obj:`str`): See :meth:`getobs.getobs.prepare` for more details.

      Returns:
         float: Returns observed value if loading data was successful
         or None if observation not available or nor recorded.
      """

      # - Timestamps
      ts1   = self._date_ + dt.timedelta(0, 6*3600); ts1   = int(ts1.strftime("%s"))
      tsend = self._date_ + dt.timedelta(0,30*3600); tsend = int(tsend.strftime("%s"))

      # - For FFX6 (maximum over the last 6 hours) I'll be sure not to pick a date/time
      #   overlapping the period we'll take the data from. Same holds for FFX3 which is
      #   max gust over the last 3 hours. Therefore
      #   - ts3: first time step to pick FFX3 from
      #   - ts6: first time step to pick FFX6 from
      ts3   = self._date_ + dt.timedelta(0, 9*3600); ts3 = int(ts3.strftime("%s"))
      ts6   = self._date_ + dt.timedelta(0,12*3600); ts6 = int(ts6.strftime("%s"))

      # - Pick 10min ffx data 
      #   From >   +6 hours to <= +30 hours: or in other words, all
      #   6h-ffx observations from "07UTC to 06UTC next day"
      sql  = "SELECT ffx  FROM %s WHERE statnr = %d AND msgtyp = 'bufr' " % (self._table_,station.wmo) + \
             "AND datumsec >  %s AND datumsec <= %d AND NOT ffx  IS NULL" % (ts1,tsend)
      # - Statements to pick 1h gusts
      #   From >   +6 hours to <= +30 hours: or in other words, all
      #   6h-ffx observations from "07UTC to 06UTC next day"
      sql1 = "SELECT ffx1 FROM %s WHERE statnr = %d AND msgtyp = 'bufr' " % (self._table_,station.wmo) + \
             "AND datumsec >  %s AND datumsec <= %d AND NOT ffx1 IS NULL" % (ts1,tsend)
      # - Statements to pick 3h gusts
      #   From >=  +9 hours to <= +30 hours: or in other words, all
      #   6h-ffx observations from "09UTC to 06UTC next day"
      sql3 = "SELECT ffx3 FROM %s WHERE statnr = %d AND msgtyp = 'bufr' " % (self._table_,station.wmo) + \
             "AND datumsec >= %s AND datumsec <= %d AND NOT ffx3 IS NULL" % (ts3,tsend)
      # - Statements to pick 6h gusts
      #   From >= +12 hours to <= +30 hours: or in other words, all
      #   6h-ffx observations from "12UTC to 06UTC next day"
      sql6 = "SELECT ffx6 FROM %s WHERE statnr = %d AND msgtyp = 'bufr' " % (self._table_,station.wmo) + \
             "AND datumsec >= %s AND datumsec <= %d AND NOT ffx6 IS NULL" % (ts6,tsend)


      # - Initialize database cursor
      cur = self.db.cursor()

      # - New object to store the values (from all sql queries)
      data = []

      def append_data(data, tmp):
         for i in tmp:
            data.append( i[0] )
         return data

      for sql in [sql, sql1, sql3, sql6]:
         # - FFX [10 min, 1 h, 3 h, 6 h]
         cur.execute( sql  )
         tmp = cur.fetchall()
         data = append_data( data, tmp )

      # - Check if +30 h observation is available.
      check30 = self.check_record( station.wmo, 30 )

      # - No wind gusts received, but last observation is here
      if len(data) == 0 and check30:
         value = 0
      # - No observations at all
      elif len(data) == 0:
         value = None
      # - If last observation is not yet here (check30): None
      #   This avoids to store live fx (developing over time)
      #   observations into the database.
      elif not check30:
         value = None
      # - Else sum up
      else:
         value = 0
         import numpy as np
         for i in data:
            value = np.maximum(value, i)
         # - Convert from meters per second to knots.
         #   Moreover, if knots are below 25 (or 12.5 m/s) set value to zero.
         if value >= 125:
            value = np.round( np.float( value ) * (900/463) / 10. ) * 10
            if value < 250.:
               value = 250
         else:
            value = 0

      # - Return value  
      return value


   # ----------------------------------------------------------------
   # - Prepare N
   # ----------------------------------------------------------------
   def _prepare_fun_N_(self,station,special):
      """Helper function for cloud cover at 12 UTC. Return value
      will be in 1/10 octas, rounded to full octas [0,10,20,30,...,80]. 
      Observations based on database column cc.

      1) if observation is available:       **return value**

      2) if observation not recorded but
         12 UTC database entry exists we
         assume that there were no clouds:  **return 0**

      3) else:                              **return None**

      Args:
         station (:obj:`stationclass.stationclass`): Station handler.
         special (:obj:`str`): See :meth:`getobs.getobs.prepare` for more details.
      
      Returns:
         float: Returns observed value if loading data was successful
         or None if observation not available or nor recorded.
      """

      # - Loading td valid at 12 UTC 
      N = self.load_obs( station.wmo, 12, 'cc' )
      # - If tmax12 is valid: take this one
      if not N == None:
         import numpy as np
         # - Note: BUFR report is in percent
         value = (np.floor(np.float(N)/100.*8.)) * 10
         if value > 80: value = 80
      # - Else if record exists but there is no observed
      #   cloud cover we have to assume that the value
      #   should be 0 but is not reported at all. 
      elif self.check_record( station.wmo, 12 ): 
         value = 0
      else:
         value = None
      # - Return value  
      return value


   # ----------------------------------------------------------------
   # - Prepare Wv
   # ----------------------------------------------------------------
   def _prepare_fun_Wv_(self,station,special):
      """Helper function for significant weather for noon between
      0600 UTC and 1200 UTC.  w1 (past weather) at 1200 UTC is used (main
      obs time, w1 contains weathr over last 6 hours), the past weather (ww)
      observations for 0600 UTC to 1200 UTC are used to identify "current
      weather" while ww between 0700 UTC to 1200 UTC is used to check the "past
      weather" (ww=20 to ww=29).  Uses :meth:`_get_proper_WvWn_` method,
      the detailed rules can be found in the method description from
      the helper class (:meth:`_get_proper_WvWn_`).

      Args:
         station (:obj:`stationclass.stationclass`): Station handler.
         special (:obj:`str`): See :meth:`getobs.getobs.prepare` for more details.
      
      Returns:
         float: Returns None if no valid Wv/Wn could have been computed, else
         a float between 00. and 90. (for Wv/Wn = [0,1,2,3,...,9] as [0.,10.,...,90.])
         will be returned.
      """

      # Note: difference between special_now and special_after is that special_after does
      # NOT include 1200 UTC (used for Nachwetter), special_now does.
      special_now   = self.special_obs_object("ww today 06:00 to today 12:00",self._date_)
      special_after = self.special_obs_object("ww today 07:00 to today 12:00",self._date_)

      w1         = self.load_obs( station.wmo, 12, 'w1' )
      ww_now     = self.load_special_obs( station.wmo, special_now   )
      ww_after   = self.load_special_obs( station.wmo, special_after )

      Wv = self._get_proper_WvWn_( w1, ww_now, ww_after )

      # If Wv is None but the 12 UTC record is here we assume a 0 (no
      # significant weather). Until the 12 UTC record is not here we
      # return a None (no observations available):
      check = self.check_record( station.wmo, 12 )
      if Wv is None and not check:
         return None
      # If 12 UTC observation is not yet here, return None.
      # This avoids that we store live observations (developing over time)
      # into the database.
      elif not check:
          return None
      else:
          return  0 if (Wv is None) else Wv

   # ----------------------------------------------------------------
   # - Prepare Wn
   # ----------------------------------------------------------------
   def _prepare_fun_Wn_(self,station,special):
      """Helper function for significant weather for afternoon between
      1200 UTC and 1800 UTC.  w1 (past weather) at 1800 UTC is used (main
      obs time, w1 contains weathr over last 6 hours), the past weather (ww)
      observations for 1200 UTC to 1800 UTC are used to identify "current
      weather" while ww between 1300 UTC to 1800 UTC is used to check the "past
      weather" (ww=20 to ww=29).  Uses :meth:`_get_proper_WvWn_` method,
      the detailed rules can be found in the method description from
      the helper class (:meth:`_get_proper_WvWn_`).

      Args:
         station (:obj:`stationclass.stationclass`): Station handler.
         special (:obj:`str`): See :meth:`getobs.getobs.prepare` for more details.
      
      Returns:
         float: Returns None if no valid Wv/Wn could have been computed, else
         a float between 00. and 90. (for Wv/Wn = [0,1,2,3,...,9] as [0.,10.,...,90.])
         will be returned.
      """

      # Note: difference between special_now and special_after is that special_after does
      # NOT include 1200 UTC (used for Nachwetter), special_now does.
      special_now   = self.special_obs_object("ww today 12:00 to today 18:00", self._date_)
      special_after = self.special_obs_object("ww today 13:00 to today 18:00", self._date_)

      w1         = self.load_obs( station.wmo, 18, 'w1' )
      ww_now     = self.load_special_obs( station.wmo, special_now   )
      ww_after   = self.load_special_obs( station.wmo, special_after )

      Wn = self._get_proper_WvWn_( w1, ww_now, ww_after )

      # If Wn is None but the 18 UTC record is here we assume a 0 (no
      # significant weather). Until the 18 UTC record is not here we
      # return a None (no observations available):
      check = self.check_record( station.wmo, 18 )
      if Wn is None and not check:
         return None
      # If 12 UTC observation is not yet here, return None.
      # This avoids that we store live observations (developing over time)
      # into the database.
      elif not check:
          return None
      else:
          return  0 if (Wn is None) else Wn

   # ----------------------------------------------------------------
   # - Prepare Wv
   # ----------------------------------------------------------------
   def _prepare_fun_Wall_(self,station,special):
      """Helper function for significant weather for 24h period between
      0600 to 0600 UTC. This function is used internally when computing the
      observed precipitation sum. If precipitation would return a -3.0 (-0.1mm/24h)
      but there were observed precipitation classes, set precipitation sum to 0.

      Args:
         station (:obj:`stationclass.stationclass`): Station handler.
         special (:obj:`str`): See :meth:`getobs.getobs.prepare` for more details.
      
      Returns:
         float: Returns None if no valid Wv/Wn could have been computed, else
         a float between 00. and 90. (for Wv/Wn = [0,1,2,3,...,9] as [0.,10.,...,90.])
         will be returned.
      """

      # Note: difference between special_now and special_after is that special_after does
      # NOT include 0600 UTC (used for Nachwetter), special_now does.
      special_after = self.special_obs_object("ww today 07:00 to tomorrow 06:00",self._date_)
      special_now   = self.special_obs_object("ww today 06:00 to tomorrow 06:00",self._date_)

      ww_after   = self.load_special_obs( station.wmo, special_after )
      ww_now     = self.load_special_obs( station.wmo, special_now   )

      Wall = self._get_proper_WvWn_( None, ww_now, ww_after, returnlist = True )

      # If Wv is None but the 06 UTC record is here we assume a 0 (no
      # significant weather). Until the 06 UTC record is not here we
      # return a None (no observations available):
      check = self.check_record( station.wmo, 6 )
      if Wall is None and not check:
         return None
      # If 12 UTC observation is not yet here, return None.
      # This avoids that we store live observations (developing over time)
      # into the database.
      elif not check:
          return None
      else:
          return  0 if (Wall is None) else Wall


   # ----------------------------------------------------------------
   # ----------------------------------------------------------------
   def _get_proper_WvWn_( self, w1, ww_now, ww_after, returnlist = False ):
      """Helper class to properly prepare Wv and Wn.
      Returns highest observed value "w1" where observed w1=1,2,3 will
      be set to w1=0. In additioin, ww is considered in two ways:
      input inww contains the values which are used to check the 'past weather'
      (do not include the leading hour, e.g., do not include 0600 UTC for the
      time period 0600 UTC to 1200 UTC) while inxX contains the same data (ww) but
      including the leading hour and is used to extract 'current weather' from
      the ww observations. 

      Please see documentation of :meth:`utils.wmowwConversion` and check the
      config file (:file:`wmo_ww.conf`) to see what will be converted into what.

      Args:
        inw1 (:obj:`int`): Observed w1 value (may contain
            None or 'missing observation' numbers (e.g, w1=10)
        ww_now (:obj:`list`): List of all observed ww values (may contain
            None values and 'missing observation'  numbers (e.g., ww=508).
            Similar to ww_after but contains less data (not including leading hour).
            From this list values 20-29 will be neglected!
        ww_after (:obj:`list`): List of all observed ww values (may contain
            None values and 'missing observation'  numbers (e.g., ww=508).
            From this list only values 20-19 will be consisered!
        returnlist (:obj:`bool`): If set to true not only one single value will
            be returned but a list of all observed w1/ww/wX whch are considiered
            in this method. Is used for the raincheck where we don't want to have
            the highest number only but all (as if highest is 9 (thunderstorm) it
            might have been a dry thunderstorm, but there might be additional
            reports on rain before/after).

      Returns:
        float: Returns a single value between 0 and 90 (w1=0 to we=90, multiplied
        by 10 as it will be stored in the databases) or None if no valid w1
        is available.
      """

      ww_now   = [] if ww_now   is None else ww_now 
      ww_after = [] if ww_after is None else ww_after 

      # For ww_now consider all except 20-29
      tmp = np.copy(ww_now); ww_now = []
      for x in tmp:
          if not x in range(20,30) and not x is None: ww_now.append(x)
      tmp = np.copy(ww_after); ww_after = []
      # For ww_after (Nachwetter; including leading hour) take only 20-29!
      for x in tmp:
          if     x in range(20,30): ww_after.append(x)


      #print("      [Input]  w1:       ", w1      )
      #print("               ww_now:   ", ww_now  )
      #print("               ww_after: ", ww_after)

      # If wmoww input argument to this class has been set: convert all
      # observed w1/ww flags into the new ones.
      if self.wmoww:
          w1       =   self.wmoww.convert( "w1", w1 )
          ww_now   = list(filter(None, [ self.wmoww.convert( "ww", x ) for x in ww_now   ] ))
          ww_after = list(filter(None, [ self.wmoww.convert( "ww", x ) for x in ww_after ] ))
          #print("      [Converted]   ",w1, ww_now, ww_after)

      # If list return is requested: do so.
      if returnlist:
          w1 = [] if w1 is None else [w1]
          return w1 + ww_now + ww_after

      w1 = 0 if not w1 else w1

      print("    Observed w1 is ", w1, end=' ')

      # If max(wX) > w1: use max(wX) value
      for ww in [ww_now, ww_after]:
         if ww:
            max_ww = np.max( ww )
            if max_ww > w1:
               w1 = int(max_ww)
         print(" considering [ww] as well yields ", w1)

      # - Return value  
      return None if w1 is None else float(w1)*10.


   # ----------------------------------------------------------------
   # - Loading RR
   # ----------------------------------------------------------------
   def _prepare_fun_RR_(self,station,special):
      """Helper function for 24h sum of precipitation based on
      database column 'rrr12' at +18 and +30h (as the reported
      observations are 12h sums this means from 06 UTC today
      to 06 UTC tomorrow). Returns precipitation in 1/10 mm
      OR -30 if there was no precipitation at all.
      Note: if there is no recorded precipitation amount or
      the amount of precipitation recorded is 0.0 I also check
      the W1 observations for the time period of interest. If
      there is no sign. precipitation weather recorded in W1
      (w1 = 5, 6, 7, 8 or 9) the value will be set to -3.0.
      In addition w1/ww are checked to set precip sum to 0 if
      -0.1 sum's were received but rain weather types have been
      reported in the same time. Therefore the method
      :meth:`getobs._prepare_fun_Wall_` is used for the time
      period 0600 to 0600 UTC of the following day.

      First: if database entry for 18 UTC is here but
      there is no recorded amount of precipitation we
      have to assume that there was no precipitation.
      The same for +30h (06 UTC next day).

      Second:
      If observed precipitation amount is negative (some
      stations send -0.1mm/12h for no precipitation) we

      Third:
      If w1/ww reports precipitation types [5,6,7,8] but rain
      sum is -0.1 (-3.0): return 0.0 for precip!

      Args:
         station (:obj:`stationclass.stationclass`): Station handler.
         special (:obj:`str`): See :meth:`getobs.getobs.prepare` for more details.
      
      Returns:
        float: Returns observed value if loading data was successful
        or None if observation not available or nor recorded.
      """

      # ----------------------------------------------------------
      # RR - Precipitation (2 * 12h)
      #      06 today to 06 tomorrow!!
      # ----------------------------------------------------------
      # Loading 12h sums
      RR18    = self.load_obs( station.wmo, 18, 'rrr12' )
      RR06    = self.load_obs( station.wmo, 30, 'rrr12' )
      # Loading 24h sums
      RR06_24 = self.load_obs( station.wmo, 30, 'rrr24' )

      # - Check if observations (records) are hete
      check18 = self.check_record( station.wmo, 18 )
      check06 = self.check_record( station.wmo, 30 )

      #print(" ------------- ")
      #print("RR18     ", RR18   )
      #print("RR06     ", RR06   )
      #print("RR06_24  ", RR06_24)
      #print("check18  ", check18)
      #print("check06  ", check06)

      # - If observed values RR18/RR06 are empty but the observations
      #   are in the database we have to assume that there was no
      #   precipitation at all. Set these values to -3.0 (no precip).
      #   Same for RR06_24
      if RR18    == None and check18: RR18 = -30.
      if RR06    == None and check06: RR06 = -30.

      # - Both observations available: use them
      if not RR06_24 == None:
         value = RR06_24
      elif not RR18 == None and not RR06 == None:
         # - Both negative (no precipitation) will
         #   result in Wetterturnier special: -3.0mm.
         if RR18 < 0 and RR06 < 0:
            value = -30.
         # - Else at least one of the obs was 0.0  
         #   which is non-obervable precipitation,
         #   but precipitation!
         else:
            if RR18 < 0.: RR18 = 0.
            if RR06 < 0.: RR06 = 0.
            value = RR18 + RR06
      else:
         value = None

      # - Extra check: if precipitation sum is 0:
      if value == 0:
         # - Load W1 observation for the time period 06UTC-06UTC
         W1 = []
         W1.append( self.load_obs( station.wmo, 12, 'w1' ) )
         W1.append( self.load_obs( station.wmo, 18, 'w1' ) )
         W1.append( self.load_obs( station.wmo, 24, 'w1' ) )
         W1.append( self.load_obs( station.wmo, 30, 'w1' ) )

         # Check if all W1-observations are 10 (no sign. weather reported),
         # class 0/1/2/3/4 (the non-precip-weather-types) or missing.
         # If so, then the sum will be set to -3.0 (dry) rather than 0.0.
         if all( item in [None,0,1,2,3,4,10] for item in W1):
            value = -30.

      # - Loaidng Wall to check whether rain has been observed
      #   in past or present weather. If there are any precipitation class
      #   observations and the precipitation sum is -0.1 (which could yield a
      #   -3.0) set precip to 0.0!
      raincheck = self._prepare_fun_Wall_(station,None)
      if not raincheck is None:
         raincheck = [x in [5,6,7,8] for x in raincheck]
         raincheck = np.any( raincheck )
         if not value is None:
            if value < 0 and raincheck: value = 0.
      
      # - Return value  
      return value


   # ----------------------------------------------------------------
   # - Loading sunshine. 
   # ----------------------------------------------------------------
   def _prepare_fun_Sd_(self,station,special):
      """Helper function for relative sun shine duration for the
      full day. Will be returned in 1/10 percent rounded to
      full percent (34% will result in 340.).

      1) if 24h sum is available on 'sunday' on 06 UTC we will 
         take this value.

      2) if 06UTC sunday is not available but we have a sunday
         value at 00 UTC: take this one.

      3) else sum up the 'sun' 1h-rly obs. WARNING: seems that
         'none' is either 'no sun' or 'not reported'. I can't
         decide which one is which one at the moment. I just
         take none = 0 and sum up.

      Args:
         station (:obj:`stationclass.stationclass`): Station handler.
         special (:obj:`str`): See :meth:`getobs.getobs.prepare` for more details.
      
      Returns:
        float: Returns observed value if loading data was successful
        or None if observation not available or nor recorded.
      """

      from pywetterturnier import utils
      # - If we have not loaded maxSd: stop
      if not station.wmo in self._maxSd_:
         utils.exit("maximum sunshine duration for station %d unknown.\n" % station.wmo + \
                    "Most possible reason: there is no entry for this station\n" + \
                    "in the table obs.stations and therefore I can't compute\n" + \
                    "the astronomic sunshine duration which is needed!")

      # - If we dont have any information about the maximum Sd we cant
      #   compute the relative value. In this case return False
      if not self._maxSd_[station.wmo]:
         value = None
      # - Else start processing the data
      else:
         # - Loading sunshine 24h sum, next day reported at 06UTC
         #   which is +30 hours from self._date_.
         #   Note: sunday is not Sunday, it is the parameter called
         #   "sunday" (sunshine, full day).
         tmp = self.load_obs( station.wmo, 30, 'sunday' )
         if tmp:
            value = int( np.round(np.float(tmp)/np.float(self._maxSd_[station.wmo]) * 100) ) * 10
         # - If no full day sunshine duration is reported +30h: check full day
         #   sunshie duration +24h (00 UTC report) which is +24 hours from self._date_
         else:
            #   Note: sunday is not Sunday, it is the parameter called
            #   "sunday" (sunshine, full day).
            tmp = self.load_obs( station.wmo, 24, 'sunday' )
            if tmp:
               value  = int( np.round(np.float(tmp)/np.float(self._maxSd_[station.wmo]) * 100) ) * 10
                
            # - Else try to sum up hourly observations
            else:
	         # Check if +24h record is here. If the record is here but we have
               # not gotten any information so far (self.load_obs(..) returned None for
               # both, +30 and +24): loading 1h observations and take the sum!
               check24 = self.check_record( station.wmo, 24 )
               # - Else try to get the hourly sums.
               if check24:
                  datum = int( self._date_.strftime('%Y%m%d') )
                  sql = "SELECT sun FROM %s WHERE statnr = %d AND " % (self._table_,station.wmo) + \
                        "msgtyp = 'bufr' AND datum = %d AND NOT sun IS NULL" % datum

                  cur = self.db.cursor()
                  cur.execute( sql )
                  data = cur.fetchall()
                  # - No data? Return None 
                  if len(data) == 0 or data == None:
                     return None
                  else:
                     # - Else sum up
                     value = sum([int( i[0] ) for i in data])
                     value = int( np.round(np.float(value) / np.float(self._maxSd_[station.wmo]) * 100) ) * 10
	            
               # Else we report None 
               else: value = None

      # - Return value
      return value
      
   _prepare_fun_Sd24_ = lambda self,station,special : self._prepare_fun_Sd_(station,special)


   # ----------------------------------------------------------------
   # - Calling the prepare_fun methods for the different
   #   parameters like TTm, TTn, ... 
   # ----------------------------------------------------------------
   def prepare( self, parameter,special=None):
      """Prepares the different observed parameters like ``TTn``, ``TTm``, ``N``,
      and so on (depending on what's defined in the database table
      ``params``). Note that the script will ignore a wrong specified
      or unknown parameter as the internal method then does not exist. 
      The date will be taken from the public arguments of the parent
      class :class`getobs.getobs`.
      The additional data (specified via ``special`` input argument will only
      be used when the final value is not yet available.

      Args:
         parameter (:obj:`str`): shortname of the Wetterturnier parameters.
         special   (:obj:`str`): String with a very specific format. This is to
            compute some live observations such as min/max.

      Examples:
         Prepare weather type parameter ``Wv``, in addition select database
         column ``w1`` and select all available observations between 07:00 today
         and 18:00 of the requested date (today), see input argument
         ``date`` on :obj:`getobs.getobs`.

         ``x.prepare( "Wv", "w1 today 07:00 to today 12:00" )``

         Compute minimum temperature ``TTn``, in addition select
         database column ``T`` between yesterday 18:00 and today 06:00.

         ``x.prepare( "TTn", "T yesterday 18:00 to today 6:00" )``

      .. todo:: Reference to database table param.
      """

      try:
         #print("eval", parameter)
         fun = eval("self._prepare_fun_%s_" % parameter)
      except Exception as e:
         print("[!] WARNING: method prepare_fun_%s does not exist. Cannot prepare data." % parameter)
         print(e)
         return

      import inspect
      if not inspect.ismethod( fun ):
         print("[!] WARNING: method prepare_fun_%s is no instancemethod. Cannot prepare data." % parameter)
         return

      # - Else calling function
      for station in self.stations:
         value = fun(station,special)
         self._add_obs_value_(parameter,station.wmo,value)

   # ----------------------------------------------------------------
   # - Show loaded data
   # ----------------------------------------------------------------
   def show( self ):
      """Shows a summary of the current @ref getobs.getobs class.
      Was mainly used for development purposes. Shows data and stuff
      stored on class attributes.
      """

      if not self.data:
         print("    Can't show data summary: no observation data loaded")
         return

      # - Else show data
      allcols = []
      for i in self.data:
         for k in list(self.data[i].keys()):
            if not k in allcols: allcols.append(k)
      #allcols.sort()

      # - Show data
      print("     ", end=' ')
      for stn in self.stations:
         print(" %13d   " % stn.wmo, end=' ')
      print("")

      # - Looping over params
      pnr = 0
      for param in allcols:
         pnr = pnr + 1 
         print("   %2d  " % pnr, end=' ')
         for stn in self.stations:
            if not stn.wmo in list(self.data.keys()):
               continue
            elif not param in list(self.data[stn.wmo].keys()):
               print(" %-5s %8s   " % (param,"- - -"), end=' ')
            else:
               print(" %-5s %8d   " % (param,self.data[stn.wmo][param]), end=' ')

         print("")
         

   # ----------------------------------------------------------------
   # - Save to database
   # ----------------------------------------------------------------
   def write_to_db( self ):
      """Write prepared observations to database. Writes all prepared
      observations which are stored in the parent :class:`getobs.getobs`
      to the Wetterturnier database.
      """

      if self.data == None:   
         print("Cant write data to database. Because there are no data. Return.")
         return

      # - Create tuple for update
      data = []

      param = {}
      for i in self.db.get_parameter_names():
         param[i] = self.db.get_parameter_id( i )

      # - Prepare a few sql statements we need later 
      sql_check  = "SELECT placedby FROM %swetterturnier_obs " % self.db.prefix + \
                   "WHERE station = %d AND betdate = %d AND paramID = %d"

      sql_insert = "INSERT INTO %swetterturnier_obs " % self.db.prefix + \
                   "(station,paramID,betdate,placed,placedby,value) " + \
                   "VALUES (%d,%d,%d,'%s',0,%d)"

      sql_update = "UPDATE %swetterturnier_obs " % self.db.prefix + \
                   "SET placed = '%s', value = %d " + \
                   "WHERE station = %d AND paramID = %d AND betdate = %d"

      # - Dates and update date
      now = dt.datetime.now()
      now = now.strftime("%Y-%m-%d %H:%M")
      betdate = np.int( np.floor( np.float(self._date_.strftime('%s')) / 86400. ) )

      # - Looping over wmo stations
      cur = self.db.cursor()
      for stn in self.stations:

         if not stn.wmo in list(self.data.keys()):
            print("[!] Can't find wmo %d in results. Skip." % stn.wmo)
            continue

         for key in list(self.data[stn.wmo].keys()):

            # - If parameter is not one of the wetterturnier parameters: skip
            if not key in param:
               print("[!] Cant find parameter %s in database! Skip!" % key)
               continue

            # - See if parameter is in NULLCONFIG of the station.
            #   If it is - ignore!
            if not param[key] in stn.getActiveParams( betdate ):
               print("    Parameter %s (%d) is/was not an active parameter for station %d. Skip." % \
                     (key, param[key], stn.wmo))
               continue

            # - Else append tuple
            tmp = (stn.wmo, param[key], betdate, now, self.data[stn.wmo][key])
            data.append(tmp)

            # - Checking SQL
            cur.execute( sql_check % (stn.wmo,betdate,param[key]) )
            res = cur.fetchall()

            # - If length res is empty: INSERT
            if len(res) == 0:
               #print("    Insert ....")
               cur.execute( sql_insert % (stn.wmo,param[key],betdate,now,self.data[stn.wmo][key]) )
            # - If there is no user-change, update
            elif res[0][0] == 0:
               #print("    Update ....")
               #print( sql_update % (now,self.data[wmo][key],wmo,param[key],betdate) )
               cur.execute( sql_update % (now,self.data[stn.wmo][key],stn.wmo,param[key],betdate) )
   

      self.db.commit()






   # ----------------------------------------------------------------
   # Small helper class for the 'special observation usage'
   # ----------------------------------------------------------------
   class special_obs_object(object):
      """This class is used to parse the `'special`' input arguments
      to :meth:`getobs.getobs.load_special_obs``."""

      def __init__( self, special, date ):
         """This class is used to parse the 'special' input arguments
         to get_obs.

         Args:
            special (:obj:`str`): String in a very special format. 
            date (:obj:`datetime.date`): Date object (date of the tournament).
         """

         ## Keep input args
         self.date      = date
         self.special   = special

         # Check whether the special option has the correct sytnax.
         # First group: parameter
         # Second group: 'from' statement
         # Third group 'to' statement
         regex_day  = "yesterday|today|tomorrow"
         regex_time = "[0-9]{1,2}:[0-9]{1,2}"
         regex = "^([a-zA-Z0-9]+)\s+({0:s})\s+({1:s})\s+to\s+({0:s})\s+({1:s}).*$".format(
                  regex_day,regex_time)

         import re
         mtch = re.match(regex,special)
         if not mtch:
            self.error = True
            return
         else:
            self.error = False
         self.parameter,self.from_keyword,self.from_time,self.to_keyword,self.to_time = mtch.groups()

         # Compute proper from/to datetime objects
         self.from_date = self._string_to_date_(self.from_keyword, self.from_time, date)
         self.to_date   = self._string_to_date_(self.to_keyword,   self.to_time,   date)


      # Helper function to show oject content
      def show( self ):
         if self.error:
            print("    Error: not able to extract required information from:")
            print("           from {0:s} for {1:s}".format( self.special, self.date ))
         else:
            print("    Parameter:    {0:s}".format( self.parameter ))
            print("    From:         {0:s} {1:s}".format( self.from_keyword, self.from_time ))
            print("    To:           {0:s} {1:s}".format( self.to_keyword,   self.to_time ))
            print("    Date is:      {0:s}".format( self.date.strftime("%Y-%m-%d %H:%M") ))
            print("    Yields from:  {0:s}".format( self.from_date.strftime("%Y-%m-%d %H:%M") ))
            print("    Yields to:    {0:s}".format( self.to_date.strftime("%Y-%m-%d %H:%M") ))
         
      # Create proper date objects given the keyword,
      # the time (e.g., 19:00) and the current tournament date 'date'
      def _string_to_date_(self,keyword,time,date):
         import re
         import datetime as dt
         hour,mins = re.match("^([0-9]{1,2}):([0-9]{1,2})$",time).groups()

         if keyword == 'yesterday':
            # If 'yesterday': subtract one day from 'date'
            date = date - dt.timedelta(1)
            # Create new date string
            date = "{0:s} {1:02d}:{2:02d}".format(
                   date.strftime("%Y-%m-%d"),int(hour),int(mins))
         elif keyword == 'today':
            # Create new date string
            date = "{0:s} {1:02d}:{2:02d}".format(
                   date.strftime("%Y-%m-%d"),int(hour),int(mins))
         elif keyword == 'tomorrow':
            # If 'tomorrow': add one day to 'date'
            date = date + dt.timedelta(1)
            # Create new date string
            date = "{0:s} {1:02d}:{2:02d}".format(
                   date.strftime("%Y-%m-%d"),int(hour),int(mins))
            
         # Convert the new proper date/time into a datetime object
         return dt.datetime.strptime(date,"%Y-%m-%d %H:%M") 
