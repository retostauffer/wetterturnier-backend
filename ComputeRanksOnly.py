# -------------------------------------------------------------------
# - NAME:        ComputeRanksOnly.py
# - AUTHOR:      Reto Stauffer
# - DATE:        2017-06-27
# -------------------------------------------------------------------
# - DESCRIPTION: Computes ranking based on what is stored in the
#                wp_wetterturnier_betstat table on "total points"
#                and updates the database.
# -------------------------------------------------------------------
# - EDITORIAL:   2017-06-27, RS: Created file on thinkreto.
# -------------------------------------------------------------------
# - L@ST MODIFIED: 2017-06-27 12:58 on thinkreto
# -------------------------------------------------------------------

import sys, os
sys.path.append('PyModules')


# - Start as main script (not as module)
if __name__ == '__main__':

   import numpy as np
   # - Wetterturnier specific modules
   from pywetterturnier import utils
   from pywetterturnier import database
   
   # - Evaluating input arguments
   inputs = utils.inputcheck('ComputePoints')
   # - Read configuration file
   config = utils.readconfig('config.conf',inputs)

   # - Initializing class and open database connection
   db        = database.database(config)
   # - Loading tdate (day since 1970-01-01) for the tournament.
   #   Normaly Friday-Tornament (tdate is then Friday) while
   #   the bet-dates are for Saturday and Sunday.
   if config['input_tdate'] == None:
      tdates     = [db.current_tournament()]
      print '  * Current tournament is %s' % utils.tdate2string( tdates[0] )
   else:
      tdates     = [config['input_tdate']]


   # - If input_user was given as string we have to find the
   #   corresponding userID first!
   if type(config['input_user']) == type(str()):
      config['input_user'] = db.get_user_id( config['input_user'] )
      if not config['input_user']:
         utils.exit('SORRY could not convert your input -u/--user to corresponding userID. Check name.')
   
   # - Loading all parameters
   params = db.get_parameter_names(False)

   # ----------------------------------------------------------------
   # - Because of the observations we have to compute the
   #   points city by city. Loading city data here first. 
   # ----------------------------------------------------------------
   # - Loading all different cities (active cities)
   cities     = db.get_cities()
   # - If input city set, then drop all other cities.
   if not config['input_city'] == None:
      tmp = []
      for elem in cities:
         if elem['name'] == config['input_city']: tmp.append( elem )
      cities = tmp

   # ----------------------------------------------------------------
   # - Now calling the function which computes the sum points
   #   filling in the betstat table.
   # ----------------------------------------------------------------
   for city in cities:

      # Take all dates
      if config['input_alldates']:
         tdates = db.all_tournament_dates( city['ID'] )

      for tdate in tdates:

         cur = db.cursor()

         sql = "SELECT userID, points FROM wp_wetterturnier_betstat " + \
               "WHERE cityID = %d AND tdate = %d" % (city['ID'],tdate)

         cur.execute(sql)
         tmp = cur.fetchall()
         data   = []
         points = []
         for rec in tmp:
            data.append( [int(rec[0]),float(rec[1]),None] )
            points.append( float(rec[1]) )

         # Take unique points and reverse-sort them
         points = np.unique(points)
         points.sort(); points = points[::-1]

         # Apply rank
         for rec in data:
            rank = np.where( points == rec[1] )[0]
            if not len(rank) == 1 :
               print points
               print rec
               print rank
               sys.exit('cannot apply rank')
            rec[2] = rank[0] + 1

            sql = "UPDATE wp_wetterturnier_betstat SET rank = %d" % rec[2] + \
                  " WHERE cityID = %d" % city['ID'] + \
                  " AND tdate = %d AND userID = %d" % (tdate,rec[0])
            cur.execute( sql )

         db.commit()


   db.close()
