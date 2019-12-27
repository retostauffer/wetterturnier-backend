# - Start as main script (not as module)
if __name__ == '__main__':

   import sys, os
   import pandas as pd
   # - Wetterturnier specific methods
   from pywetterturnier import utils, database

   # - Evaluating input arguments
   inputs = utils.inputcheck('ComputeUserStats')


   # - Read configuration file
   config = utils.readconfig('config.conf',inputs)
   # - Initializing class and open database connection
   db        = database.database(config)


   # - Loading all different cities (active cities)
   cities     = db.get_cities()
   # - If input city set, then drop all other cities.
   if not config['input_city'] == None:
      tmp = []
      for elem in cities:
         if elem['name'] == config['input_city']: tmp.append( elem )
      cities = tmp

   #userIDs = db.get_all_users()
   userIDs = []
   #users = ["Moses","Petrus","Georg","Pfingstochse","Schneegewitter","Michi23","MOS-Mix"]
   users = ["Moses","Petrus","Georg","Meteomedia"]

   if config["input_users"]:
      #print config["input_users"]
      users = config["input_users"]
   
   elif config["input_user"]:
      #print config["input_users"]
      users = [config["input_user"]]

   #-s => compare multiple users
   for i in users:
      userIDs.append( db.get_user_id(i) )
   #print users; userIDs

   measures=["points_adj","points_adj1","points_adj2","part"]
   #measures=["part","points","mean","median","sd","max","min"]

   #-t option to quickly set asymptote ymax
   if config['input_tdate'] == None:
      ymax = 185
   else:
      ymax = config['input_tdate']

   #-p option for testing minimum participations and exponent formula
   if config['input_param'] == None:
      par = [1,1]
   else:
      par = config['input_param'].split(",")

   mids = {1:2010, 2:2010, 3:2011, 4:2012, 5:2013}

   #verbose switch for debugging
   if config["input_verbose"]:
      verbose = True
   else: verbose = False

   #-d to only calculate points_adj in a certain timespan (from,to)
   if config["input_dates"]:
      span = config["input_dates"]
   else: span = False

   #calculate userstats only
   for city in cities:
      print "city = " + city["hash"]
      midyear = mids[city['ID']]
      print "midyear = " + str(midyear) + "\n"
      if ymax == -1:
         sql = "SELECT max FROM %swetterturnier_citystats WHERE cityID = %d"
         cur = db.cursor()
         cur.execute( sql % ( db.prefix, city['ID'] ) )
         data = cur.fetchone()
         ymax = data[0]

      for userID in userIDs:
         user = db.get_username_by_id(userID)
         stats = db.compute_stats( city['ID'], measures, userID, 0, 0, ymax=ymax, pout=int(par[0]), pmin=int(par[1]), span=span, referenz=True, midyear=midyear, verbose=verbose )

         db.upsert_stats( city['ID'], stats, userID, 0, 0 )
   
   sql = "SELECT wu.user_login, %s FROM %swetterturnier_userstats us JOIN wp_users wu ON userID = wu.ID WHERE cityID=%d AND userID IN%s ORDER BY points_adj DESC LIMIT 0,50"
   cols = ",".join( measures )
 
   #generating ranking table output, write to .xls file
   with pd.ExcelWriter( "plots/test_list.xls" ) as writer:
      for city in cities:
         table = pd.read_sql_query( sql % ( cols, db.prefix, city['ID'], database.sql_tuple(userIDs) ), db )
         print table
         table.to_excel( writer, sheet_name=city["hash"] )

   db.commit()
   db.close()
