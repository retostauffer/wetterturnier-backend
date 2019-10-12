# -------------------------------------------------------------------
# - NAME:        ComputeMoses.py
# - AUTHOR:      Reto Stauffer
# - DATE:        2014-09-19
# - LICENSE: GPL-3, Reto Stauffer, copyright 2014
# -------------------------------------------------------------------
# - DESCRIPTION: Print moses files in oldput format.
#                Can be started several times. 
# -------------------------------------------------------------------
# - EDITORIAL:   2014-09-13, RS: Created file on thinkreto.
# -------------------------------------------------------------------
# - L@ST MODIFIED: 2018-01-09 21:12 on prognose2
# -------------------------------------------------------------------

#import python3's print function, back2thefuture!
from __future__ import print_function

# -------------------------------------------------------------------
# - Embedded function. Can be used on its own (called from
#   ComputeMoses.py)
#   IF STARTED AS A SCRIPT PLEASE CHECK THE PART BELOW THE 
#   FUNCTION HERE!
# -------------------------------------------------------------------
def print_moses( db, config, cities, tdates ):

   path="moses/input/"
   table_head = "Spielername               N  SD  DD FF FX Wv Wn    PPP    TX    TN    TD    RR"
   day_heads = ["                                      Samstag","                                      Sonntag"]
   params = db.get_parameter_names( sort=True )

   def print_rows( args, file ):
      row_format = "{name:<21.21s} {n:>5} {sd:>3} {dd:>3} {ff:>2} {fx:>2} {wv:>2} {wn:>2} {ppp:>6.6} {tn:>5.5} {tx:>5.5} {td:>5.5} {rr:>5.5}"

      for i in range(1,8):
         if type( args[i] ) != str: args[i] = int( args[i] )

      print( row_format.format(
                name=args[0],
                n=args[1],
                sd=args[2],
                dd=args[3],
                ff=args[4],
                fx=args[5],
                wv=args[6],
                wn=args[7],
                ppp=args[8],
                tn=args[9],
                tx=args[10],
                td=args[11],
                rr=args[12]), file=f) 


   for city in cities:
      cityID = city['ID']
      if config['input_alldates']:
         tdates = db.all_tournament_dates( city['ID'] )
      for tdate in tdates:
         #workaround for missing ZUR bets on 3 tdates, dirty
         if cityID == 3 and tdate in [15870, 15849, 15898]: continue
         stations = db.get_stations_for_city( cityID, active=False, tdate=tdate )
         #print output to file, first get prober filename
         filename = path + utils.tdate2string( tdate, moses=True )+"."+city['name'].lower()[0]+"pw"
         f = open(filename,'w')
         users = db.get_participants_in_city( cityID, tdate, sort=True )
         for day in range(1,3):
            print(day_heads[day-1], file=f)
            print("", file=f)
            for i in range(4):
               print("", file=f)
            print(table_head, file=f)
            print(78*"-", file=f)
            for station in stations:
               obs = [station.name]
               for param in params:
                  paramID = db.get_parameter_id( param )
                  value = db.get_obs_data( cityID, paramID, tdate, day, station.wmo )
                  if value is False or value is None: obs.append( "n" )
                  else:
                     obs.append( float( value ) / 10 )
               print_rows( obs, f )
            print(78*"-", file=f)
            for userID in users:
               bet = [db.get_username_by_id(userID,which="display_name")]
               for param in params:
                  paramID = db.get_parameter_id( param )
                  value = db.get_bet_data( "user", userID, cityID, paramID, tdate, day )
                  if value is False or value is None: bet.append( "n" )
                  else:
                     bet.append( float( value ) / 10 )
               print_rows( bet, f )
            if day == 1: print("\f", file=f)
            else: print("", file=f)

# -------------------------------------------------------------------
# - Start as main script (not as module)
# -------------------------------------------------------------------
if __name__ == '__main__':

   import sys, os
   import numpy as np
   from glob import glob
   # - wetterturnier specific packages
   from pywetterturnier import utils, database
   from datetime import datetime as dt
   import numpy as np

   # - Evaluating input arguments
   inputs = utils.inputcheck('PrintMoses')
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

   # - Calling the function now
   print_moses(db,config,cities,tdates)
