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
# - L@ST MODIFIED: 2015-08-02 15:42 on prognose2.met.fu-berlin.de
# -------------------------------------------------------------------

import sys, os
import datetime as dt
import numpy as np

class getobs( object ):


   def __init__(self, config, db, city, date):

      self.config = config
      self.city   = city
      self.date   = date
      self.db     = db
      self.table  = config['mysql_obstable'] 
      self.data   = None

      # - Loading available columns in self.table
      self.columns = self.get_columns()

      # - Loading wmo stations for this city
      #self.stations = self.db.get_station_numbers_for_city( city['ID'] )
      self.stations = self.db.get_stations_for_city( city['ID'] )

      if len(self.stations) == 0: return False

      # - Compute day length
      self.maxSd = self.get_maximum_Sd()


   # ----------------------------------------------------------------
   # - Compute maximum day length using the python astral package.
   # ----------------------------------------------------------------
   def get_maximum_Sd( self ):

      import astral
      from datetime import datetime as dt

      # - self.maxSd used to store the info based on the wmo number
      maxSd = {}
      cur = self.db.cursor()
      sql = "SELECT name, lon, lat, hoehe FROM obs.stations WHERE statnr = %s"
      for stn in self.stations:
         cur.execute( sql % stn.wmo )
         res = cur.fetchone()

         # - no info? Skip
         if res == None:
            maxSd[stn.wmo] = None
            print "[!] ERROR: Problems in get_maximum_Sd. Reason: \n" + \
                  "    there is no entry for wmo station %d in table\n" % stn.wmo + \
                  "    obs.stations and I can't compute the astronomic\n" + \
                  "    sunshine duration."
            maxSd[stn.wmo] = None
      
         # - Else
         else:

            # - Else compute day length
            nam = str( res[0] )
            lon = float( res[1] )
            lat = float( res[2] )
            if int(res[3]) == None:
               elevation = 0
            else:
               elevation = int(res[3])

            # - Define location
            loc = astral.Location( (nam,'Region',lat,lon,'Europe/London',elevation) )
            res = loc.sun(local=True,date=self.date)
            daylen = int(res['sunset'].strftime('%s')) - int(res['sunrise'].strftime('%s'))
            daylen = daylen / 60.

            maxSd[stn.wmo] = daylen

            print "    WMO station %7d: daylength %5.2f min (%5.2f h)" % \
                   (stn.wmo,daylen,daylen/60.)

      return maxSd


   # ----------------------------------------------------------------
   # - Loading 
   # ----------------------------------------------------------------
   def get_columns( self ):

      sql = "SHOW COLUMNS FROM %s" % self.table
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

      parameter = parameter.lower()
      if not parameter in self.columns:
         sys.exit("Parameter %s does not exist in database table %s. Stop in getobs.load_obs" % \
                  (parameter, self.table))

      tmp    = self.date + dt.timedelta( 0, hour*3600 )
      datum  = int( tmp.strftime('%Y%m%d') )
      stdmin = int( tmp.strftime('%H%M')   )
      #print "    - For station %6d: %d %04d try to load %s" % (wmo,datum,stdmin,parameter)

      # - Load from db
      sql = "SELECT %s FROM %s WHERE msgtyp='bufr' AND statnr=%d AND datum=%d AND stdmin=%d" % \
            (parameter, self.table, wmo, datum, stdmin)

      cur = self.db.cursor()
      cur.execute( sql )
      data = cur.fetchall()

      # - No row in database at all 
      if len(data) == 0:
         return None
      elif len(data) > 1:
         sys.exit("ERROR: got more than one row - thats not good. Stop.")
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

      datumsec   = self.date + dt.timedelta( 0, hour*3600 )
      datumsec   = int( datumsec.strftime('%s') )
      sql = "SELECT count(*) FROM %s WHERE msgtyp='bufr' AND statnr=%d AND datumsec = %d" % \
            (self.table, wmo, datumsec )
      cur = self.db.cursor()
      cur.execute( sql )
      data = cur.fetchone()

      # - Else return value
      return (int(data[0]) > 0)

   



   # ----------------------------------------------------------------
   # - Loading sunshine. 
   #   1) if 24h sum is available on 'sunday' on 06 UTC we will 
   #      take this value.
   #   2) if 06UTC sunday is not available but we have a sunday
   #      value at 00 UTC: take this one.
   #   3) else sum up the 'sun' 1h-rly obs. WARNING: seems that
   #      'none' is either 'no sun' or 'not reported'. I can't
   #      decide which one is which one at the moment. I just
   #      take none = 0 and sum up.
   # ----------------------------------------------------------------
   def load_sunshine( self, wmo ):

      # - If we have not loaded maxSd: stop
      if not wmo in self.maxSd:
         sys.exit("ERROR: maximum sunshine duration for station %d unknown.\n" % wmo + \
                  "Most possible reason: there is no entry for this station\n" + \
                  "in the table obs.stations and therefore I can't compute\n" + \
                  "the astronomic sunshine duration which is needed!")

      # - If we dont have any information about the maximum Sd we cant
      #   compute the relative value. In this case return False
      if not self.maxSd[wmo]: return False

      # - Loading sunshine 24h sum, next day reported at 06UTC
      #   which is +30 hours from self.date.
      tmp = self.load_obs( wmo, 30, 'sunday' )
      if tmp:
         tmp =int( np.round(np.float(tmp)/np.float(self.maxSd[wmo]) * 100) ) * 10
         return tmp

      # - Loading sunshine 24h sum, next day reported at 00UTC
      #   which is +24 hours from self.date
      tmp = self.load_obs( wmo, 24, 'sunday' )
      if tmp:
         tmp =int( np.round(np.float(tmp)/np.float(self.maxSd[wmo]) * 100) ) * 10
         return tmp
   
      # - Else try to get the hourly sums.
      datum = int( self.date.strftime('%Y%m%d') )
      sql = "SELECT sun FROM %s WHERE statnr = %d AND " % (self.table,wmo) + \
            "msgtyp = 'bufr' AND datum = %d AND NOT sun IS NULL" % datum

      cur = self.db.cursor()
      cur.execute( sql )
      tmp = cur.fetchall()

      # - No data? Return False
      if len(tmp) == 0: return False
      
      # - Else sum up
      Sd = 0
      for rec in tmp: Sd += int(rec[0])
      Sd =int( np.round(np.float(Sd)/np.float(self.maxSd[wmo]) * 100) ) * 10

      return Sd 


   # ----------------------------------------------------------------
   # - Adding value
   # ----------------------------------------------------------------
   def __add_obs_value__(self,what,wmo,value):

      # - If value is none: return
      if value == None: return
      # - Initialize data object and add new dict with key wmo
      if not self.data:
         self.data = {wmo:{}}
      # - Adding new dict with key wmo
      elif not wmo in self.data.keys():
         self.data[wmo] = {}
      # - Adding value
      self.data[wmo][what] = value


   # ----------------------------------------------------------------
   # - Calling the prepare_fun methods for the different
   #   parameters like TTm, TTn, ... 
   # ----------------------------------------------------------------
   def prepare( self, what ):

      try:
         fun = eval("self.prepare_fun_%s" % what)
      except Exception as e:
         print "[!] WARNING: method prepare_fun_%s does not exist. Cannot prepare data." % what
         print e
         return

      import inspect
      if not inspect.ismethod( fun ):
         print "[!] WARNING: method prepare_fun_%s is no instancemethod. Cannot prepare data." % what
         return

      # - Else calling function
      for stn in self.stations:
         fun(what,stn)

   # ----------------------------------------------------------------
   # - Prepare TTm (Maximum Temperature)
   #   Returns temperature in 1/10 celsius
   # ----------------------------------------------------------------
   def prepare_fun_TTm(self,what,stn):

      # - Loading tmax24 and tmax12 (12h/24 period maximum)
      #   valid for 18 UTC in the evening for the current date 
      tmax12 = self.load_obs( stn.wmo, 18, 'tmax12' )
      tmax24 = self.load_obs( stn.wmo, 18, 'tmax24' )
      # - If tmax12 is valid: take this one
      if not tmax12 == None:
         value = tmax12
      # - Else if tmax24 is valid, take this one
      elif not tmax24 == None:
         value = tmax24
      # - Else value is None
      else: 
         value = None
      # - Add value
      self.__add_obs_value__(what,stn.wmo,value)


   # ----------------------------------------------------------------
   # - Prepare TTn (Minimum Temperature)
   #   Returns temperature in 1/10 celsius
   # ----------------------------------------------------------------
   def prepare_fun_TTn(self,what,stn):

      # - Loading tmax24 and tmax12 (12h/24 period maximum)
      #   valid for 18 UTC in the evening for the current date 
      value = self.load_obs( stn.wmo,  6, 'tmin12' )
      ####tmin12 = self.load_obs( stn.wmo,  6, 'tmin12' )
      ##### - If value not valid: skip 
      ####if tmin12 == None:
      ####   value = None
      ##### - Else take value
      ####else:
      ####   value = tmin12
      # - Add value
      self.__add_obs_value__(what,stn.wmo,value)


   # ----------------------------------------------------------------
   # - Prepare TTd (Dewpoint Temperature at 12 UTC)
   #   Returns temperature in 1/10 celsius
   # ----------------------------------------------------------------
   def prepare_fun_TTd(self,what,stn):

      # - Loading td valid at 12 UTC 
      value = self.load_obs( stn.wmo, 12, 'td' )
      ###td = self.load_obs( stn.wmo, 12, 'td' )
      #### - If value not valid: skip 
      ###if td == None:
      ###   value = None
      #### - Else take value
      ###else: 
      ###   value = td 
      # - Add value
      self.__add_obs_value__(what,stn.wmo,value)


   # ----------------------------------------------------------------
   # - Prepare PPP (mean sea level pressure at 12 UTC)
   #   Returns pressure in 1/10 hPa 
   # ----------------------------------------------------------------
   def prepare_fun_PPP(self,what,stn):

      # - Loading td valid at 12 UTC 
      value = self.load_obs( stn.wmo, 12, 'pmsl' )
      ###pmsl = self.load_obs( stn.wmo, 12, 'pmsl' )
      #### - If value not valid: skip 
      ###if pmsl == None:
      ###   value = None
      #### - Else take value
      ###else: 
      if not value == None:
         import numpy as np
         value = np.round( value/10. ) 
      # - Add value
      self.__add_obs_value__(what,stn.wmo,value)


   # ----------------------------------------------------------------
   # - Prepare dd (wind direction at 12 UTC)
   #   Returns cirection in degrees*10 
   # ----------------------------------------------------------------
   def prepare_fun_dd(self,what,stn):

      # - Loading td valid at 12 UTC 
      dd = self.load_obs( stn.wmo, 12, 'dd' )
      ff = self.load_obs( stn.wmo, 12, 'ff' )
      # - If dd is valid: take this one
      if dd == None:
         value = None
      # - if wind direction is 0 (variable) 
      elif dd == 0:
         # - No wind: return variable wind!
         if ff == 0:    value = np.round(float(dd)/10) * 100.
         # - Else skip the dd observation!
         else:          value = None
      # - Else take dd as it is
      else: 
         value = np.round(float(dd)/10) * 100.
      # - Add value
      self.__add_obs_value__(what,stn.wmo,value)

   # ----------------------------------------------------------------
   # - Prepare ff (wind speed at 12 UTC in knots)
   #   Returns wind in full knots but in 1/10 knots resolution
   # ----------------------------------------------------------------
   def prepare_fun_ff(self,what,stn):

      # - Loading td valid at 12 UTC 
      value = self.load_obs( stn.wmo, 12, 'ff' )
      ##ff = self.load_obs( stn.wmo, 12, 'ff' )
      ### - If value not valid: skip 
      ##if ff == False:
      ##   value = None
      ##else:
      if not value == None:
         import numpy as np
         value = np.round( np.float( value ) * 1.94384449 / 10 ) * 10
      # - Add value
      self.__add_obs_value__(what,stn.wmo,value)

   # ----------------------------------------------------------------
   # - Loading fx (maximum wind gust over last 1h, 6 to 6 UTC)
   #   Returns fx in full knots as soon as over 25, unit in 1/10 knots.
   # ----------------------------------------------------------------
   def prepare_fun_fx(self,what,stn):

      # - Timestamps
      ts1 = self.date + dt.timedelta(0, 6*3600); ts1 = int(ts1.strftime("%s"))
      ts2 = self.date + dt.timedelta(0,30*3600); ts2 = int(ts2.strftime("%s"))

      # - Else try to get the hourly sums.
      sql = "SELECT ffx1 FROM %s WHERE statnr = %d AND msgtyp = 'bufr' " % (self.table,stn.wmo) + \
            "AND datumsec > %s AND datumsec <= %d AND NOT ffx1 IS NULL" % (ts1,ts2)

      cur = self.db.cursor()
      cur.execute( sql )
      tmp = cur.fetchall()

      check30 = self.check_record( stn.wmo, 30 )

      # - No wind gusts received, but last observation is here
      if len(tmp) == 0 and check30:
         value = 0
      # - No observations at all
      elif len(tmp) == 0:
         value = None
      # - Else sum up
      else:
         value = 0
         import numpy as np
         for rec in tmp: value = np.maximum(value,rec[0]) 
         # - Convert from meters per second to knots.
         #   Moreover, if knots are below 25, ignore.
         value = np.round( np.float( value ) * 1.94384449 / 10. ) * 10
         if value < 250.: value = 0
      # - Add value
      self.__add_obs_value__(what,stn.wmo,value)


   # ----------------------------------------------------------------
   # - Prepare N (cloud cover at 12 UTC)
   #   Returns clouds in octa * 10 
   # ----------------------------------------------------------------
   def prepare_fun_N(self,what,stn):

      # - Loading td valid at 12 UTC 
      N = self.load_obs( stn.wmo, 12, 'cc' )
      # - If tmax12 is valid: take this one
      if N:
         import numpy as np
         # - Note: BUFR report is in percent
         value = np.round(np.float(N)/100.*8.) * 10 
      # - Else if record exists but there is no observed
      #   cloud cover we have to assume that the value
      #   should be 0 but is not reported at all. 
      elif self.check_record( stn.wmo, 12 ): 
         value = 0
      else:
         value = None
      # - Add value
      self.__add_obs_value__(what,stn.wmo,value)


   # ----------------------------------------------------------------
   # - Prepare Wv (weather between 06 and 12 UTC based on w1)
   #   Returns class times 10 
   # ----------------------------------------------------------------
   def prepare_fun_Wv(self,what,stn):

      w1 = self.load_obs( stn.wmo, 12, 'w1' )
      if w1 and w1 < 10:
         value = w1 * 10
      # - If no valid observation but record exists we have to
      #   assume that there is no record because there was no
      #   significant weather at all.
      elif self.check_record( stn.wmo, 12 ):
         value = 0.
      # - Else no data 
      else:
         value = None 
      # - Add value
      self.__add_obs_value__(what,stn.wmo,value)


   # ----------------------------------------------------------------
   # - Prepare Wn (weather between 12 and 18 UTC based on w1)
   #   Returns class times 10 
   # ----------------------------------------------------------------
   def prepare_fun_Wn(self,what,stn):

      w1 = self.load_obs( stn.wmo, 18, 'w1' )
      if w1 and w1 < 10:
         value = w1 * 10
      # - If no valid observation but record exists we have to
      #   assume that there is no record because there was no
      #   significant weather at all.
      elif self.check_record( stn.wmo, 18 ):
         value = 0.
      # - Else no data 
      else:
         value = None 
      # - Add value
      self.__add_obs_value__(what,stn.wmo,value)


   # ----------------------------------------------------------------
   # - Loading RR (precipitation as 24h sum) 
   #   Returns sum in 1/10 mm
   # ----------------------------------------------------------------
   def prepare_fun_RR(self,what,stn):

      # ----------------------------------------------------------
      # RR - Precipitation (2 * 12h)
      #      06 today to 06 tomorrow!!
      # ----------------------------------------------------------
      RR18 = self.load_obs( stn.wmo, 18, 'rrr12' )
      RR06 = self.load_obs( stn.wmo, 30, 'rrr12' )
      # - Check if observations (records) are hete
      check18 = self.check_record( stn.wmo, 18 )
      check06 = self.check_record( stn.wmo, 30 )
      # - IF RR18 is None (no value) but the observation
      #   for 18 UTC is hereL set RR18 to 0.0 (we have to
      #   assume that non-observed is = 0.0).
      #   Same for RR06
      if RR18 == None and check18: RR18 = 0.
      if RR06 == None and check06: RR06 = 0.

      # - Both observations available: use them
      if not RR18 == None and not RR06 == None:
         if RR18 < 0.: RR18 = 0.
         if RR06 < 0.: RR06 = 0.
         value = RR18 + RR06
         # Wetterturnier special: 0mm is -3.0
         if value == 0.: value = -30
      else:
         value = None
      # - Add value
      self.__add_obs_value__(what,stn.wmo,value)


   # ----------------------------------------------------------------
   # - Loading sunshine. 
   #   1) if 24h sum is available on 'sunday' on 06 UTC we will 
   #      take this value.
   #   2) if 06UTC sunday is not available but we have a sunday
   #      value at 00 UTC: take this one.
   #   3) else sum up the 'sun' 1h-rly obs. WARNING: seems that
   #      'none' is either 'no sun' or 'not reported'. I can't
   #      decide which one is which one at the moment. I just
   #      take none = 0 and sum up.
   # ----------------------------------------------------------------
   def prepare_fun_Sd(self,what,stn):

      # - If we have not loaded maxSd: stop
      if not stn.wmo in self.maxSd:
         sys.exit("ERROR: maximum sunshine duration for station %d unknown.\n" % stn.wmo + \
                  "Most possible reason: there is no entry for this station\n" + \
                  "in the table obs.stations and therefore I can't compute\n" + \
                  "the astronomic sunshine duration which is needed!")

      # - If we dont have any information about the maximum Sd we cant
      #   compute the relative value. In this case return False
      if not self.maxSd[stn.wmo]:
         value = None
      # - Else start processing the data
      else:
         # - Loading sunshine 24h sum, next day reported at 06UTC
         #   which is +30 hours from self.date.
         tmp = self.load_obs( stn.wmo, 30, 'sunday' )
         if tmp:
            value =int( np.round(np.float(tmp)/np.float(self.maxSd[stn.wmo]) * 100) ) * 10
         # - Loading sunshine 24h sum, next day reported at 00UTC
         #   which is +24 hours from self.date
         else:
            tmp = self.load_obs( stn.wmo, 24, 'sunday' )
            if tmp:
               Sd = int( np.round(np.float(tmp)/np.float(self.maxSd[stn.wmo]) * 100) ) * 10
               value = Sd 
            # - Else try to sum up hourly observations
            else:
               # - Else try to get the hourly sums.
               datum = int( self.date.strftime('%Y%m%d') )
               sql = "SELECT sun FROM %s WHERE statnr = %d AND " % (self.table,stn.wmo) + \
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
                  value = int( np.round(np.float(value)/np.float(self.maxSd[stn.wmo]) * 100) ) * 10

      # - Add value
      self.__add_obs_value__(what,stn.wmo,value)


   # ----------------------------------------------------------------
   # - Show loaded data
   # ----------------------------------------------------------------
   def show( self ):

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
      betdate = np.int( np.floor( np.float(self.date.strftime('%s')) / 86400. ) )

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

























