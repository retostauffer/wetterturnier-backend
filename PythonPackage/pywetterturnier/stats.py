from __future__ import division
from pywetterturnier import utils

#compute statistics out of some wetterturnier database tables like *betstat
def compute_stats(self, cityID, measures, userID=False, tdate=False, day=0, last_tdate=None, referenz=True, mitteltips=True, aliases=None, pout=25, pmid=100, midyear=2010, span=None, dates=None, verbose=False):
   """
   Computes all kinds of statistics e.g. the points for the eternal list plus min/max/median/mean of points for each user, city, tdate and so on.
   """ 
   res = {} #results will be saved here with measures as keys, tdate as subkeys

   import numpy as np

   cur = self.db.cursor()
   day_strs = ["", "_d1", "_d2"]
   day_str = day_strs[0]
   if day != 0:
      day_str = day_strs[day]
   if last_tdate: last_tdate_str = " AND tdate<=" + str(last_tdate)
   else: last_tdate_str = ""

   sql = "SELECT points"+day_str+" FROM %swetterturnier_betstat WHERE "
   if tdate or (not tdate and not userID and cityID):
      # We don't want Sleepy in our tdatestats!
      #exclude = [self.get_user_id("Sleepy")]
      exclude = []
      if not referenz:
         groupID = self.get_group_id( "Referenztipps" )
         for j in self.get_participants_in_group( groupID, cityID, tdate, playing=False ):
            exclude.append( j )

      if not mitteltips:
         #include no groups
         sql2 = "SELECT ID FROM %susers WHERE user_login LIKE \"%s\""
         cur.execute( sql2 % ( self.prefix, "GRP_%" ) )
         data2 = cur.fetchall()
         for j in data2:
            exclude.append( int(j[0]) )

      if tdate: #tdatestats
         #only include users who really played on tdate (no sleepy points!)
         #played = self.sql_tuple( self.get_participants_in_city( cityID, tdate ) )
         sql += "cityID=%d AND tdate=%d AND userID NOT IN%s" + last_tdate_str
         cur.execute( sql % ( self.prefix, cityID, tdate, self.sql_tuple(exclude) ) )

      elif cityID: #citystats
         sql2 = "SELECT part FROM %swetterturnier_tdatestats WHERE cityID=%d" + last_tdate_str
         cur.execute( sql2 % ( self.prefix, cityID ) )
         data = cur.fetchall()
         for i in measures:
            parts = []
            for j in data:
               parts.append( int(j[0]) )
            if i == "mean_part": res[i] = np.mean( parts )
            elif i == "max_part": res[i] = np.max( parts )
            elif i == "min_part": res[i] = np.min( parts )
            elif i == "tdates": res[i] = len( parts )

         sql += "cityID=%d AND userID NOT IN%s" + last_tdate_str
         cur.execute( sql % ( self.prefix, cityID, self.sql_tuple(exclude) ) )

   elif userID: #userstats
      userIDs = [userID]
      #if we are using an alias dict we merge all aliases of a user with his/her other identities
      if aliases:
         username = self.get_username_by_id( userID )
         if username in aliases.keys() or username in sum(aliases.values(), []):
            if verbose: print username
            for j in aliases.keys():
               if username == j:
                  for k in aliases[j]:
                     userIDs.append( self.get_user_id( k ) )
                  break
               else:
                  if username in aliases[j]:
                     userIDs.append( self.get_user_id( j ) )
                     for k in aliases[j]:
                        userID = self.get_user_id( k )
                        if userID not in userIDs:
                           userIDs.append( userID )
            if verbose: print userIDs

      sql += "userID IN%s"
      if cityID != 0:
         sql += " AND cityID=%d" + last_tdate_str
         cur.execute( sql % ( self.prefix, self.sql_tuple(userIDs), cityID ) )
      else:
         sql += last_tdate_str
         cur.execute( sql % ( self.prefix, self.sql_tuple(userIDs) ) )

   else:
      utils.exit( "Wrong usage of compute_stats!")

   data = cur.fetchall()
   points = []
   for i in data:
      #sleepy has NULL points on d1 and d2, skip him!
      if i[0] == None: continue
      else: points.append( float(i[0]) )

   if not points: points.append(0)


   if cityID == 0:
      """
      first calculate sd_ind for all tournaments played. Pretend as cities were one
      so if a user participated in multiple cities on the same day
      it counts like he played multiple tournaments &
      for each of these tournaments we look up the sd_upp and calculate a mean (sd_ind)
      """
      sql = "SELECT cityID, tdate, points FROM %swetterturnier_betstat WHERE userID IN%s AND tdate <= %d"
      cur.execute( sql % (self.prefix, self.sql_tuple(userIDs), last_tdate ) )
      points = {}
      for j in cur.fetchall():
         if j[0] not in points:
            points[j[0]] = {}
         points[j[0]][j[1]] = j[2]

      sd_upp = []
      for cityID in points.keys():
         for tdate in points[cityID].keys():
            sd_upp.append( self.get_stats( cityID, measure="sd_upp", tdate=tdate ) )

      if not sd_upp: return {"points_adj":0}
      #remove None values
      sd_upp = [x for x in sd_upp if x]
      sd_ind = np.nanmean(sd_upp)
      res["sd_ind"] = sd_ind

      #now we get the individual points for each tournament played
      points_adj = []
      parts = {}
      for cityID in points.keys():
         parts[cityID] = 0

      for cityID in points.keys():
         for tdate in points[cityID].keys():
            median = self.get_stats( cityID, measure="median", tdate=tdate )
            points_adj.append( points[cityID][tdate] - median )
            parts[cityID] += 1
      
      #get mean participations for every city a user ever played
      parts_all = np.sum( parts.values() )
      #actually parts_mean, we will use this variable in calculation
      parts = parts_all / len(parts.values())
      res["part"] = parts_all
      
      sql = "SELECT points FROM wp_wetterturnier_betstat WHERE userID IN%s"
      cur.execute( sql % self.sql_tuple(userIDs) )
      points_all = [ j[0] for j in cur.fetchall() if j[0] ]

      if points_all:
         res["max"]  = np.max(points_all)
         res["mean"] = np.mean(points_all)

      #norm by sd_ind, scale by mean participations in all cities
      if parts < pout:
         f = 0
      elif parts < pmid:
         f = np.sqrt( float(parts) / pmid )
      else:
         f = 1

      #average points above median
      res["points_med"] = np.mean(points_adj)
      
      #final adjusted points
      res["points_adj"] = f * (res["points_med"] / sd_ind) * 1000
      if np.isnan( res["points_adj"] ):
         res["points_adj"] = 0
      
      sql = """
      SELECT rank, count(rank) AS count FROM %swetterturnier_betstat
      WHERE userID IN%s AND rank <= 3 %s
      GROUP BY rank ORDER BY rank
      """
      cur.execute( sql % (self.prefix, self.sql_tuple(userIDs), last_tdate_str) )
      ranks = {1:"0", 2:"0", 3:"0"}
      for j in cur.fetchall():
         ranks[j[0]] = str(j[1])

      res["ranks_weekend"] = ",".join(ranks.values())

      return res

   elif cityID == 6:   
      #weighted variant sum(p_adj_i * part_i) / sum(part_i)
      
      #which cities did the user play? would be better to call userstat but then we need to get rid of zero/null rows...
      sql = "SELECT cityID FROM wp_wetterturnier_betstat WHERE userID IN%s"
      cur.execute( sql % self.sql_tuple(userIDs) )
      cityIDs=[]
      for i in cur.fetchall():
         if i[0] not in cityIDs: cityIDs.append(i[0])

      #get points_adj from userstats
      points_adj, parts, sd_ind = ([] for _ in range(3))
      for cityID in cityIDs:
         measures = self.get_stats( cityID=cityID, userID=userIDs[0], measures=["points_adj","part","sd_ind"] )
         if measures:
            points_adj.append(measures[0])
            parts.append(     measures[1])
            sd_ind.append(    measures[2])

      if not points_adj or not parts or not sd_ind or None in points_adj:
         res["points_adj"] = 0
         res["part"]       = 0
         res["sd_ind"]     = 0
         return res

      else:
         sql = "SELECT points FROM wp_wetterturnier_betstat WHERE userID IN%s"
         cur.execute( sql % self.sql_tuple(userIDs) )
         points_all = [ j[0] for j in cur.fetchall() if j[0] ]

         if points_all:
            res["max"]  = np.max(points_all)
            res["mean"] = np.mean(points_all)
         
         sql = """
         SELECT rank, count(rank) AS count FROM %swetterturnier_betstat
         WHERE userID IN%s AND rank <= 3 %s
         GROUP BY rank ORDER BY rank
         """
         cur.execute( sql % (self.prefix, self.sql_tuple(userIDs), last_tdate_str) )
         ranks = {1:"0", 2:"0", 3:"0"}
         for j in cur.fetchall():
            ranks[j[0]] = str(j[1])

         res["ranks_weekend"] = ",".join(ranks.values())

         parts_all         = np.sum( parts)
         res["part"]       = parts_all
         res["points_adj"] = np.dot( points_adj, parts ) / parts_all
         res["sd_ind"]     = np.dot( sd_ind, parts ) / parts_all
         return res

   for i in measures:
      i += day_str
      if i == "points"+day_str:
         res[i] = sum(points)
      elif "sd_ind" in i and "_d" not in i:
         #get tdates where the user participated
         sql = "SELECT tdate FROM %swetterturnier_betstat WHERE userID IN%s AND cityID=%d"
         if "1" in i or "2" in i or "X" in i:
            spanstr = i[-1]

            if midyear:
               middle_tdate = str(utils.string2tdate(str(midyear)+"-01-01"))
            #print "Middle of tournament (tdate): %s" % middle_tdate
            if "1" in i:
               sql+=" AND tdate<="+middle_tdate
            elif "2" in i:
               sql+=" AND tdate>"+middle_tdate
            elif span:
               if verbose: print span
               sql+=" AND tdate BETWEEN "+str(span[0])+" AND "+str(span[1])

         cur.execute( sql % (self.prefix, self.sql_tuple(userIDs), cityID) )
         tdates = [j[0] for j in cur.fetchall()]

         sql = "SELECT sd_upp from %swetterturnier_tdatestats WHERE cityID=%d AND tdate IN%s"
         cur.execute( sql % (self.prefix, cityID, self.sql_tuple(tdates) ) )
         #print sql % (self.prefix, cityID, self.sql_tuple(tdates) )
         sd_upp = [j[0] for j in cur.fetchall()]
         res[i] = np.mean( sd_upp )
         #print(res[i])
         if res[i] == None or np.isnan(res[i]): res[i] = 0

      elif "points_adj" in i and "_d" not in i:
         if verbose:
            print self.get_username_by_id( userIDs[0] )
            print i,"\n"

         #skip Sleepy
         #if self.get_user_id("Sleepy") in userIDs: continue

         parts = len(points)
         if not parts: continue
         """
         find all dates where the user actually played
         for each date calculate:
         (points-points) / (ymax-median*)
         sum up and divide by number of tdates
         * daily median and median fitted by PlotStats
           should be calculated earlier in ComputeStats with other citystats!
         """
         tdates = {}
         sql = "SELECT tdate, points FROM %swetterturnier_betstat WHERE userID IN%s AND cityID=%d"
         if "1" in i or "2" in i or "X" in i:
            if midyear:
               middle_tdate = str(utils.string2tdate(str(midyear)+"-01-01"))
            if verbose:
               print "Middle of tournament (tdate): %s" % middle_tdate
            if "1" in i:
               sql+=" AND tdate<="+middle_tdate
            elif "2" in i:
               sql+=" AND tdate>"+middle_tdate
            elif span:
               if verbose: print span
               sql+=" AND tdate BETWEEN "+str(span[0])+" AND "+str(span[1])
               #print sql
         cur.execute( sql % (self.prefix, self.sql_tuple(userIDs), cityID) )
         data = cur.fetchall()

         for j in data:
            tdates[j[0]] = {}
            tdates[j[0]]["points"] = j[1]

         #get the actual median for each tdate
         sql = "SELECT tdate, median from %swetterturnier_tdatestats WHERE cityID=%d AND tdate IN%s"
         cur.execute( sql % (self.prefix, cityID, self.sql_tuple(tdates.keys()) ) )
         data = cur.fetchall()
         for j in data:
            tdates[j[0]]["median"] = j[1]

         if "1" in i: timestr="1"
         elif "2" in i: timestr="2"
         elif "X" in i: timestr="X"
         else: timestr = "" 
         sd_ind = self.get_stats( cityID, measure="sd_ind"+timestr, userID=userIDs[0] )
         if sd_ind in [0, None] or np.isnan(sd_ind): continue

         if verbose:
            print "tdate      points median sd      points_adj"

         points_adj = []

         for t in sorted(tdates.keys()):
            if {"points","median"} <= set(tdates[t]):
               perc = tdates[t]["points"] - tdates[t]["median"]
               if verbose:
                  print utils.tdate2string(t), str(tdates[t]["points"]).ljust(6), str(tdates[t]["median"]).ljust(6), str(round(sd_ind,2)).ljust(7), str(round(perc,2)).ljust(10)
            else: continue

            points_adj.append( perc )

         if not points_adj: points_adj.append(0)
         if verbose:
            print ""

         #if someone has less than "pout" parts, just kick him out!
         if parts < pout:
            f = 0
         #in between pout and pmid the points get adjusted by the sqrt() function
         elif parts < pmid:
            f = np.sqrt( float(parts) / pmid )
         else: #if parts >= pmid
            f = 1
         #average points above median
         res["points_med"] = np.mean(points_adj)

         #final adjusted points
         res["points_adj"] = f * (res["points_med"] / sd_ind) * 1000
         if np.isnan( res["points_adj"] ):
            res["points_adj"] = 0

      elif i == "mean"+day_str:
         res[i] = round(np.mean(points), 1)
      
      elif i == "median"+day_str:
         res[i] = np.median(points)
      
      elif i == "Qlow"+day_str:
         res[i] = np.percentile(points, 25, interpolation="midpoint")
      
      elif i == "Qupp"+day_str:
         res[i] = np.percentile(points, 75, interpolation="midpoint")
      
      elif i == "max"+day_str:
         res[i] = max(points)
      
      elif i == "min"+day_str:
         res[i] = min(points)
      
      elif i == "sd"+day_str: #standard deviation
         sd = np.std(points)
         if np.isnan(sd): res[i] = 0
         else: res[i] = sd

      elif i == "part":
         #important for part count, otherwise could be 1 if a player/date actually has 0 part
         if len(points) == 1 and points[0] == 0: res[i] = 0
         else: res[i] = len(points)
      
      elif i == "sd_upp"+day_str:
         median = self.get_stats( tdate=tdate, cityID=cityID, measure="median"+day_str )
         if not median: median = res["median"+day_str]
         if not median: continue
         sql = "SELECT points"+day_str+" from %swetterturnier_betstat WHERE tdate=%d AND cityID=%d AND points"+day_str+" > %f"
         #print sql % (self.prefix, tdate, cityID, median)
         cur.execute( sql % (self.prefix, tdate, cityID, median) )
         sd = np.mean( [ j[0] - median for j in cur.fetchall() ] )

         if np.isnan(sd): res[i] = 0
         else: res[i] = sd

      elif i == "ranks_weekend":
         sql = """
         SELECT rank, count(rank) AS count FROM %swetterturnier_betstat
         WHERE cityID = %d AND userID IN%s AND rank <= 3 %s
         GROUP BY rank ORDER BY rank
         """
         cur.execute( sql % (self.prefix, cityID, self.sql_tuple(userIDs), last_tdate_str) )
         ranks = {1:"0", 2:"0", 3:"0"}
         for j in cur.fetchall():
            ranks[j[0]] = str(j[1])
         
         res[i] = ",".join(ranks.values())
         
      elif i == "ranks_season":
         pass

      else: continue

   if not res: utils.exit("No results!")
   return res


