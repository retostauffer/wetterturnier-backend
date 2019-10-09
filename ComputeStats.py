# - Start as main script (not as module)
if __name__ == '__main__':

   import sys, os
   import pandas as pd
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

   measures=["points","points_adj","points_adj_med","points_adj_fit","points_adj_mean","part","mean","median","Qlow","Qupp","max","min","sd"]
 

   for city in cities:
      if config['input_alldates']:
         tdates = db.all_tournament_dates( city['ID'] )
         print 'ALL DATES'
      for tdate in tdates:
         for day in range(3):
            stats = db.get_stats( city['ID'], measures[5:], 0, tdate, day)
            db.upsert_stats( city['ID'], stats, 0, tdate, day)
      
      #Compute citystats which can be used for plotting box whiskers etc
      #TODO: we could already calculate the fit coefficients A,B,C later used for plotting here
      stats = db.get_stats( city['ID'], measures[-7:] + ["mean_part","max_part","min_part","tdates"] )
      db.upsert_stats( city['ID'], stats )

   # check whether current tournament is finished to keep open tournaments out of the userstats
   today              = utils.today_tdate()
   current_tnmt       = db.current_tournament()
   if today > current_tnmt + 2:
      last_tdate = current_tnmt
   else:
      last_tdate = current_tnmt - 7
   
   for userID in userIDs:
      user = db.get_username_by_id(userID)
      for city in cities:
         for day in range(3):
            stats = db.get_stats( city['ID'], measures, userID, 0, day, last_tdate)
            db.upsert_stats( city['ID'], stats, userID, 0, day)
   
   #generating ranking table output, write to .xls file
   with pd.ExcelWriter( "plots/eternal_list.xls" ) as writer:
      for city in cities:
         sql = "SELECT wu.user_login, us.points %s FROM %swetterturnier_userstats us JOIN wp_users wu ON userID = wu.ID WHERE cityID=%d ORDER BY points_adj_mean DESC LIMIT 0,100"
	 cols = ",".join( measures[:6] )
	 table = pd.read_sql_query( sql % ( cols, db.prefix, city['ID'] ), db )
         table.to_excel( writer, sheet_name = city["hash"] )


   import PlotStats
   tdate = max(tdates) - 7
   PlotStats.plot(db, cities, tdate)

   db.commit()
   db.close()
