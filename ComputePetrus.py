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
# - L@ST MODIFIED: 2015-08-04 09:16 on prognose2.met.fu-berlin.de
# -------------------------------------------------------------------



# - Start as main script (not as module)
if __name__ == '__main__':

   import sys, os
   import numpy as np
   # - Wetterturnier specific modules
   from pywetterturnier import utils
   from pywetterturnier import database
   from pywetterturnier import mitteltip 

   # - Evaluating input arguments
   inputs = utils.inputcheck('ComputePetrus')
   # - Read configuration file
   config = utils.readconfig('config.conf',inputs)

   # - If input_user was given as string we have to find the
   #   corresponding userID first!
   if not config['input_user'] == None:
      print '[!] NOTE: got input -u/--user. Will be ignored in ComputePetrus.'
      config['input_user'] = None
   
   
   # - Initializing class and open database connection
   db        = database.database(config)
   # - Loading tdate (day since 1970-01-01) for the tournament.
   #   Normaly Friday-Tornament (tdate is then Friday) while
   #   the bet-dates are for Saturday and Sunday if there was
   #   no input tournament date -t/--tdate.
   if config['input_tdate'] == None:
      tdate      = db.current_tournament()
   else:
      tdate      = config['input_tdate']

   print '  * Current tournament is %s' % utils.tdate2string( tdate )
   # - Loading all different cities (active cities)
   cities     = db.get_cities()

   # ----------------------------------------------------------------
   # - Prepare the Petrus
   # ----------------------------------------------------------------
   username = 'Petrus'
   db.create_user( username )
   userID = db.get_user_id( username )
   
   # ----------------------------------------------------------------
   # - Compute its mitteltip, one for each station. 
   # ----------------------------------------------------------------
   for city in cities:
   
      print '\n  * Compute the %s for city %s (ID: %d)' % (username,city['name'], city['ID']) 
   
      # - Returns list object containing two dicts 
      #   where all the bets are in.
      bet = mitteltip.mitteltip(db,'all',False,city,tdate)
 
      # - If bet is False, continue
      if bet == False: continue
   
      # -------------------------------------------------------------
      # - Inserting into database now
      # -------------------------------------------------------------
      print '    Inserting data into database now'
      for day in range(1,3):
         for k in bet[day-1].keys():
            paramID = db.get_parameter_id(k)
            db.upsert_bet_data(userID,city['ID'],paramID,tdate,day,bet[day-1][k])
   
   db.close()
