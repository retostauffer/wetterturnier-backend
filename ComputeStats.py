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

   from datetime import datetime as dt
   fmt = "%Y-%m-%d"
   #date = dt.fromtimestamp(tdate*86400).strftime(fmt)
   # - Loading all different cities (active cities)
   cities     = db.get_cities()
   # - If input city set, then drop all other cities.
   if not config['input_city'] == None:
      tmp = []
      for elem in cities:
         if elem['name'] == config['input_city']: tmp.append( elem )
      cities = tmp

   userIDs = db.get_all_users()

   measures=("points","points_adj","mean","median","max","min","sd","part")
   print str(measures)[1:-1]
  
   for userID in userIDs:
      user = db.get_username_by_id(userID)
      for city in cities:
         values=[]
         for measure in measures:
            values.append( db.get_stats(userID, city['ID'], measure) )
         db.upsert_stats( userID, city['ID'], measures, values )
  
   for city in cities:
      if config['input_alldates']:
         tdates = db.all_tournament_dates( city['ID'] )
         print 'ALL DATES'
      for tdate in tdates:
         values=[]
         for measure in measures[2:]:
            values.append(db.get_stats(0, city['ID'], measure, tdate))
         db.upsert_stats(0, city['ID'], measures[2:], values, tdate)

   db.commit()
   db.close()
