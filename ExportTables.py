from pywetterturnier import database, utils
import pandas as pd

inputs = utils.inputcheck('ExportTables')
# - Read configuration file
config = utils.readconfig('config.conf',inputs)
# - Initializing class and open database connection
db     = database.database(config)

cities = db.get_cities()

#sql = "SELECT wu.user_login, us.points_adj, %s FROM %swetterturnier_userstats us JOIN %susers wu ON userID = wu.ID WHERE cityID=%d AND max!=0 AND min!=0 and part >= 25 ORDER BY wu.user_login"

#sql="SELECT wu.user_login, bs.points, %s, REPLACE(wu.user_login, 'GRP_', '') FROM %swetterturnier_betstat bs JOIN %susers wu ON userID = wu.ID WHERE cityID=%d AND wu.user_login NOT LIKE 'Sleepy' ORDER BY tdate"

sql="SELECT wu.user_login, bs.points, %s FROM %swetterturnier_betstat bs JOIN %susers wu ON userID = wu.ID WHERE cityID=%d AND wu.user_login NOT LIKE 'Sleepy' ORDER BY tdate"

measures = ["tdate","rank"]
#measures = ["mean","median","Qlow","Qupp","max","min","sd","part"]
cols = ",".join( measures )

if config['input_filename'] == None:
   filename = "test"
else:
   filename = config['input_filename']

#generating ranking table output, write to .xls file
with pd.ExcelWriter( "plots/%s.xls" % filename ) as writer:
   for city in cities:
      table = pd.read_sql_query( sql % ( cols, db.prefix, db.prefix, city['ID'] ), db )
      table.to_excel( writer, sheet_name = city["hash"] )
