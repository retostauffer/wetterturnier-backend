# -------------------------------------------------------------------
# - NAME:        ComputeSumPoints.py
# - AUTHOR:      Reto Stauffer
# - DATE:        2014-09-21
# - LICENSE: GPL-3, Reto Stauffer, copyright 2014
# -------------------------------------------------------------------
# - DESCRIPTION: Compute summated points for all players. 
# -------------------------------------------------------------------
# - EDITORIAL:   2014-09-19, RS: Created file on thinkreto.
#                Adapted from ComputePetrus.py
# -------------------------------------------------------------------
# - L@ST MODIFIED: 2017-06-29 01:08 on thinkreto
# -------------------------------------------------------------------



# -------------------------------------------------------------------
# - Embedded function. Can be used on its own (called from
#   ComputePoints.py)
#   IF STARTED AS A SCRIPT PLEASE CHECK THE PART BELOW THE 
#   FUNCTION HERE!
# -------------------------------------------------------------------
def CSP(db,config,cities,tdates):

   import sys, os
   import numpy as np
   from pywetterturnier import utils
   print '\n  * Compute sum points to fill betstat table'

   # ----------------------------------------------------------------
   # - Now going over the cities and compute the points. 
   # ----------------------------------------------------------------
   for city in cities:

      # -------------------------------------------------------------
      # - If aldates, take all tdates from database
      # -------------------------------------------------------------
      if config['input_alldates']:
         tdates = db.all_tournament_dates( city['ID'] )

      # -------------------------------------------------------------
      # - Looping trough dates
      # -------------------------------------------------------------
      for tdate in tdates:

         # ----------------------------------------------------------------
         # - Check if we are allowed to perform the computation of the
         #   mean bets on this date
         # ----------------------------------------------------------------
         check = utils.datelock(config,tdate)
         if check:
            print '    Date is \'locked\' (datelock). Dont execute, skip.'
            continue

         print '    For %s tournament is %s' % (city['name'], utils.tdate2string( tdate ))

         # - If config['input_user'] is an integer value this
         #   is a userID. Compute the sum points for this user
         #   only. This is for some replay purposes.
         if type(config['input_user']) == type(int()):
            extra = ' AND userID = %d ' % config['input_user']
         else:
            extra = '' 

         sqlP = 'SELECT userID, cityID, tdate, ' + \
                'round(sum(points),1) AS points, max(placed) AS submitted ' + \
                'FROM %swetterturnier_bets ' + \
                'WHERE cityID = %d AND tdate = %d %s ' + \
                'GROUP BY userID, cityID, tdate '
         sqlP = sqlP % (db.prefix,city['ID'], tdate, extra)
         sqlX = 'SELECT userID, cityID, tdate, sum(points) AS points ' + \
                'FROM %swetterturnier_bets ' + \
                'WHERE cityID = %d AND tdate = %d ' + \
                'AND betdate = %d %s ' + \
                'GROUP BY userID, cityID, tdate'
         sql1 = sqlX % (db.prefix,city['ID'], tdate, tdate+1, extra)
         sql2 = sqlX % (db.prefix,city['ID'], tdate, tdate+2, extra)

         sql_full = 'SELECT p.points AS points, d1.points AS points_d1, d2.points AS points_d2, ' + \
                    'p.userID, p.cityID, p.tdate ' + \
                    'FROM ('+sqlP+') AS p ' + \
                    'LEFT OUTER JOIN ' + \
                    '('+sql1+') AS d1 ON p.userID=d1.userID AND p.tdate=d1.tdate ' + \
                    'AND p.cityID = d1.cityID ' + \
                    'LEFT OUTER JOIN ' + \
                    '('+sql2+') AS d2 ON p.userID=d2.userID AND p.tdate=d2.tdate ' + \
                    'AND p.cityID = d2.cityID ' + \
                    ''

         print '    - Reading data from database'
         cur = db.cursor()
         cur.execute( sql_full )
         desc = cur.description
         data = cur.fetchall()

         # Now compute 
         if len(data) == 0:
            print '    - Sorry, got no data to compute sum points'
         else:
            # Else: we have data, update database
            print '    - Upserting database (%d lines)' % len(data)

            # Require the index of the "points" variable
            points_idx = None
            for di in range(0,len(desc)):
               if str(desc[di][0]) == 'points':
                  points_idx = di
                  break
            if points_idx is None:
               sys.exit("ERROR: could not find variable \"points\" in data. Stop.")

            # - Prepare the data
            sql = 'UPDATE IGNORE '+db.prefix+'wetterturnier_betstat ' + \
                  'SET rank=%s, points=%s, points_d1=%s, points_d2=%s ' + \
                  'WHERE userID=%s AND cityID=%s AND tdate=%s'

            #for d in data:
            #    if not int(d[0]) == 1130: continue
            #    print d

            # Compute rank
            points = []
            for pi in range(0,len(data)): points.append(data[pi][points_idx])
            points = np.sort(points)[::-1]

            rank = []
            data = list(data)
            for pi in range(0,len(data)):
               this   = data[pi][points_idx]
               # if points is empty
               # Append empty rank (IN FRONT) and skip
               if not this:
                  data[pi] = (None,) + data[pi]
                  continue
               # else search rank
               # and append rank IN FRONT (check sql command)
               rank   = np.where(points == this)[0]
               if not len(rank):
                  data[pi] = (None,) + data[pi]
               else:
                  data[pi] = (rank[0] + 1,) + data[pi]
            
            cur.executemany( sql , data )
            db.commit()



# -------------------------------------------------------------------
# - Start as main script (not as module)
# -------------------------------------------------------------------
if __name__ == '__main__':

   import numpy as np
   # - Wetterturnier specific modules
   from pywetterturnier import utils, database
   
   # - Evaluating input arguments
   inputs = utils.inputcheck('ComputeSumPoints')
   # - Read configuration file
   config = utils.readconfig('config.conf',inputs)

   # - Initializing class and open database connection
   db        = database.database(config)
   # - Loading tdate (day since 1970-01-01) for the tournament.
   #   Normaly Friday-Tornament (tdate is then Friday) while
   #   the bet-dates are for Saturday and Sunday.
   if config['input_tdate'] == None:
      tdates     = [db.current_tournament()]
   else:
      tdates     = [config['input_tdate']]

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

   # - Calling the function now
   CSP(db,config,cities,tdates)

   db.commit()
