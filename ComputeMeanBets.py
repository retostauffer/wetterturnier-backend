# -------------------------------------------------------------------
# - NAME:        ComputeMeanBets.py
# - AUTHOR:      Reto Stauffer
# - DATE:        2014-09-19
# - LICENSE: GPL-3, Reto Stauffer, copyright 2014
# -------------------------------------------------------------------
# - DESCRIPTION: Compute Mitteltips for groups. 
# -------------------------------------------------------------------
# - EDITORIAL:   2014-09-13, RS: Created file on thinkreto.
# -------------------------------------------------------------------
# - L@ST MODIFIED: 2017-06-25 13:40 on thinkreto
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
   inputs = utils.inputcheck('ComputeMeanBets')
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

   # - Loading all active users from the database
   active_groups = db.get_active_groups()

   # - Checking input user if set
   #   If input_user was given as string we have to find the
   #   corresponding userID first!
   if type(config['input_user']) == type(int()):
      config['input_user'] = db.get_username_by_id( config['input_user'] )
      if not config['input_user']:
         utils.exit('SORRY could not convert your input -u/--user to corresponding username. Check name.')

   # - Check if input_user is an active group.
   if not config['input_user'] == None:
      if not config['input_user'] in active_groups:
         print '    Some help for you: currently active groups:'
         for grp in active_groups:
            print '    - %s' % grp
         utils.exit('Sorry, but %s is not a name of an active group. Stop.' % config['input_user'])
      else:
         active_groups = [config['input_user']]

   # - Create new user
   for group in active_groups:

      # - Each group has its own user which is
      #   GRP_<grupname>. Check if exists or create.
      username = 'GRP_%s' % group
      db.create_user( username )
      userID = db.get_user_id( username )
      groupID = db.get_group_id( group )

      # - Getting users for the groups
      for city in cities:

         print '\n  * Compute the %s (groupID %d) for city %s (ID: %d)' % \
                   (username,groupID,city['name'], city['ID']) 

         # ----------------------------------------------------------------
         # - If aldates, take all tdates from database
         # ----------------------------------------------------------------
         if config['input_alldates']:
            tdates = db.all_tournament_dates( city['ID'] )

         # ----------------------------------------------------------------
         # - Looping trough dates
         # ----------------------------------------------------------------
         for tdate in tdates:

            print '    Current tdate is: %d' % tdate

            # ----------------------------------------------------------------
            # - I do not have the judgingclass before the rule changes in
            #   2002 (2002-12-06) and therefore it does not make any sense
            #   to compute MeanBets for that time period (becuase we can
            #   never compute the corresponding points). Skip. 
            # ----------------------------------------------------------------
            if tdate < 12027:
               from judgingclass20021206 import judging
               print '[!] I dont know the rules to compute points before 2002-12-06'
               print '    Therefore it makes no sense to compute MeanBets. Skip.' 
               continue
         
            # -------------------------------------------------------------
            # - List element to store the two dict dbects
            #   containing the bets for Petrus
            # -------------------------------------------------------------
            bet = mitteltip.mitteltip(db,'group',groupID,city,tdate)
   
   
            # -------------------------------------------------------------
            # - If at least one query returnd no data, mitteltip returns
            #   False. We cannot compute the Mitteltip. Message and
            #   continue.
            # -------------------------------------------------------------
            if not bet:
               print '[!] At least one parameter returned no data. Skip!!'
               continue
   
   
            # -------------------------------------------------------------
            # - Inserting into database now
            # -------------------------------------------------------------
            print '    Inserting data into database now'
            for day in range(1,3):
               for k in bet[day-1].keys():
                  paramID = db.get_parameter_id(k)
                  db.upsert_bet_data(userID,city['ID'],paramID,tdate,day,bet[day-1][k])
   
   db.close()
