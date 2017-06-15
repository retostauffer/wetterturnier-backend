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
# - L@ST MODIFIED: 2017-06-15 17:43 on prognose2.met.fu-berlin.de
# -------------------------------------------------------------------

import sys, os
import datetime as dt
import numpy as np

class getobs( object ):


   def __init__(self, config, db, city, date):
      """!Initialization of the @ref getobs.getobs class.
      
      @param config. List, contains all necessary configs for the
      pywetterturnier package. Please have a look into 
      @ref utils.readconfig for more details. 
      @return Returns nothing. Just contains several methods.
      """

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
      self.stations = self.db.get_stations_for_city( city['ID'] )

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
      """!Computes astronomic (maximum) sun shine duration for a set
      of stations. Note that the station has to be stored in the database
      table @b obs.stations. If not, we dont know the position of the   
      station and therefore we can't compute astronomical sunshine
      duration resulting in a None value.
      Uses external python package @astral.

      @param stations. List of @ref stationclass.stationclass objects.
      @param datetime object. Day of the observations.
      @return A dict consisting of WMO station number and
      the length of the astronomic day in seconds. 
      """

      import astral
      from datetime import datetime as dt

      # - self._maxSd_ used to store the info based on the wmo number
      maxSd = {}
      cur = self.db.cursor()
      sql = "SELECT name, lon, lat, hoehe FROM obs.stations WHERE statnr = %s"
      for station in stations:
         cur.execute( sql % station.wmo )
         res = cur.fetchone()

         # - no info? Skip
         if res == None:
            maxSd[station.wmo] = None
            print "[!] ERROR: Problems in get_maximum_Sd. Reason: \n" + \
                  "    there is no entry for wmo station %d in table\n" % station.wmo + \
                  "    obs.stations and I can't compute the astronomic\n" + \
                  "    sunshine duration."
            maxSd[station.wmo] = None
      
         # - Else
         else:

            # - Else compute day length
            nam = str(   res[0] )
            lon = float( res[1] )
            lat = float( res[2] )
            if int(res[3]) == None:
               elevation = 0
            else:
               elevation = int(res[3])

            # - Define location
            loc = astral.Location( (nam,'Region',lat,lon,'Europe/London',elevation) )
            res = loc.sun(local=True,date=date)
            daylen = int(res['sunset'].strftime('%s')) - int(res['sunrise'].strftime('%s'))
            daylen = daylen / 60.

            maxSd[station.wmo] = daylen

            print "    WMO station %7d: daylength %5.2f min (%5.2f h)" % \
                   (station.wmo,daylen,daylen/60.)

      return maxSd


   # ----------------------------------------------------------------
   # - Loading 
   # ----------------------------------------------------------------
   def get_columns( self, table ):
      """!Returns database table columns.
      @param table. String, name of the database table.
      @return A list of all available table columns.
      """

      sql = "SHOW COLUMNS FROM %s" % table
      cur = self.db.cursor()
      cur.execute(sql)
      tmp = cur.fetchall()
      res = []
      for rec in tmp: res.append( str(rec[0]).lower() )
      return res

   # ----------------------------------------------------------------
   # - Loading observations
   # ----------------------------------------------------------------
   def load_obs( self, wmo, hour, parameter ):
      """!Loading a specific observation from the database.
      The date for which the observation should be valid and the
      name of the database are coming from the public attributes of the
      class (@ref getobs.getobs).

      @param wmo. Numeric, WMO station number.
      @param hour. Integer, hour for which the observation should
      be valid [0,...,24].
      @return Either a numeric value or None if the cell in the
      database was empty (NULL).
      """

      from pywetterturnier import utils

      parameter = parameter.lower()
      if not parameter in self._columns_:
         utils.exit("Parameter %s does not exist in database table %s. Stop in getobs.load_obs" % \
                  (parameter, self._table_))

      tmp    = self._date_ + dt.timedelta( 0, hour*3600 )
      datum  = int( tmp.strftime('%Y%m%d') )
      stdmin = int( tmp.strftime('%H%M')   )
      #print "    - For station %6d: %d %04d try to load %s" % (wmo,datum,stdmin,parameter)

      # - Load from db
      sql = "SELECT %s FROM %s WHERE msgtyp='bufr' AND statnr=%d AND datum=%d AND stdmin=%d" % \
            (parameter, self._table_, wmo, datum, stdmin)

      cur = self.db.cursor()
      cur.execute( sql )
      data = cur.fetchall()

      # - No row in database at all 
      if len(data) == 0:
         return None
      elif len(data) > 1:
         utils.exit("got more than one row - thats not good. Stop.")
      # - Field is empty
      elif data[0][0] == None:
         return None

      # - Else return value
      return data[0][0]


   # ----------------------------------------------------------------
   # - Checks if a a certain observation at leas has a row in the
   #   database (wmo/time/date) row exits - do not check the
   #   content of the colums. 
   # ----------------------------------------------------------------
   def check_record( self, wmo, hour ):
      """!Checks if database record exists. Just checks if for the   
      current date/time/station combination a row exists in the database
      and not what a specific cell contains. Note: date, and table name
      are coming from the public attributes of @ref getobs.getobs .

      @param wmo. Integer, WMO station number.
      @param hour. Integer, hour time shift relative to the 'date', 00:00 UTC.
         As an example: hour=30 means that we are checking 'tomorrow 06:00 UTC'.
      @return Boolean value. False if no such row exists, else True.
      """

      datumsec   = self._date_ + dt.timedelta( 0, hour*3600 )
      datumsec   = int( datumsec.strftime('%s') )
      sql = "SELECT count(*) FROM %s WHERE msgtyp='bufr' AND statnr=%d AND datumsec = %d" % \
            (self._table_, wmo, datumsec )
      cur = self.db.cursor()
      cur.execute( sql )
      data = cur.fetchone()

      # - Else return value
      return (int(data[0]) > 0)


   # ----------------------------------------------------------------
   # - Adding value
   # ----------------------------------------------------------------
   def _add_obs_value_(self,parameter,wmo,value):
      """!Adds a loaded observation to the final data object stored on the
      parent @ref getobs.getobs object. Appends all data to the
      public attribute getobs.getobs.data .
      @param parameter. String, wetterturnier parameter shortname.
      @param wmo. Integer, WMO station number.
      @param value. Either a numeric value or None.
      """

      # - If value is none: return
      if value == None: return
      # - Initialize data object and add new dict with key wmo
      if not self.data:
         self.data = {wmo:{}}
      # - Adding new dict with key wmo
      elif not wmo in self.data.keys():
         self.data[wmo] = {}
      # - Adding value
      self.data[wmo][parameter] = value


   # ----------------------------------------------------------------
   # - Calling the prepare_fun methods for the different
   #   parameters like TTm, TTn, ... 
   # ----------------------------------------------------------------
   def prepare( self, parameter ):
      """!Prepares the different observed parameters like TTn, TTm, N,
      and so on. Note that the script will ignore a wrong specified
      or unknown parameter as the internal method then does not exist. 
      The date will be taken from the public arguments of the parent
      class @ref getobs.getobs.

      @param parameter. String, shortname of the Wetterturnier parameters. 
      @return No return. Appends data to internal object. 
      """

      try:
         fun = eval("self._prepare_fun_%s_" % parameter)
      except Exception as e:
         print "[!] WARNING: method prepare_fun_%s does not exist. Cannot prepare data." % parameter
         print e
         return

      import inspect
      if not inspect.ismethod( fun ):
         print "[!] WARNING: method prepare_fun_%s is no instancemethod. Cannot prepare data." % parameter
         return

      # - Else calling function
      for station in self.stations:
         value = fun(station)
         self._add_obs_value_(parameter,station.wmo,value)

   # ----------------------------------------------------------------
   # - Prepare TTm
   # ----------------------------------------------------------------
   def _prepare_fun_TTm_(self,station):
      """!Helper function for TTM, maximum temperature. Returns 18 UTC maximum
      temperature, either from column tmax12 or - if tmax12 not available
      but tmax24 exists - maximum temperature from tmax24.
      Temperature will be in 1/10 degrees Celsius.

      @param station. Object of class @ref stationclass.stationclass.
      @return numeric or None. Returns observed value if loading data
         was successful, or None if observation not available or nor recorded
      """

      # - Loading tmax24 and tmax12 (12h/24 period maximum)
      #   valid for 18 UTC in the evening for the current date 
      tmax12 = self.load_obs( station.wmo, 18, 'tmax12' )
      tmax24 = self.load_obs( station.wmo, 18, 'tmax24' )
      # - If tmax12 is valid: take this one
      if not tmax12 == None:
         value = tmax12
      # - Else if tmax24 is valid, take this one
      elif not tmax24 == None:
         value = tmax24
      # - Else value is None
      else: 
         value = None
      # - Return value
      return value


   # ----------------------------------------------------------------
   # - Prepare TTn
   # ----------------------------------------------------------------
   def _prepare_fun_TTn_(self,station):
      """!Helper function for TTN, minimum temperature. Returns 06 UTC minimum
      temperature. Simply the tmin12 column at 06 UTC in 1/10 degrees Celsius.

      @param station. Object of class stationclass.
      @return numeric or None. Returns observed value if loading data
         was successful, or None if observation not available or nor recorded
      """

      # - Loading tmax24 and tmax12 (12h/24 period maximum)
      #   valid for 18 UTC in the evening for the current date 
      value = self.load_obs( station.wmo,  6, 'tmin12' )
      # - Return value
      return value 


   # ----------------------------------------------------------------
   # - Prepare TTd
   # ----------------------------------------------------------------
   def _prepare_fun_TTd_(self,station):
      """!Helper function for dew point temperature. Returns 12 UTC observed
      dew point temperature from database column td in 1/10 degrees Celsius.

      @param station. Object of class stationclass.
      @return numeric or None. Returns observed value if loading data
         was successful, or None if observation not available or nor recorded
      """

      # - Loading td valid at 12 UTC 
      value = self.load_obs( station.wmo, 12, 'td' )
      # - Return value
      return value


   # ----------------------------------------------------------------
   # - Prepare PPP
   # ----------------------------------------------------------------
   def _prepare_fun_PPP_(self,station):
      """!Helper function for mean sea level pressure at 12 UTC.
      Based on database column pmsl. Return value will be in 1/10 hPa.

      @param station. Object of class stationclass.
      @return numeric or None. Returns observed value if loading data
         was successful, or None if observation not available or nor recorded
      """

      # - Loading td valid at 12 UTC 
      value = self.load_obs( station.wmo, 12, 'pmsl' )
      # - Original value is in 1/100 hPa. Convert.
      if not value == None:
         import numpy as np
         value = np.round( value/10. ) 
      # Return value 
      return value


   # ----------------------------------------------------------------
   # - Prepare dd
   # ----------------------------------------------------------------
   def _prepare_fun_dd_(self,station):
      """!Helper function for the wind direction at 12 UTC from database
      column dd. Values will be returned in 1/10 degrees but rounded
      to full 10 degrees. E.g., observed '138' degrees will be converted
      into '1400' (1/10 degrees, rounded to full 10 degrees). 
      Special case: also depends on database column ff. The following
      cases will be used:
      @arg 1) if dd not observed/received: @b return None
      @arg 2) if dd==0 and ff==0:          @b return 0.0
      @arg 3) if dd==0 and ff>0:           @b return None (variable wind direction)
      @arg 4) else:                        @b return value

      @param station. Object of class stationclass.
      @return numeric or None. Returns observed value if loading data
         was successful, or None if observation not available or nor recorded
      """

      # - Loading td valid at 12 UTC 
      dd = self.load_obs( station.wmo, 12, 'dd' )
      ff = self.load_obs( station.wmo, 12, 'ff' )
      # - If dd is valid: take this one
      if dd == None:
         value = None
      # - if wind direction is 0 (variable) 
      elif dd == 0:
         # - No wind: return variable wind!
         if ff == 0:    value = 0 
         # - Else skip the dd observation!
         else:          value = None
      # - Else take dd as it is
      else: 
         value = np.round(float(dd)/10) * 100.
         # - North wind will be 360, not 0. Change if 0 occurs
         if value == 0.: value = 3600.
      # - Return value
      return value

   # ----------------------------------------------------------------
   # - Prepare ff
   # ----------------------------------------------------------------
   def _prepare_fun_ff_(self,station):
      """!Helper function for the wind speed at 12 UTC. Based on database
      column ff. Values will be in 1/10 knots but rounded to full knots.
      E.g., if 3.2m/s observed -> 6.22kt -> Return value will be 60. 
      Args:
         parameter (string): string with parameter short name (e.g., TTm, N, RR)
         station (class): stationclass object. 
      Returns:
         numeric: observed value if loading data was successful 
         None: if observation not available or nor recorded
      @param station. Object of class stationclass.
      @return numeric or None. Returns observed value if loading data
         was successful, or None if observation not available or nor recorded
      """

      # - Loading td valid at 12 UTC 
      value = self.load_obs( station.wmo, 12, 'ff' )
      if not value == None:
         import numpy as np
         value = np.round( np.float( value ) * 1.94384449 / 10 ) * 10
      # - Return value  
      return value

   # ----------------------------------------------------------------
   # - Loading fx (maximum wind gust over last 1h, 6 to 6 UTC)
   # ----------------------------------------------------------------
   def _prepare_fun_fx_(self,station):
      """!Helper function for the maximum gust speed (fx > 25kt).
      Based on database column fx1. Return value will be in 1/10 knots but
      rounded to full knots. 
      E.g., if 21.2m/s observed -> 41.21kt -> Return value will be 410. 
      Special cases:
      @arg 1) no observation available but +30h
           observation (row) is in database:
           Assume that there were no gusts at all:      @b return 0
      @arg 2) no observations available and +30h
            observation (row) not yet in database:      @b return None 
      @arg 3) observation available, below 25 knots:    @b return 0 
      @arg 4) observation available, >= 25 knots:       @b return value

      @param station. Object of class stationclass.
      @return numeric or None. Returns observed value if loading data
         was successful, or None if observation not available or nor recorded
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
      def append_data(data,tmp):
         for rec in tmp:  data.append( rec[0] )
         return data

      # - FFX (last 10 min gusts) 
      cur.execute( sql  );     tmp = cur.fetchall();     data = append_data( data, tmp )
      # - FFX1 (last 1 h gusts) 
      cur.execute( sql1 );     tmp = cur.fetchall();     data = append_data( data, tmp )
      # - FFX1 (last 3 h gusts) 
      cur.execute( sql3 );     tmp = cur.fetchall();     data = append_data( data, tmp )
      # - FFX1 (last 6 h gusts) 
      cur.execute( sql6 );     tmp = cur.fetchall();     data = append_data( data, tmp )

      # - Check if +30 h observation is available.
      check30 = self.check_record( station.wmo, 30 )

      # - No wind gusts received, but last observation is here
      if len(data) == 0 and check30:
         value = 0
      # - No observations at all
      elif len(data) == 0:
         value = None
      # - Else sum up
      else:
         value = 0
         import numpy as np
         for rec in data: value = np.maximum(value,rec) 
         # - Convert from meters per second to knots.
         #   Moreover, if knots are below 25, ignore.
         value = np.round( np.float( value ) * 1.94384449 / 10. ) * 10
         if value < 250.: value = 0
      # - Return value  
      return value


   # ----------------------------------------------------------------
   # - Prepare N
   # ----------------------------------------------------------------
   def _prepare_fun_N_(self,station):
      """!Helper function for cloud cover at 12 UTC. Return value
      will be in 1/10 octas, rounded to full octas [0,10,20,30,...,80]. 
      Observations based on database column cc.
      @arg 1) if observation is available:       @b return value
      @arg 2) if observation not recorded but
            12 UTC database entry exists we
            assume that there were no clouds:     @b return 0
      @arg 3) else:                               @b return None

      @param station. Object of class stationclass.
      @return numeric or None. Returns observed value if loading data
         was successful, or None if observation not available or nor recorded
      """

      # - Loading td valid at 12 UTC 
      N = self.load_obs( station.wmo, 12, 'cc' )
      # - If tmax12 is valid: take this one
      if not N == None:
         import numpy as np
         # - Note: BUFR report is in percent
         value = np.round(np.float(N)/100.*8.) * 10 
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
   def _prepare_fun_Wv_(self,station):
      """!Helper function for significant weather observatioins between
      06 UTC and 12 UTC (forenoon) based on database table w1.
      Value will be in 1/10 levels [0,10,20,...,90].
         1) if observation not recorded but
            12 UTC database entry exists we
            assume that there were no clouds       return 0
         2) if observation not recorded and
            12 UTC database entry not available    return None
         3) If observation is = 10 (no sign weather)
            we can return class 0                  @b return 0
         4) observation here BUT 
            the observed value is > 10 (note:
            BUFR messages, > 10 are for automated
            significant weather instruments)       return None 
         5) If observation is 1, 2, or 3: set to 0
            as 1, 2, 3 are not used in the WT      return 0
         6) else                                   return value

      @param station. Object of class stationclass.
      @return numeric or None. Returns observed value if loading data
         was successful, or None if observation not available or nor recorded
      """

      check12 = self.check_record( station.wmo, 12 )
      w1 = self.load_obs( station.wmo, 12, 'w1' )
      # - Not observed
      if w1 == None:
         if check12:    value = 0
         else:          value = None
      # - Observed 
      else:
         # - If there is no significant weather, the BUFR reports a
         #   code 10 on w1/w2 (no sign weather phaenomena).
         #   In this case we can return a 0.
         if int(w1) == 10:           value = 0
         elif w1 >  10.:             value = None    # automated observation
         elif w1 >= 1. and w1 <= 4.: value = 0       # 1,2,3 is not used
         else:                       value = w1 * 10 # juchee
      # - Return value  
      return value


   # ----------------------------------------------------------------
   # - Prepare Wn
   # ----------------------------------------------------------------
   def _prepare_fun_Wn_(self,station):
      """!Helper function for significant weather observatioins between
      12 UTC and 18 UTC (afternoon). Based on database table w1.
      Value will be in 1/10 levels [0,10,20,...,90].
         1) if observation not recorded but
            18 UTC database entry exists we
            assume that there were no clouds:      @b return 0
         2) if observation not recorded and
            18 UTC database entry not available:   @b return None
         3) If observation is = 10 (no sign weather)
            we can return class 0                  @b return 0
         4) observation here BUT 
            the observed value is > 10 (note:
            BUFR messages, > 10 are for automated
            significant weather instruments):      @b return None 
         5) If observation is 1, 2, or 3: set to 0
            as 1, 2, 3 are not used in the WT      return 0
         6) else:                                @b return value

      @param station. Object of class stationclass.
      @return numeric or None. Returns observed value if loading data
         was successful, or None if observation not available or nor recorded
      """

      check18 = self.check_record( station.wmo, 18 )
      w1 = self.load_obs( station.wmo, 18, 'w1' )
      # - Not observed
      if w1 == None:
         if check18:    value = 0. 
         else:          value = None
      # - Observed 
      else:
         # - If there is no significant weather, the BUFR reports a
         #   code 10 on w1/w2 (no sign weather phaenomena).
         #   In this case we can return a 0.
         if int(w1) == 10:           value = 0
         elif w1 >  10.:             value = None    # automated observation
         elif w1 >= 1. and w1 <= 4.: value = 0       # 1,2,3 is not used
         else:                       value = w1 * 10 # juchee
      # - Return value  
      return value


   # ----------------------------------------------------------------
   # - Loading RR
   # ----------------------------------------------------------------
   def _prepare_fun_RR_(self,station):
      """!Helper function for 24h sum of precipitation based on
      database column 'rrr12' at +18 and +30h (as the reported
      observations are 12h sums this means from 06 UTC today
      to 06 UTC tomorrow). Returns precipitation in 1/10 mm
      OR -30 if there was no precipitation at all.
      @arg First: if database entry for 18 UTC is here but
           there is no recorded amount of precipitation we
           have to assume that there was no precipitation.
           The same for +30h (06 UTC next day).
      @arg Second:
           If observed precipitation amount is negative (some
           stations send -0.1mm/12h for no precipitation) we

      @param station. Object of class stationclass.
      @return numeric or None. Returns observed value if loading data
         was successful, or None if observation not available or nor recorded
      """

      # ----------------------------------------------------------
      # RR - Precipitation (2 * 12h)
      #      06 today to 06 tomorrow!!
      # ----------------------------------------------------------
      RR18 = self.load_obs( station.wmo, 18, 'rrr12' )
      RR06 = self.load_obs( station.wmo, 30, 'rrr12' )
      # - Check if observations (records) are hete
      check18 = self.check_record( station.wmo, 18 )
      check06 = self.check_record( station.wmo, 30 )

      # - If observed values RR18/RR06 are empty but the observations
      #   are in the database we have to assume that there was no
      #   precipitation at all. Set these values to -3.0 (no precip).
      if RR18 == None and check18: RR18 = -3.0
      if RR06 == None and check06: RR06 = -3.0

      # - Both observations available: use them
      if not RR18 == None and not RR06 == None:
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

         # Check if all W1-observations are 10 (no sign. weather reported)
         # And precipitation sum is 0 mm: return -3.0.
         print value
         if all( item in [None,10] for item in W1):
            value = -30.

      # - Return value  
      return value


   # ----------------------------------------------------------------
   # - Loading sunshine. 
   # ----------------------------------------------------------------
   def _prepare_fun_Sd_(self,station):
      """!Helper function for relative sun shine duration for the
      full day. Will be returned in 1/10 percent rounded to
      full percent (34% will result in 340.).
      @arg 1) if 24h sum is available on 'sunday' on 06 UTC we will 
              take this value.
      @arg 2) if 06UTC sunday is not available but we have a sunday
              value at 00 UTC: take this one.
      @arg 3) else sum up the 'sun' 1h-rly obs. WARNING: seems that
              'none' is either 'no sun' or 'not reported'. I can't
              decide which one is which one at the moment. I just
              take none = 0 and sum up.

      @param station. Object of class stationclass.
      @return numeric or None. Returns observed value if loading data
         was successful, or None if observation not available or nor recorded
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
         tmp = self.load_obs( station.wmo, 30, 'sunday' )
         if tmp:
            value =int( np.round(np.float(tmp)/np.float(self._maxSd_[station.wmo]) * 100) ) * 10
         # - Loading sunshine 24h sum, next day reported at 00UTC
         #   which is +24 hours from self._date_
         else:
            tmp = self.load_obs( station.wmo, 24, 'sunday' )
            if tmp:
               Sd = int( np.round(np.float(tmp)/np.float(self._maxSd_[station.wmo]) * 100) ) * 10
               value = Sd 
            # - Else try to sum up hourly observations
            else:
               # - Else try to get the hourly sums.
               datum = int( self._date_.strftime('%Y%m%d') )
               sql = "SELECT sun FROM %s WHERE statnr = %d AND " % (self._table_,station.wmo) + \
                     "msgtyp = 'bufr' AND datum = %d AND NOT sun IS NULL" % datum

               cur = self.db.cursor()
               cur.execute( sql )
               tmp = cur.fetchall()

               # - No data? Return None
               if len(tmp) == 0:
                  value = None
               else:
                  # - Else sum up
                  value = 0
                  for rec in tmp: value += int(rec[0])
                  value = int( np.round(np.float(value)/np.float(self._maxSd_[station.wmo]) * 100) ) * 10

      # - Return value
      return value


   # ----------------------------------------------------------------
   # - Show loaded data
   # ----------------------------------------------------------------
   def show( self ):
      """!Shows a summary of the current @ref getobs.getobs class.
      Was mainly used for development purposes. Shows data and stuff
      stored on class attributes.
      """

      if not self.data:
         print "    Can't show data summary: no observation data loaded"
         return

      # - Else show data
      allcols = []
      for rec in self.data:
         for k in self.data[rec].keys():
            if not k in allcols: allcols.append(k)
      allcols.sort()

      # - Show data
      print "     ",
      for stn in self.stations:
         print " %13d   " % stn.wmo,
      print ""

      # - Looping over params
      pnr = 0
      for param in allcols:
         pnr = pnr + 1 
         print "   %2d  " % pnr,
         for stn in self.stations:
            if not stn.wmo in self.data.keys():
               continue
            elif not param in self.data[stn.wmo].keys():
               print " %-5s %8s   " % (param,"- - -"),
            else:
               print " %-5s %8d   " % (param,self.data[stn.wmo][param]),

         print ""
         

   # ----------------------------------------------------------------
   # - Save to database
   # ----------------------------------------------------------------
   def write_to_db( self ):
      """!Write prepared observations to database. Writes all prepared
      observations which are stored in the parent @ref getobs.getobs class
      to the Wetterturnier database.
      """

      if self.data == None:   
         print "Cant write data to database. Because there are no data. Return."
         return

      # - Create tuple for update
      data = []

      param = {}
      for p in self.db.get_parameter_names():
         id = self.db.get_parameter_id( p )
         param[p] = id

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

         if not stn.wmo in self.data.keys():
            print "[!] Can't find wmo %d in results. Skip." % stn.wmo
            continue

         for key in self.data[stn.wmo].keys():

            # - If parameter is not one of the wetterturnier parameters: skip
            if not key in param:
               print "[!] Cant find parameter %s in database! Skip!" % key
               continue

            # - See if parameter is in NULLCONFIG of the station.
            #   If it is - ignore!
            if type(stn.nullconfig) == type(list()):
               if param[key] in stn.nullconfig:
                  print "    Parameter %s (%d) is in nullconfig of station %d. Skip." % \
                        (key, param[key], stn.wmo)
                  continue

            # - Else append tuple
            tmp = (stn.wmo, param[key], betdate, now, self.data[stn.wmo][key])
            data.append(tmp)

            # - Checking SQL
            cur.execute( sql_check % (stn.wmo,betdate,param[key]) )
            res = cur.fetchall()

            # - If length res is empty: INSERT
            if len(res) == 0:
               #print "    Insert ...."
               cur.execute( sql_insert % (stn.wmo,param[key],betdate,now,self.data[stn.wmo][key]) )
            # - If there is no user-change, update
            elif res[0][0] == 0:
               #print "    Update ...."
               #print( sql_update % (now,self.data[wmo][key],wmo,param[key],betdate) )
               cur.execute( sql_update % (now,self.data[stn.wmo][key],stn.wmo,param[key],betdate) )
   

      self.db.commit()

























