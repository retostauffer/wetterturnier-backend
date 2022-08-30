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
   from pywetterturnier import utils, database, mitteltip
   
   # - Evaluating input arguments
   inputs = utils.inputcheck('ComputePersistenzen')
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
      print(tdates)
   # - Loading all different cities (active cities)
   cities     = db.get_cities()
   # - If input city set, then drop all other cities.
   if not config['input_city'] == None:
      tmp = []
      for i in cities:
         if i['name'] == config['input_city']: tmp.append( i )
      cities = tmp


   for i,j in zip( ["Donnerstag","Freitag"], [1,0] ):
      print(i, j)
      # ----------------------------------------------------------------
      # - Prepare the Persistenz
      # ----------------------------------------------------------------
      username = i
      db.create_user( username )
      userID = db.get_user_id( username )

      # -------------------------------------------------------------
      # Remove boolean values from list
      # -------------------------------------------------------------
      def remove_bool_from_list( x ):
         res = []
         for i in x:
            if not isinstance(i, bool):
               res.append( elem )
         return res

      # ----------------------------------------------------------------
      # - Loopig over all tournament dates
      # ----------------------------------------------------------------
      from datetime import datetime as dt
      for tdate in tdates:

         # - Using obervations of the tournament day for our Persistenz player
         tdate_str = utils.tdate2string( tdate - j )

         print("    Searching for Observations:     %s (%d)" % (tdate_str, tdate-j))

         # ----------------------------------------------------------------
         # - Check if we are allowed to perform the computation of the
         #   mean bets on this date
         # ----------------------------------------------------------------
         check = utils.datelock(config,tdate-j)
         if check:
            print('    Date is \'locked\' (datelock). Dont execute, skip.')
            continue

         # ----------------------------------------------------------------
         # - Compute mitteltip mean of all stations of each city... 
         # ----------------------------------------------------------------
         for city in cities:
            print('\n  * Compute the %s for city %s (ID: %d)' % (username,city['name'], city['ID']))
            
            # - bit hacky: go 1 day back in mitteltip function to get obs
            #   instead of user bets like in Petrus. typ='persistenz' for db
            #   idea: we could also take thursday's obs for saturday and
            #   fridays tip for sunday, or even saturday's for sunday...
            bet = mitteltip.mitteltip( db, 'persistenz', False, city, tdate - j )
            print("bet:", bet) 
            # - If bet is False, continue
            if bet == False: continue
            
            # - Save into database. Note: we have loaded the persistence
            #   data from the tournament (e.g. Friday)
            #   but have to store for two days (saturday, sunday). Therefore
            #   there is the day-loop here.
            for day in range(1,3):
               print("    Insert Persistenz bets into database for day %d" % day)
               for k in list(bet[day-1].keys()):
                  paramID = db.get_parameter_id(k)
                  db.upsert_bet_data(userID,city['ID'],paramID,tdate,day,bet[day-1][k])

   
   # - Close database
   db.commit()
   db.close()
