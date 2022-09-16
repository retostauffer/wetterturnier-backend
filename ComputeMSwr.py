# -------------------------------------------------------------------
# - NAME:        ComputePetrus.py
# - AUTHOR:      Reto Stauffer
# - DATE:        2014-09-19
# - LICENSE: GPL-3, Reto Stauffer, copyright 2014
# -------------------------------------------------------------------
# - DESCRIPTION: Compute Petrus for the next tournament date.
#                Can be started several times. 
# -------------------------------------------------------------------
# - EDITORIAL:   2014-09-13, RS: Created file on thinkreto.
# -------------------------------------------------------------------
# - L@ST MODIFIED: 2018-01-07 14:45 on marvin
# -------------------------------------------------------------------



# - Start as main script (not as module)
if __name__ == '__main__':

   import sys, os
   import numpy as np
   # - Wetterturnier specific modules
   from pywetterturnier import utils, database, mitteltip 

   # - Evaluating input arguments
   inputs = utils.inputcheck('ComputeMSwr')
   # - Read configuration file
   config = utils.readconfig('config.conf',inputs)

   # - If input_user was given as string we have to find the
   #   corresponding userID first!
   if not config['input_user'] == None:
      print('[!] NOTE: got input -u/--user. Will be ignored.')
      config['input_user'] = None
   
   
   # - Initializing class and open database connection
   db        = database.database(config)
   # - Loading tdate (day since 1970-01-01) for the tournament.
   #   Normaly Friday-Tornament (tdate is then Friday) while
   #   the bet-dates are for Saturday and Sunday if there was
   #   no input tournament date -t/--tdate.
   if config['input_tdate'] == None:
      tdates      = [db.current_tournament()]
   else:
      tdates      = [config['input_tdate']]

   print('  * Current tournament is %s' % utils.tdate2string( tdates[0] ))
   # - Loading all different cities (active cities)
   cities     = db.get_cities()
   # - If input city set, then drop all other cities.
   if not config['input_city'] == None:
      tmp = []
      for i in cities:
         if i['name'] == config['input_city']: tmp.append( i )
      cities = tmp


   # ----------------------------------------------------------------
   # - Prepare the Petrus
   # ----------------------------------------------------------------
   username = 'MSwr-MOS-Mix'
   db.create_user( username )
   userID = db.get_user_id( username )
   
   # ----------------------------------------------------------------
   # - Compute its mitteltip, one for each station. 
   # ----------------------------------------------------------------
   for city in cities:
   
      print('\n  * Compute the %s for city %s (ID: %d)' % (username,city['name'], city['ID'])) 

      if config['input_alldates']:
         tdates = db.all_tournament_dates( city['ID'] )

      # ----------------------------------------------------------------
      # - Looping trough dates
      # ----------------------------------------------------------------
      for tdate in tdates:

         # ----------------------------------------------------------------
         # - Check if we are allowed to perform the computation of the
         #   mean bets on this date
         # ----------------------------------------------------------------
         check = utils.datelock(config,tdate)
         if check:
            print('    Date is \'locked\' (datelock). Dont execute, skip.')
            continue

	 # ----------------------------------------------------------------
	 # - I do not have the judgingclass before the rule changes in
	 #   2002 (2002-12-06) and therefore it does not make any sense
	 #   to compute MeanBets for that time period (becuase we can
	 #   never compute the corresponding points). Skip. 
	 # ----------------------------------------------------------------
         if tdate < 12027:
            print('[!] I dont know the rules to compute points before 2002-12-06')
            print('    Therefore it makes no sense to compute MeanBets. Skip.')
            continue
 
         # - Returns list object containing two dicts 
         #   where all the bets are in.
         bet = mitteltip.mswr(db,'mswr',False,city,tdate)
 
         # - If bet is False, continue
         if bet == False: continue
   
         # -------------------------------------------------------------
         # - Inserting into database now
         # -------------------------------------------------------------
         print('    Inserting data into database now')
         for day in range(1,3):
            for k in list(bet[day-1].keys()):
               paramID = db.get_parameter_id(k)
               db.upsert_bet_data(userID,city['ID'],paramID,tdate,day,bet[day-1][k])
   
   db.commit()
   db.close()
