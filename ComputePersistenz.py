# -------------------------------------------------------------------
# - NAME:        ComputePersistenz.py
# - AUTHOR:      Reto Stauffer
# - DATE:        2015-07-29
# - LICENSE: GPL-3, Reto Stauffer, copyright 2014
# -------------------------------------------------------------------
# - DESCRIPTION: Computes Peristenz for the tournament. Therefore
#                using wp_wetterturnier_obs, the entries for one
#                day before the actual tournament (e.g., tournament
#                is on friday, take tursday obs). 
# -------------------------------------------------------------------
# - EDITORIAL:   2015-07-29, RS: Adapted from ComputeMoses.py
# -------------------------------------------------------------------
# - L@ST MODIFIED: 2018-01-20 13:15 on prognose2
# -------------------------------------------------------------------



# - Start as main script (not as module)
if __name__ == '__main__':

   import sys, os
   import numpy as np
   from glob import glob
   # - Wetterturnier specific methods
   from pywetterturnier import utils
   from pywetterturnier import database
   
   # - Evaluating input arguments
   inputs = utils.inputcheck('ComputePetrus')
   # - Read configuration file
   config = utils.readconfig('config.conf',inputs)
   
   # - Initializing class and open database connection
   db        = database.database(config)
   # - Loading tdate (day since 1970-01-01) for the tournament.
   #   Normaly Friday-Tornament (tdate is then Friday) while
   #   the bet-dates are for Saturday and Sunday if there was
   #   no input tournament date -t/--tdate.
   if config['input_tdate'] == None:
      tdates     = [db.current_tournament()]
   else:
      tdates     = [config['input_tdate']]

   # - Loading all different cities (active cities)
   cities     = db.get_cities()
   # - If input city set, then drop all other cities.
   if not config['input_city'] == None:
      tmp = []
      for elem in cities:
         if elem['name'] == config['input_city']: tmp.append( elem )
      cities = tmp

   # - Reading parameter list
   params = db.get_parameter_names(False)

   # ----------------------------------------------------------------
   # - Prepare the Moses
   # ----------------------------------------------------------------
   username = 'Persistenz'
   db.create_user( username )
   userID = db.get_user_id( username )

   # -------------------------------------------------------------
   # Remove boolean values from list
   # -------------------------------------------------------------
   def remove_bool_from_list( x ):
      res = []
      for elem in x:
         if not isinstance(elem,bool):
            res.append( elem )
      return res

   # ----------------------------------------------------------------
   # - Loopig over all tournament dates
   # ----------------------------------------------------------------
   from datetime import datetime as dt
   for tdate in tdates:

      # - Using obervations the day before for our Persistenz player
      tdate_str = dt.fromtimestamp( tdate * 86400 ).strftime('%a, %Y-%m-%d')
      bdate_str = dt.fromtimestamp( (tdate-1) * 86400 ).strftime('%a, %Y-%m-%d')
      bdate     = tdate - 1

      print "  * Tournament date to process now: %s (%d)" % (tdate_str,tdate)
      print "    Searching for Observations:     %s (%d)" % (bdate_str,bdate)

      # ----------------------------------------------------------------
      # - Check if we are allowed to perform the computation of the
      #   mean bets on this date
      # ----------------------------------------------------------------
      check = utils.datelock(config,tdate)
      if check:
         print '    Date is \'locked\' (datelock). Dont execute, skip.'
         continue

      # ----------------------------------------------------------------
      # - Compute its mitteltip, one for each station. 
      # ----------------------------------------------------------------
      res = {} # Results dict
      for city in cities:
      
         print '\n  * Compute the %s for city %s (ID: %d)' % (username,city['name'], city['ID']) 

         # -------------------------------------------------------------
         # - Looping over all parameters, search for Moses coefficients
         #   and try to find the bets of the users.
         # -------------------------------------------------------------
         for param in params:

            print '    - Searching Persistenz parameter %s' % param
            # - Loading parameter ID
            paramID = db.get_parameter_id( param )
            res[param] = []

            # -------------------------------------------------------------
            # - Looping over all defined stations
            # -------------------------------------------------------------
            for stn in db.get_stations_for_city( city['ID'] ):

               # - If parameter is/was not active: ignore
               if not paramID in stn.getActiveParams( tdate ):
                  print "    Parameter %s is/was not an active parmaeter for station %d: ignore" % (param,stn.wmo)
                  continue

               # - The results dict, needed later
               val = db.get_obs_data(city['ID'],paramID,tdate,-1,stn.wmo)
               if isinstance(val,bool): continue

               res[param].append( val )

            #res[param] = remove_bool_from_list( res[param] )


         # -------------------------------------------------------------
         # - Make mean
         # -------------------------------------------------------------
         def mean(x):
            counter = 0
            value   = 0
            for elem in x:
               if elem == None or type(elem) == type(bool()): continue
               value   += elem
               counter += 1
            if not counter: return( None )
            return float(value) / float(counter)

         # -------------------------------------------------------------
         # - Inserting into database now
         # -------------------------------------------------------------
         import numpy as np
         print '    Inserting data into database now'
         bet = {}
         for param in res.keys(): 

            # - No data?
            if len(res[param]) == 0: continue

            # -------------------------------------------------------
            # - take arithmetic mean value for: N, Sd, ff, PPP, TTm, TTn, TTd
            # -------------------------------------------------------
            if len(res[param]) == 0:
               bet[param] = None
            elif param in ['N','ff','Sd']:
               bet[param] = np.int(np.round( mean( res[param] ) / 10. )) * 10
            elif param in ['PPP','TTm','TTn','TTd']:
               bet[param] = np.int(np.round( mean(res[param]) ))

            # -------------------------------------------------------
            # - ffx: decide gust or no gust
            #   if half have no gusts: no gusts
            #   if gusts, take arithmetic mean.
            # -------------------------------------------------------
            elif param in ['fx']:
               data = np.asarray(res[param])
               # - If all false I have to expect that there was no
               #   gust observation and therefore fx = 0!
               if np.all(data == False):
                  bet[param] = 0
               elif np.sum( data <= 0 ) >= np.sum( data > 0 ):
                  bet[param] = 0
               else:
                  bet[param] = np.int(np.round( np.mean( data[data>0] ) / 10. )) * 10

            # -------------------------------------------------------
            # - RR: decide precipitation or not 
            #   if half have no precipitation: no precipitation 
            #   else arithmetic mean of precipitation
            # -------------------------------------------------------
            elif param in ['RR']:
               data = np.asarray(res[param])
               # - If all false I have to expect that there was no
               #   precipitation and therefore RR = 0!
               if np.all(data == False):
                  bet[param] = -30
               elif np.sum( data < 0 ) >= np.sum( data >= 0 ):
                  bet[param] = -30
               else:
                  bet[param] = np.int(np.round( np.mean( data[data>=0] ) ))

            # -------------------------------------------------------
            # - Wv/Wn
            # -------------------------------------------------------
            elif param in ['Wv','Wn']:
               data = np.asarray(res[param]) / 10
               # - More for 0/4 than for 5/6/7/8/9:
               if np.sum( data < 5 ) > np.sum( data >= 5 ):
                  data = data[data < 5]
                  if np.sum( data == 0 ) > np.sum( data == 4 ):
                     bet[param] = 0
                  else:
                     bet[param] = 40
               # - Else there were more 5/6/7/8 values.
               else:
                  data = data[data >= 5]
                  print data
                  # - More stratiform 
                  if np.sum( data <= 7 ) > np.sum( data > 7 ):
                     data = data[data <= 7]
                     # - More liquid
                     if np.sum( data < 7 ) > np.sum( data == 7 ):
                        data = data[data < 7]
                        if np.sum( data == 5 ) > np.sum( data == 6 ):
                           bet[param] = 50
                        else:
                           bet[param] = 60
                     # - More solid gives 7
                     else:
                        bet[param] = 70 
                     
                  # - More convective
                  else:
                     data = data[data > 7]
                     if np.sum( data == 8 ) > np.sum( data == 9 ):
                        bet[param] = 80
                     else:
                        bet[param] = 90

            # -------------------------------------------------------
            # - dd: vector mean
            # -------------------------------------------------------
            elif param in ['dd']:

               data = np.asarray(res[param])
               data = data/10.; u = 0; v = 0
               for elem in data:
                  u = u + np.sin( elem * np.pi / 180. )
                  v = v + np.cos( elem * np.pi / 180. )
               u = u/np.float(len(data))
               v = v/np.float(len(data))
               val = np.int( np.round( np.arctan2(u,v) * 1800. / np.pi, -2 ) )
               # - Correct for outside [0-360[
               if val <= 0:      val = val + 3600
               elif val > 3600:  val = val - 3600
               # - Store
               bet[param] = val

            # - Else warning and skip
            else:
               print "[!] Persistenz player: no rule for parameter %s. Skip." % param
               continue


         # - Save into database. Note: we have loaded the persistence
         #   dat from day -1 (e.g., thuesday if tournament is friday)
         #   but have to store for two days (saturday, sunday). Therefore
         #   there is the day-loop here.
         for day in range(1,3):
            print "    Insert Persistenz bets into database for day %d" % day
            for param in bet.keys():
               paramID = db.get_parameter_id( param )
               #print              userID,city['ID'],paramID,tdate,day,bet[param]
               if bet[param] is None:
                  print "    - user %4d, city %2d, tdate %d, parameter %-6s %8s" % \
                             (userID,city['ID'],tdate,"%s:" % param,'None')
               else:
                  print "    - user %4d, city %2d, tdate %d, parameter %-6s %8d" % \
                             (userID,city['ID'],tdate,"%s:" % param,bet[param])
                  db.upsert_bet_data(userID,city['ID'],paramID,tdate,day,bet[param])

   
   # - Close database
   db.commit()
   db.close()
