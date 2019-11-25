# -------------------------------------------------------------------
# - NAME:        ComputePoints.py
# - AUTHOR:      Reto Stauffer
# - DATE:        2014-09-21
# - LICENSE: GPL-3, Reto Stauffer, copyright 2014
# -------------------------------------------------------------------
# - DESCRIPTION: Compute points for all players. 
# -------------------------------------------------------------------
# - EDITORIAL:   2014-09-19, RS: Created file on thinkreto.
#                Adapted from ComputePetrus.py
# -------------------------------------------------------------------
# - L@ST MODIFIED: 2018-01-19 15:20 on marvin
# -------------------------------------------------------------------

import sys, os
sys.path.append('PyModules')


# - Start as main script (not as module)
if __name__ == '__main__':

   import numpy as np
   # - Wetterturnier specific modules
   from pywetterturnier import utils, database
   
   # - Evaluating input arguments
   inputs = utils.inputcheck('ComputePoints')
   # - Read configuration file
   config = utils.readconfig('config.conf',inputs)

   # - Initializing class and open database connection
   db        = database.database(config)
   # - Loading tdate (day since 1970-01-01) for the tournament.
   #   Normaly Friday-Tornament (tdate is then Friday) while
   #   the bet-dates are for Saturday and Sunday.
   if config['input_tdate'] == None:
      tdates     = [db.current_tournament()]
      print '  * Current tournament is %s' % utils.tdate2string( tdates[0] )
   else:
      tdates     = [config['input_tdate']]

   # - If input_user was given as string we have to find the
   #   corresponding userID first!
   if type(config['input_user']) == type(str()):
      config['input_user'] = db.get_user_id( config['input_user'] )
      if not config['input_user']:
         utils.exit('SORRY could not convert your input -u/--user to corresponding userID. Check name.')
   
   # - Loading all parameters
   params = db.get_parameter_names(False)

   # ----------------------------------------------------------------
   # - Because of the observations we have to compute the
   #   points city by city. Loading city data here first. 
   # ----------------------------------------------------------------
   # - Loading all different cities (active cities)
   cities     = db.get_cities()
   # - If input city set, then drop all other cities.
   if not config['input_city'] == None:
      tmp = []
      for elem in cities:
         if elem['name'] == config['input_city']: tmp.append( elem )
      cities = tmp

   # ----------------------------------------------------------------
   # - Now going over the cities and compute the points. 
   # ----------------------------------------------------------------
   for city in cities:

      # -------------------------------------------------------------
      # - If aldates, take all tdates from database
      # -------------------------------------------------------------
      if config['input_alldates']:
         tdates = db.all_tournament_dates( city['ID'] )

      # -------------------------------------------------------------
      # - Looping trough dates
      # -------------------------------------------------------------
      for tdate in tdates:

         # ----------------------------------------------------------------
         # - Check if we are allowed to perform the computation of the
         #   mean bets on this date
         # ----------------------------------------------------------------
         check = utils.datelock(config,tdate)
         if check:
            print '    Date is \'locked\' (datelock). Dont execute, skip.'
            continue

         print '  * Current tournament is %s' % utils.tdate2string( tdate )

         # ----------------------------------------------------------
         # - Avoid to change old points!
         # ----------------------------------------------------------
         if not config['input_force'] and tdate <= 17532:
            print "\n       SKIP SKIP SKIP SKIP SKIP SKIP SKIP SKIP"
            print "       |  do NOT change points before 2018   |"
            print "       SKIP SKIP SKIP SKIP SKIP SKIP SKIP SKIP\n"
            continue

         # ----------------------------------------------------------
         # - Which judgingclass do we have to take?
         #   It is possible that the scoring system changed.
         # ----------------------------------------------------------
         #   Take the latest judgingclass changed in 2002-12-06
         if tdate < 12027:
            if config['input_ignore']:
               print '[!] Judginglcass not defined - but started in ignore mode. Skip.'
               continue
            else:
               utils.exit('I dont know which judgingclass I should use for this date. Stop.')

         # ----------------------------------------------------------
         # - Dynamically loading judgingclass
         # ----------------------------------------------------------
         modname = "pywetterturnier.judgingclass%s" % config['judging_test']
         try:
            from importlib import import_module
            judging = import_module(modname)
         except Exception as e:
            print e
            utils.exit("Problems loading the judgingclass %s" % modname)

         jug = judging.judging()

         # ----------------------------------------------------------
         # - Looping over the forecast days
         # ----------------------------------------------------------
         for day in range(1,3):
   
            print '\n  * Compute points for city %s (ID: %d)' % (city['name'], city['ID'])
            print '    Bets for: %s' % utils.tdate2string( tdate + day )
   
            # -------------------------------------------------------
            # - Compute points
            # -------------------------------------------------------
            for param in params:

               if not config['input_param'] == None:
                  if not param == config['input_param']: continue
   
               paramID = db.get_parameter_id( param )
               print '    Compute points for %s (paramID: %d)' % (param, paramID)
   
               # - Gettig observations
               obs = db.get_obs_data(city['ID'],paramID,tdate,day)
               if not obs:
                  print '    Observations not available. Skip at that time.'
                  continue
   
               # - Loading city observations
               # - Loading the user bets
               nullonly = False
               tmp = db.get_cityall_bet_data(city['ID'],paramID,tdate,day,nullonly=nullonly)
               # Gotno data?
               if not tmp[0] or not tmp[1]:
                  print "[!] Got no data to compute the points. Skip"; continue
               db_userID, db_cityID, db_paramID, db_tdate, db_betdate, values = tmp
               # - No data: skip 
               if not values:
                  print '    Got no data for this parameter. Skip.'
                  continue
   
               # - If the parameter to judge is "dd" we need additional
               #   information about the observed wind speed! Take it here.
               if param == 'dd':
                  ffID = db.get_parameter_id( 'ff' )
                  special = db.get_obs_data(city['ID'],ffID,tdate,day)
               else:
                  special = None # unused
   
               # - Now compute points
               points = jug.get_points(obs,param,values,special,tdate)
   
               jug.points_to_database( db, db_userID, db_cityID, db_paramID, db_tdate, \
                                       db_betdate, points )


   # ----------------------------------------------------------------
   # - Now calling the function which computes the sum points
   #   filling in the betstat table.
   # ----------------------------------------------------------------
   import ComputeSumPoints
   ComputeSumPoints.CSP(db,config,cities,tdates)


   db.commit()
   db.close()







