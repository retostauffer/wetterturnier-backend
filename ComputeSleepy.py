# -------------------------------------------------------------------
# - NAME:        ComputeSleepy.py
# - AUTHOR:      Reto Stauffer
# - DATE:        2014-09-19
# - LICENSE: GPL-3, Reto Stauffer, copyright 2014
# -------------------------------------------------------------------
# - DESCRIPTION: Compute Sleepy. The Sleepy delivers the points
#                for all the players without bets.
#                The sleepy does not play on the wetterturnier.
#                Sleepy is not based on bets or daily points,
#                just on the 'total weekend points'.
#
#                The points the Sleepy gets is:
#                mean(points) - mean(abs(points - mean(points)))
#                ... and NOT mean minus standard deviation as
#                written on the old wetterturnier.de
# -------------------------------------------------------------------
# - EDITORIAL:   2014-09-13, RS: Created file on thinkreto.
# -------------------------------------------------------------------
# - L@ST MODIFIED: 2017-12-20 17:35 on prognose2
# -------------------------------------------------------------------



# - Start as main script (not as module)
if __name__ == '__main__':
   """
   ComputeSleepy: the sleepy is the player who contains
   points only - these are the points which will be applied
   to all users which did not join the tournament.
   Used by the ranking routines and stuff.
   """

   import sys, os
   import numpy as np
   # - Wetterturnier specific modules
   from pywetterturnier import utils
   from pywetterturnier import database

   # - Evaluating input arguments
   inputs = utils.inputcheck('ComputeSleepy')
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

   # - Loading all different cities (active cities)
   cities     = db.get_cities()
   # - If input city set, then drop all other cities.
   if not config['input_city'] == None:
      tmp = []
      for elem in cities:
         if elem['name'] == config['input_city']: tmp.append( elem )
      cities = tmp

   # ----------------------------------------------------------------
   # - Prepare the Sleepy
   # ----------------------------------------------------------------
   username = 'Sleepy'
   db.create_user( username )
   userID = db.get_user_id( username )
   print '    The userID of the sleepy is %d' % userID
   
   # ----------------------------------------------------------------
   # - Compute its sleepy, one for each city 
   # ----------------------------------------------------------------
   import numpy as np
   for city in cities:
   
      print '\n  * Compute the %s for city %s (ID: %d)' % (username,city['name'], city['ID']) 

      # ----------------------------------------------------------------
      # - If aldates, take all tdates from database
      # ----------------------------------------------------------------
      if config['input_alldates']:
         tdates = db.all_tournament_dates( city['ID'] )

      # ----------------------------------------------------------------
      # - Looping trough dates
      # ----------------------------------------------------------------
      for tdate in tdates:

         # - Returns list object containing two dicts 
         #   where all the bets are in.
         tmp = db.get_sleepy_points(city['ID'],tdate,userID)
         if tmp == False: continue

         # - Else prepare the data to compute the Sleepy poins
         data = []
         for elem in tmp:
            if elem[0] == None: continue
            data.append(float(elem[0]))   # store total points to a list

         if len(data) == 0: continue

         points    = np.round(np.mean(data)  - np.mean(np.abs(data  - np.mean(data ))),1)
 
         # - Insert Sleepy points
         print '    Inserting Sleepy points for %d' % tdate
         print "    UPSERT: user %d, city %d, tdate %d, points %f " % (userID,city['ID'],tdate,points)

         db.upsert_sleepy_points(userID,city['ID'],tdate,points)

   
   
   db.commit()
   db.close()
