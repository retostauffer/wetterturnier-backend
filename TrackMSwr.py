def track(db, cities, tdate, config, verbose=False):
  
   def bdate2day( bdate ):
      """Helper function converting the betdate value from the database into human-readable weekday (Sat/Sun)"""
      day12 = bdate - tdate
      if day12 == 1:
         return "Sat"
      else:
         return "Sun"

   dayname = {1:"Sat", 2:"Sun"}

   from pywetterturnier import utils
   import sys
   sys.path.append('PyModules')
   # ----------------------------------------------------------
   # - Dynamically loading judgingclass
   # ----------------------------------------------------------

   # TODO: replace quick and dirty with automatic recognition of newest judgingclass

   if tdate <= 19200:
      judgingdate = config["judging_old"]
   else:
      judgingdate = config["judging_operational"]
   modname = f"pywetterturnier.judgingclass{judgingdate}"
   try:
      from importlib import import_module
      judging = import_module(modname)
   except Exception as e:
      print(e)
      utils.exit("Problems loading the judgingclass %s" % modname)

   jug = judging.judging()
   
   import pandas as pd
   import numpy as np
   from datetime import date

   #if tdate < utils.today_tdate():
   #   tdate -= 7

   cur = db.cursor()

   #generate files for MSwr forecast tracking (biggest differences from MOS every weekend)
   mswr  = ( "MOS-Mix","EZ-MOS","GFS-MOS" )
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
                       'Diff(Obs)' : pd.Series(dtype='float'),
                       'Param'     : pd.Series(dtype='str'),
                       'City'      : pd.Series(dtype='str'),
                       'Day'       : pd.Series(dtype='str')})

   if verbose: print(out)

   # - For the parameter to judge is "dd/dd12" we need additional
   #   information about the observed wind speed! Take it here.
   ffID = db.get_parameter_id( "dd12" )
   special = ()

   for m in mswr:
      mswrID = db.get_user_id( "MSwr-" + m )
      if verbose: print(m)
      for c in cities:
         cname = c["name"]
         cityID = c["ID"]
         if verbose: print(cname)
         for p in params:
            if verbose: print(p)
            paramID = db.get_parameter_id(p)

            if "Sd" in p or "RR" in p:
               pmax = 8
            else: pmax = 7

            for d in range(1,3):
               bdate = tdate + d
               sql = f"SELECT value,points FROM wp_wetterturnier_bets WHERE userID={mswrID} AND betdate={bdate} AND paramID={paramID} AND cityID={cityID}"
               cur.execute(sql)
               try: res = cur.fetchall()[0]
               except: sys.exit()
               if verbose: print(res)
               mos = mosDF.loc[(mosDF['cityID'] == cityID) & (mosDF['paramID'] == paramID) & (mosDF['betdate'] == bdate)]
               val = res[0] / 10
               
               mos_val    = int(mos["value"]) / 10
               try:
                  mos_points = float(mos["points"])
               except TypeError:
                  mos_points = 0
               
               if verbose:
                  print(mos_val, mos_points)
                  print(res[0], res[1])
               
               if p == "dd12":
                  ff12 = db.get_obs_data(cityID, ffID, tdate, d)
                  special = [ np.copy( ff12 ) ]

               if val <= mos_val:
                  obs = np.copy( val )
                  bet = np.copy( mos_val )
               else:
                  obs = np.copy( mos_val )
                  bet = np.copy( val )

               dP = pmax - jug.get_points( [obs*10], p, [bet*10], special, tdate )[0]
               special = () # reset var

               if p == "dd12":
                  if val < 90 and mos_val > 270:
                     val += 90; mos_val += 90
                  elif mos_val < 90 and val > 270:
                     mos_val -= 90; val -= 90
                  dV = 360 - abs(val - mos_val)
                  if dV > 180:
                     dV = 360 - dV
               else:
                  dV = val - mos_val

               if verbose:
                  print(type(val), type(mos_val))
                  print(val, mos_val)

               if date.today().weekday() == 4:
                  dO = 0
               else:
                  dO = res[1] - mos_points

               new_row = {'MOS':m, 'Diff(Val)':dV, 'Diff(Pts)':dP, 'Diff(Obs)':dO, 'Param':p, 'City':cname, 'Day':dayname[d]}

               out = pd.concat( [ out, pd.DataFrame([new_row]) ], ignore_index=True )

   val = out["Diff(Val)"]
   pts = out["Diff(Pts)"]
   obs = out["Diff(Obs)"]
   
   out = out.sort_values(by='Diff(Obs)', key=abs, ascending=False)

   sum_row  = { 'MOS':"SUM", 'Diff(Val)':val.sum(), 'Diff(Pts)':pts.sum(), 'Diff(Obs)':obs.sum() }
   mean_row = { 'MOS':"MEAN", 'Diff(Val)':val.mean(), 'Diff(Pts)':pts.mean(), 'Diff(Obs)':obs.mean() }

   stat_rows = pd.DataFrame([sum_row, mean_row])
   if verbose: print(stat_rows)
   out = pd.concat( [ out, stat_rows ], ignore_index=True )

   date_str = utils.tdate2string( tdate )
   if verbose: print(date_str)
   
   writer = pd.ExcelWriter( f"mswr/{date_str}.xlsx" )
   out.to_excel(writer, index=False, sheet_name="Sheet1", engine="xlsxwriter", float_format="%.1f")
   #nuber format
   workbook  = writer.book
   worksheet = writer.sheets["Sheet1"]
   fmt = workbook.add_format({"num_format": "0.0"})
   worksheet.set_column("B:D", None, fmt)
   writer.close()

   if verbose: print(out)

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
   track(db, cities, tdate, config, verbose)

   db.commit()
   db.close()