def get_stats(self, cityID, measure=None, measures=None, userID=None, tdate=None, tdates=None, day=None):
   """Get statistics from tables citystats, userstats, tdatestats"""

   if measure: measures = [measure]
   if tdate:   tdates   = [tdate]

   cur = self.cursor()
   if tdates or (not tdates and not userID and cityID):

      if day:
         days_str = "_"+str(day)
         for m in range(measures):
            measures[m] += day_str

      if tdates:
         sql = "SELECT %s FROM %swetterturnier_tdatestats WHERE cityID=%d AND tdate IN%s"
         cur.execute( sql % ( self.sql_tuple(measures, 1), self.prefix, cityID, self.sql_tuple(tdates) ) )

      elif cityID:
         sql = "SELECT %s FROM %swetterturnier_citystats WHERE cityID=%d"
         cur.execute( sql % ( self.sql_tuple(measures, 1), self.prefix, cityID ) )

   elif userID:
      sql = "SELECT %s FROM %swetterturnier_userstats WHERE cityID=%d AND userID=%d"
      #print sql % ( self.sql_tuple(measures, 1), self.prefix, cityID, userID )
      cur.execute( sql % ( self.sql_tuple(measures, 1), self.prefix, cityID, userID ) )
   
   data = cur.fetchall()
   if not data: return None
   res = [ elem for elem in data[0] ]
   if len(res) == 1: return res[0]
   elif not res: return None
   else: return res


