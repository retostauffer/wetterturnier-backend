# - Start as main script (not as module)
if __name__ == '__main__':

   import sys, os
   import pandas as pd
   # - Wetterturnier specific methods
   from pywetterturnier import utils, database

   # - Evaluating input arguments
   inputs = utils.inputcheck('ComputeStats')
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
      print '  * Current tournament is %s' % utils.tdate2string( tdates[0] )
   else:
      tdates     = [config['input_tdate']]

   #verbose switch for debugging
   if config["input_verbose"]:
      verbose = True
   else: verbose = False

   #-p option for testing sigmoid function, setting midpoint where y=0.5
   if config['input_param'] == None:
      par = [50, 0.05] #pmid, k
   else:
      par = config['input_param'].split(",")

   # - Loading all different cities (active cities)
   cities     = db.get_cities()
   # - If input city set, then drop all other cities.
   if not config['input_city'] == None:
      tmp = []
      for elem in cities:
         if elem['name'] == config['input_city']: tmp.append( elem )
      cities = tmp

   userIDs = db.get_all_users()

   measures=["sd_ind","points_adj","points","part","mean","median","Qlow","Qupp","max","min","sd"]

   # check whether current tournament is finished to keep open tournaments out of the userstats
   today              = utils.today_tdate()
   current            = db.current_tournament()
   if today > current + 2:
      last_tdate = current
   else:
      if len(tdates) == 1 and tdates[0] == current: tdates = [current - 7]
      elif current in tdates: tdates.remove( current )
      last_tdate = current - 7


   #calculate tdatestats
   for city in cities:
      if config['input_alldates']:
         tdates = db.all_tournament_dates( city['ID'] )
         print 'ALL DATES'
      for tdate in tdates:
         for day in range(3):
            stats = db.compute_stats( city['ID'], measures[-8:]+["sd_upp"], 0, tdate, day )
            #if all stats are 0 we assume that no tournament took place on tdate
            if stats.values() == [0] * len(stats):
               continue
            else:
               db.upsert_stats( city['ID'], stats, 0, tdate, day)
      
      #Compute citystats which can be used for plotting box whiskers etc
      #TODO: we should already calculate the fit coefficients m,n / A,B,C later used for plotting here
      stats = db.compute_stats( city['ID'], measures[-7:] + ["mean_part","max_part","min_part","tdates"], last_tdate = last_tdate )
      db.upsert_stats( city['ID'], stats )

   if config['input_tdate'] == None:

      #append pseudo-city for all cities ranking
      cities.append( {"name":"all_cities", "hash":"ALL", "ID":0} )
      cities.append( {"name":"all_cities_weighted","hash":"ALW","ID":6} )

      #calculate userstats, first import aliases.json as dict
      from json import load
      with open("aliases.json") as aliases:
         aliases = load( aliases )
      for userID in userIDs:
	 user = db.get_username_by_id(userID)
	 for city in cities:
	    for day in range(3):
	       stats = db.compute_stats( city['ID'], measures, userID, 0, day, last_tdate, aliases=aliases, pout=50, pmid=int(par[0]), x0=float(par[1]) )
               db.upsert_stats( city['ID'], stats, userID, 0, day )

      sql = """
         SELECT wu.user_login, %s
         FROM %swetterturnier_userstats us
         JOIN wp_users wu ON userID = wu.ID
         WHERE cityID=%d AND user_login NOT LIKE 'Sleepy'
         AND part >= 50
         ORDER BY points_adj DESC
      """

      cols = ",".join( ("ROUND(points_adj, 1) AS points_adj", "ROUND(sd_ind, 1) AS sd_ind", "part") )
 
      if config['input_filename'] == None:
         filename = "eternal_list"
      else:
         filename = config['input_filename']

      #generating ranking table output, write to .xls file
      with pd.ExcelWriter( "plots/%s.xls" % filename ) as writer:
         for city in cities:
            print city["hash"]
            table = pd.read_sql_query( sql % ( cols, db.prefix, city['ID'] ), db )
            print table
            table.to_excel( writer, sheet_name = city["hash"] )

      #now we call a plotting routine which draws some nice statistical plots
      import PlotStats
      tdate = max(tdates) - 7
      print "Calling plot routine now..."
      PlotStats.plot(db, cities[:-2], tdate, verbose=False)

   db.commit()
   db.close()
