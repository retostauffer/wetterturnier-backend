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
   """
   MeteoService-GFS-MOS = MSwr-GFS-MOS
   GME-MOS = DWD-ICON-MOS
   DWD-MOS-Mix = DWD-EZGMEMOS
   """

   for i in users:
      userIDs.append( db.get_user_id(i) )
   #print users; userIDs

   measures=["points_adj_fit","points_adj_poly","points_adj_fit1","points_adj_fit2","points_adj_poly1","points_adj_poly2"]
   #measures=["points_adj_fit2"]

   #using -t option to quickly set asymptote ymax
   if config['input_tdate'] == None:
      ymax = 200
   else:
      ymax = config['input_tdate']

   #p option for testing minimum participations and exponent formula
   if config['input_param'] == None:
      par = [100,2]
   else:
      par = config['input_param'].split(",")

   mids = {1:2010, 2:2010, 3:2011, 4:2012, 5:2013}

   #calculate userstats only
   for userID in userIDs:
      user = db.get_username_by_id(userID)
      for city in cities:
         midyear = mids[city['ID']]

         stats = db.get_stats( city['ID'], measures, userID, 0, 0, ymax=ymax, pmin=int(par[0]), ex=int(par[1]), midyear=midyear, span=["2010-12-01","2012-04-30"] )
         db.upsert_stats( city['ID'], stats, userID, 0, 0 )
   
   sql = "SELECT wu.user_login, %s FROM %swetterturnier_userstats us JOIN wp_users wu ON userID = wu.ID WHERE cityID=%d AND userID IN%s ORDER BY points_adj_fit DESC LIMIT 0,80"
   cols = ",".join( measures )
 
   #generating ranking table output, write to .xls file
   with pd.ExcelWriter( "plots/test_list.xls" ) as writer:
      for city in cities:
	 sql = "SELECT wu.user_login, %s FROM %swetterturnier_userstats us JOIN wp_users wu ON userID = wu.ID WHERE cityID=%d AND userID IN%s ORDER BY points_adj_fit DESC LIMIT 0,80"
	 cols = ",".join( measures )
	 table = pd.read_sql_query( sql % ( cols, db.prefix, city['ID'], tuple(userIDs) ), db )
	 print table
         table.to_excel( writer, sheet_name=city["hash"] )

   db.commit()
   db.close()
