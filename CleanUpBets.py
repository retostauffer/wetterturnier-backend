# - Start as main script (not as module)
if __name__ == '__main__':

   import sys, os
   # - Wetterturnier specific modules
   from pywetterturnier import utils, database, mitteltip

   # - Evaluating input arguments
   inputs = utils.inputcheck('CleanBets')
   # - Read configuration file
   config = utils.readconfig('config.conf', inputs)

   # - If input_user was given as string we have to find the
   #   corresponding userID first!
   if not config['input_user'] == None:
      print('[!] NOTE: got input -u/--user. Will be ignored in CleanBets.')
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

   for city in cities:
      print("Now cleaning up bets in %s" % city['name'])
      # ----------------------------------------------------------------
      # - If alldates, take all tdates from database
      # ----------------------------------------------------------------
      if config['input_alldates']:
         tdates = db.all_tournament_dates( city['ID'] )
      for tdate in tdates:
         print(utils.tdate2string( tdate ))
         check = utils.datelock( config, tdate )
         if check:
            print("    Date is 'locked' (datelock). Dont execute.")
            continue
         missing = db.find_missing_bets( city['ID'], tdate )
         if missing == False:
            print("OK"); continue
         else:
            for userID in missing:
               db.delete_bet( userID, city['ID'], tdate )

   db.commit()
   db.close()

   print("Cleaning finished - GOOD NIGHT!")
