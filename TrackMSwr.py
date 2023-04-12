def track(db, cities, tdate, verbose=False):
  
   def bdate2day( bdate ):
      """Helper function converting the betdate value from the database into human-readable weekday (Sat/Sun)"""
      day12 = bdate - tdate
      if day12 == 1:
         return "Sat"
      else:
         return "Sun"

   dayname = {1:"Sat", 2:"Sun"}

   from pywetterturnier import utils
   import pandas as pd
   import sys

   if tdate < utils.today_tdate():
      tdate -= 7

   cur = db.cursor()

   #generate files for MSwr forecast tracking (biggest differences from MOS every weekend)
   mswr  = ( "MOS-Mix","EZ-MOS","GFS-MOS" )
   mswr  = [ "MSwr-" + i for i in mswr    ]
   mosID = db.get_user_id( "GRP_MOS" )
   if verbose: print(mosID)
   sql = f"SELECT cityID,paramID,betdate,value,points FROM wp_wetterturnier_bets WHERE userID={mosID} AND tdate={tdate}"
   if verbose: print(sql)
   cur.execute(sql)
   res = cur.fetchall()
   if verbose: print(res)

   mosDF = pd.read_sql_query(sql, db)
   #mosV = mosDF.loc[(mosDF['cityID'] == 1) & (mosDF['paramID'] == 13)]
   #print(mosV); sys.exit()

   if verbose: print(mosDF)

   params = db.get_parameter_names(active=True, tdate=tdate)
   if verbose: print(params)

   out = pd.DataFrame({'MOS'       : pd.Series(dtype='str'),
                       'Diff(Val)' : pd.Series(dtype='float'),
                       'Diff(Pts)' : pd.Series(dtype='float'),
                       'Param'     : pd.Series(dtype='str'),
                       'City'      : pd.Series(dtype='str'),
                       'Day'       : pd.Series(dtype='str')})

   if verbose: print(out)

   for m in mswr:
      mswrID = db.get_user_id( m )
      if verbose: print(m)
      for c in cities:
         cname = c["name"]
         cityID = c["ID"]
         if verbose: print(cname)
         for p in params:
            if verbose: print(p)
            paramID = db.get_parameter_id(p)
            for d in range(1,3):
               bdate = tdate + d
               sql = f"SELECT value,points FROM wp_wetterturnier_bets WHERE userID={mswrID} AND betdate={bdate} AND paramID={paramID}"
               cur.execute(sql)
               res = cur.fetchall()[0]
               if verbose: print(res)
               mos = mosDF.loc[(mosDF['cityID'] == cityID) & (mosDF['paramID'] == paramID) & (mosDF['betdate'] == bdate)]
               if verbose: print(int(mos["value"] / 10), int(mos["points"]))
               if verbose: print(res[0], res[1])
               dV = (res[0] - int(mos["value"]))  / 10
               dP = (res[1] - int(mos["points"]))
               out = out.append({'MOS':m, 'Diff(Val)':dV, 'Diff(Pts)':dP, 'Param':p, 'City':cname, 'Day':dayname[d]}, ignore_index=True)

   if verbose: print(out)

   date_str = utils.tdate2string( tdate )
   if verbose: print(date_str)
   with pd.ExcelWriter( f"mswr/{date_str}.xls" ) as writer: out.to_excel( writer )

# - Start as main script (not as module)
# -------------------------------------------------------------------
if __name__ == '__main__':

   # - need to import the database
   from pywetterturnier import database, utils

   # - Evaluating input arguments
   inputs = utils.inputcheck('PlotStats')
   # - Read configuration file
   config = utils.readconfig('config.conf',inputs)

   # - Initializing class and open database connection
   db        = database.database(config)

   # ----------------------------------------------------------------
   # - Loading all different cities (active cities)
   cities     = db.get_cities()

   #TODO: only accepted input should be city!
   # - If input city set, then drop all other cities.
   if not config['input_city'] == None:
      tmp = []
      for i in cities:
         if i['name'] == config['input_city']: tmp.append( i )
      cities = tmp

   if config['input_verbose'] == None:
      verbose = False
   else: verbose = config['input_verbose']

   if config['input_tdate'] == None:
      tdate     = db.current_tournament()
      print('  * Current tournament is %s' % utils.tdate2string( tdate ))
   else:
      tdate = config['input_tdate']

   # - Calling the function now
   track(db, cities, tdate, verbose)

   db.commit()
   db.close()