def upsert_stats(self, cityID, stats, userID=False, tdate=False, day=0):
   """Insert stats dict into database"""
   cur = self.db.cursor()
   mstr   = ""
   values, sql_vals = [], ""
   update = " ON DUPLICATE KEY UPDATE "

   for i in stats.keys():
      mstr += "%s, " % i
      values.append( stats[i] )
      sql_vals = sql_vals + i + "=VALUES(" + i + "), "
   sql_vals, mstr = sql_vals[:-2], mstr[:-2]

   if tdate:
      sql = "INSERT INTO %swetterturnier_tdatestats (cityID, tdate, %s) VALUES %s" + update + sql_vals
      cur.execute( sql % (self.prefix, mstr, str(self.sql_tuple(sum( [[cityID],[tdate],values], [])) )  ))
   elif userID:
      sql = "INSERT INTO %swetterturnier_userstats (userID, cityID, %s) VALUES %s" + update + sql_vals
      cur.execute( sql % (self.prefix, mstr, str(self.sql_tuple(sum( [[userID],[cityID],values], []) ) ) ))
   elif cityID:
      sql = "INSERT INTO %swetterturnier_citystats (cityID, %s) VALUES %s" + update + sql_vals
      cur.execute( sql % (self.prefix, mstr, str(self.sql_tuple(sum( [[cityID],values], []) ) ) ))
   else: utils.exit("Wrong usage of upsert_stats in database.py!")
