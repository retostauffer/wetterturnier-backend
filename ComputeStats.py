# - Start as main script (not as module)
if __name__ == '__main__':

   import sys, os
   # - Wetterturnier specific methods
   from pywetterturnier import utils, database

   # - Evaluating input arguments
   inputs = utils.inputcheck('ComputeStats')
   print inputs
   # - Read configuration file
   config = utils.readconfig('config.conf',inputs)
   print config
   # - Initializing class and open database connection
   db        = database.database(config)

   # - Loading tdate (day since 1970-01-01) for the tournament.
   #   Normaly Friday-Tornament (tdate is then Friday) while
   #   the bet-dates are for Saturday and Sunday if there was
   #   no input tournament date -t/--tdate.
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

   userIDs = db.get_all_users()

   measures=("points","points_adj","mean","median","Qlow","Qupp","max","min","sd","part")
  
   for userID in userIDs:
      user = db.get_username_by_id(userID)
      for city in cities:
         for day in range(3):
            stats = db.get_stats(userID, city['ID'], measures, 0, day)
            db.upsert_stats( userID, city['ID'], stats, 0, day)
   #TODO Cumpute rank, rank_adj? 

   for city in cities:
      if config['input_alldates']:
         tdates = db.all_tournament_dates( city['ID'] )
         print 'ALL DATES'
      for tdate in tdates:
         for day in range(3):
            stats = db.get_stats(0, city['ID'], measures[2:], tdate, day)
            db.upsert_stats(0, city['ID'], stats, tdate, day)

   import PlotStats
   tdate = max(tdates) - 7
   PlotStats.plot(db, cities, tdate)

   db.commit()
   db.close()
