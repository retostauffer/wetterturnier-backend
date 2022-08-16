# -------------------------------------------------------------------
# - NAME:        Observations.py 
# - AUTHOR:      Reto Stauffer
# - DATE:        2015-07-21
# - LICENSE: GPL-3, Reto Stauffer, copyright 2014
# -------------------------------------------------------------------
# - DESCRIPTION: Loading observations from the 'raw' database and
#                insert the necessary values into the wetterturnier
#                observation table (wetterturnier_obs) which will
#                be used to compute the points.
# -------------------------------------------------------------------
# - EDITORIAL:   2015-07-23, RS: Created file on thinkreto.
# -------------------------------------------------------------------
# - L@ST MODIFIED: 2018-02-03 09:20 on marvin
# -------------------------------------------------------------------


# - Start as main script (not as module)
if __name__ == '__main__':

   import numpy as np
   import sys, os
   # - Wetterturnier specific modules
   from pywetterturnier import utils, database, getobs

   os.environ['TZ'] = 'UTC' # Important!
   
   # - Evaluating input arguments
   inputs = utils.inputcheck('Observations')
   # - Read configuration file
   config = utils.readconfig('config.conf',inputs)

   # - Reading WMO WW conversion file
   wmoww = utils.wmowwConversion( "wmo_ww.conf" )
   wmoww.show()

   # - Initializing class and open database connection
   db        = database.database(config)
   # - Loading tdate (day since 1970-01-01) for the tournament.
   #   Normaly Friday-Tornament (tdate is then Friday) while
   #   the bet-dates are for Saturday and Sunday.
   if config['input_tdate'] == None:
      tdates     = [db.current_tournament()]
      print('  * Current tournament is %s' % utils.tdate2string( tdates[0] ))
   else:
      tdates     = [config['input_tdate']]

   # - Loading all parameters
   params = db.get_parameter_names(active=True, sort=True, tdate=tdates[0])
   #params = ("TTm","TTn","TT12","TTd","dd","FF","FX","PPP","Sd","Sd12","RRm","RRt")
   #print(params)

   # ----------------------------------------------------------------
   # - Because of the observations we have to compute the
   #   points city by city. Loading city data here first. 
   # ----------------------------------------------------------------
   # - Loading all different cities (active cities)
   cities     = db.get_cities()
   # - If input city set, then drop all other cities.
   if not config['input_city'] == None:
      tmp = []
      for i in cities:
         if i['name'] == config['input_city']: tmp.append( i )
      cities = tmp

   # ----------------------------------------------------------------
   # - Create dates. Days since 1970. And I am going back in
   #   time ndays days.
   # ----------------------------------------------------------------
   ndays = 3
   
   import datetime as dt
   #today = int(dt.datetime.now().strftime('%s'))/86400
   #today = dt.datetime.fromtimestamp( today * 86400 )
   for tdate in tdates:

      tdate_int = tdate
      tdate = dt.datetime.fromtimestamp( tdate * 86400 )
      print("    Processing data for tournament: %s (tdate=%d)" % (tdate, tdate_int))

      # ----------------------------------------------------------------
      # - Now going over the cities and compute the points. 
      # ----------------------------------------------------------------
      for city in cities:

         print("\n  * Observations for station %s" % city['name'])

         # ----------------------------------------------------------------
         # - Looping trough tournament/bet dates.
         #   Note that 'tdate' is the tournament date (e.g., friday)
         #   and we need the observations for the day before (therefore
         #   starting the range at -1) for the persistence user,
         #   plus two days. Actually the day of the tournament would not
         #   be necessary, processing it just in case we need it somewhere.
         # ----------------------------------------------------------------
         for day in range(-1,ndays):

            date = tdate + dt.timedelta( day )
            print("\n  * Processing observations for day: %s\n" % date)

            obs = getobs.getobs(config, db, city, date, wmoww )

            #TODO get active parameters (SINCE/UNTIL columns) and loop over them

            for p in params:
               obs.prepare(p)

            """
            #OLD PARAMETERS:
            # - Temperatures
            obs.prepare('TTm') #,special='T today 06:00 to today 18:00')
            obs.prepare('TTn') #,special='T yesterday 18:00 to today 6:00 ')
            obs.prepare('TTd')
            # - Wind speed and direction
            obs.prepare('dd')
            obs.prepare('ff')
            obs.prepare('fx')
            # - Mean sea level Pressure
            obs.prepare('PPP')
            # - Cloud cover
            obs.prepare('N')
            # - Significant weather
            obs.prepare('Wv')
            obs.prepare('Wn')
            # - Precipitation
            obs.prepare('RR')
            # - Sunshine
            obs.prepare('Sd')
            """

            obs.show()
            obs.write_to_db()

   db.close()
