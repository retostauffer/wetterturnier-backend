# -------------------------------------------------------------------
# - NAME:        database.py
# - AUTHOR:      Reto Stauffer
# - DATE:        2014-09-13
# -------------------------------------------------------------------
# - DESCRIPTION: Database class handling the database connection.
# -------------------------------------------------------------------
# - EDITORIAL:   2014-09-13, RS: Created file on thinkreto.
# -------------------------------------------------------------------
# - L@ST MODIFIED: 2015-08-04 07:36 on prognose2.met.fu-berlin.de
# -------------------------------------------------------------------


import MySQLdb
import utils

class database(object):

   # ----------------------------------------------------------------
   # - Init
   # ----------------------------------------------------------------
   def __init__(self,config):
      """The database class is handling the connection to the
      mysql database and different calls and stats."""

      self.config = config
      self.db = self.__connect__()

      self.prefix = self.config['mysql_prefix']

   # ----------------------------------------------------------------
   # - Init
   # ----------------------------------------------------------------
   def __connect__(self):
      """Open database connection"""

      print '  * Establishing database connection'
      host   = self.config['mysql_host']
      user   = self.config['mysql_user']
      passwd = self.config['mysql_pass']
      db     = self.config['mysql_db']
      return MySQLdb.connect(host=host,user=user,passwd=passwd,db=db)

   # ----------------------------------------------------------------
   # - Some methods from mysql 
   # ----------------------------------------------------------------
   def cursor(self):
      return self.db.cursor()
   def execute(self,sql):
      return self.db.execute(sql)
   def executemany(self,sql,data):
      return self.db.executemany(sql,data)
   def commit(self):
      self.db.commit()


   # -------------------------------------------------------------------
   # - Create a group
   # -------------------------------------------------------------------
   def create_group(self, name, desc ):
   
      c_sql = 'SELECT count(*) FROM %swetterturnier_groups WHERE ' + \
              'groupName =\'%s\''
      i_sql = 'INSERT INTO %swetterturnier_groups ' + \
              '(groupName, groupDesc, active) VALUES (\'%s\', \'%s\', 1)'
   
      # - Check if allready existing
      cur = self.db.cursor()
      cur.execute( c_sql % (self.prefix,name) )
      N = cur.fetchone()[0]
      if N > 0:
         print '    Group %s already existing.' % name
         return

      # - Create group
      print '    Group %s created.' % name
      cur.execute( i_sql % (self.prefix,name,desc) )
      self.db.commit()


   # -------------------------------------------------------------------
   # - Create a group
   # -------------------------------------------------------------------
   def create_user(self, name, password = None ):

      import os
      import utils

      # - If wpconfig is missing we cannot create the new user.
      #   In this case, stop. This is just for the development
      #   server.
      # - If the file wp-config.php does not exist, stop.
      if not os.path.isfile( self.config['migrate_wpconfig'] ):
         utils.exit('Sorry, %s does not exist. Stop. Necessary to create wp users' % config['migrate_wpconfig'])

      
   
      # - If name length is equal to zero, stop too.
      if len(name.strip()) == 0:
         utils.exit('BUMM got empty username for database.create_user')
   
      # - Check if allready existing
      sql = 'SELECT count(*) FROM %susers WHERE ' + \
              'user_login =\'%s\''
      cur = self.db.cursor()
      cur.execute( sql % (self.prefix,name) )
      N = cur.fetchone()[0]
      if N > 0:
         print '    User %s already existing.' % name
         return

      # - We are using php to create the user. Reason:
      #   I havn't found out what wordpress is doing.
      #   Therefore I am using wordpress's intrinsic function
      #   to create propper users.
      if password == None:
         password = name[::-1]
      str = []
      str.append('<?php')
      str.append('require_once(\'%s\');' % self.config['migrate_wpconfig'])
      str.append('$a = wp_create_user(\'%s\',\'%s\');' % (name, password))
      str.append('print_r( $a );')
      str.append('?>')

      # - Crate php file
      print '    Create php file to create the user'
      phpfile = '%s/create_user.php' % self.config['rawdir']
      fid = open( phpfile,'w+');
      fid.write( '\n'.join( str ) )
      fid.close()

      print '    Calling php file now ...'
      print ' ---------------------------- '
      os.system('cat %s' % phpfile)
      print ' ---------------------------- '
      os.system('php %s' % phpfile)

      userID = self.get_user_id( name )
      if not userID:
         utils.exit('OH DEAR, CREATED USER BUT GOT NO userID IN RETURN')




   # -------------------------------------------------------------------
   # - Getting dict containing all active cities in the database. 
   # -------------------------------------------------------------------
   def get_cities(self):

      print '  * %s' % 'looking active cities'
      sql = 'SELECT ID, name FROM %swetterturnier_cities WHERE active = 1 ' + \
            'ORDER BY ID'

      cur = self.cursor()
      cur.execute( sql % self.prefix )
      data = cur.fetchall()

      if len(data) == 0:
         utils.exit('Cannot load city data from database in database.current_tournament')
      
      res = []
      for elem in data:
         res.append( {'name':str(elem[1]),'ID':int(elem[0])} )

      return res


   # -------------------------------------------------------------------
   # - Loading stations from database for a given city
   # -------------------------------------------------------------------
   def get_stations_for_city(self,cityID):
      """!Loading all stations mached to a certain city.
      @param cityID. Integer, ID of the city in the database.
      @return List object containing @b N @ref stationclass.stationclass objects.
      """

      sql = "SELECT * FROM %swetterturnier_stations WHERE cityID = %d" % (self.prefix,cityID)
      cur = self.db.cursor()
      cur.execute( sql )
      desc = cur.description
      data = cur.fetchall()

      from stationclass import *
      stations = []
      for rec in data: stations.append( stationclass(desc,rec) )

      return stations


   # -------------------------------------------------------------------
   # - Current tournament
   # -------------------------------------------------------------------
   def current_tournament(self):

      print '  * %s' % 'Searching current tournament date'
      sql = 'SELECT max(tournamentdate) FROM %swetterturnier_bets'

      cur = self.cursor()
      cur.execute( sql % self.config['mysql_prefix'] )
      tdate = cur.fetchone()[0]

      print '    Current tournament date is: %d' % tdate

      return tdate


   # -------------------------------------------------------------------
   # - Get all tournament dates 
   # -------------------------------------------------------------------
   def all_tournament_dates(self,cityID):

      print '  * %s' % 'Searching all tournament dates for city %d' % cityID
      sql = 'SELECT tournamentdate FROM %swetterturnier_bets ' + \
            'WHERE cityID = %d GROUP BY tournamentdate'

      # - DEVELOPMENT: ONLY DATES 2015+
      print "[!] RETO: DEVELOPMENT IN all_tournament_dates YOU ARE ONLY"
      print "    PICKING DATES 2015+ AND NOT ALL ..."
      sql = 'SELECT tournamentdate FROM %swetterturnier_bets ' + \
            'WHERE cityID = %d AND tournamentdate > 16436 GROUP BY tournamentdate'

      cur = self.cursor()
      cur.execute( sql % (self.config['mysql_prefix'], cityID) )
      data = cur.fetchall()
      tdates = []
      for elem in data: tdates.append( elem[0] )
      print '    Found %d different dates for city %d' % (len(tdates),cityID)

      return tdates

   # -------------------------------------------------------------------
   # - Returns alllllll bets for a given tournamentdate and
   #   a parameter. Returns ID and values. That's what we need
   #   to compute and store the points. Returns two lists with ID and values.
   #   This will be used by the judgingclass to compute the points.
   # -------------------------------------------------------------------
   def get_cityall_bet_data(self,cityID,paramID,tdate,day,nodeadman=True,nullonly=False):

      # - If day is smaller equal 5 then the betdate
      #   is tdate + day. Else day == betdate
      if day <= 5:
         betdate = tdate + day
      else:
         betdate = day

      cur = self.db.cursor()
      sql = 'SELECT ID, value FROM %swetterturnier_bets ' + \
            'WHERE cityID = %d AND paramID = %d AND betdate = %d AND ' + \
            'tournamentdate = %d' ### AND status = 1'

      # - If there is a userID on self.config['input_user']:
      #   only return the data for this user!
      if type(self.config['input_user']) == type(int()):
         sql += ' AND userID = %d' % self.config['input_user']

      # - Only compute points where points are NULL
      #   in the database
      if nullonly:
         sql += ' AND points IS NULL '

      if nodeadman:
         deadID = self.get_user_id('Deadman')
         sql += ' AND userID != %d ' % deadID
      cur.execute( sql % (self.prefix, cityID, paramID, betdate, tdate) ) 
      #####cur.execute( sql % (self.prefix, cityID, paramID, betdate, tdate, 1) ) 

      data = cur.fetchall()
      if not data or len(data) == 0:
         return False, False
      else:
         IDs = []; values = []
         for elem in data:
            IDs.append( int(elem[0]) )
            values.append( int(elem[1]) )
         return IDs, values
      

   # -------------------------------------------------------------------
   # - Loading bets. 
   # -------------------------------------------------------------------
   def get_bet_data(self,typ,ID,cityID,paramID,tdate,bdate):

      import numpy as np

      # - Typ is either "all" for Petrus (takes all human bets),
      #   "user" to get the bet of one user (ID = userID), or
      #   "group" to get the bets for a group (ID = groupID)
      if not typ in ['all','user','group']:
         utils.exit('Wrong typ input to database.get_bet_data. Has to be all, user, or group')
      
      # - bdate is either a bet date (days since 1970-01-01) or
      #   an integer lower 5. If the second one is the case
      #   bdate = tdate+bdate to get days.
      if bdate <= 5: bdate = tdate + bdate
      cur = self.db.cursor()

      # - Ignore the deadman!
      deadID = self.get_user_id('Deadman')

      # - For Petrus, load all bets for a given
      #   tournamentdate/betdate, city and parameter.
      if typ == 'all': 
         # - Also ignore Referenztips. They look like players but they
         #   should not be included into mitteltips. Else Persistenz
         #   is included into the computation of the Persistenz.
         ref = self.get_group_id('Referenztips')
         cur.execute( 'SELECT userID FROM %swetterturnier_groupusers WHERE groupID = %d' % (self.prefix, ref) )
         tmp = cur.fetchall()
         ref = [];
         for rec in tmp: ref.append('AND v.userID != %d' % rec[0] )
         # - Create final statement
         sql = 'SELECT v.value AS value FROM %swetterturnier_bets AS v ' + \
                     'LEFT OUTER JOIN %susers AS u ' + \
                     'ON v.userID = u.ID ' + \
                     'WHERE u.user_login NOT LIKE \'%s\' ' + \
                     'AND v.cityID = %d AND v.paramID = %d ' + \
                     'AND v.tournamentdate = %d AND v.betdate = %d ' + \
                     'AND v.userID != %d ' + ' '.join( ref )
                     #####'AND v.status = %d AND v.userID != %d'
         ###print( sql % (self.prefix, self.prefix, 'GRP_%', cityID, paramID, tdate, bdate, deadID) ) 
         cur.execute( sql % (self.prefix, self.prefix, 'GRP_%', cityID, paramID, tdate, bdate, deadID) ) 
      # - If input was user, load tips for a specific user.
      elif typ == 'user':
         sql = 'SELECT value FROM %swetterturnier_bets WHERE ' + \
                     'userID = %d AND cityID = %d AND paramID = %d ' + \
                     'AND tournamentdate = %d AND betdate = %d ' #####+ \
                     #####'AND status = %d'
         ####print self.prefix, ID, cityID, paramID, tdate, bdate
         ####print( sql % (self.prefix, ID, cityID, paramID, tdate, bdate ) ) 
         cur.execute( sql % (self.prefix, ID, cityID, paramID, tdate, bdate ) ) 
         #####cur.execute( sql % (self.prefix, ID, cityID, paramID, tdate, bdate, 1 ) ) 
      # - If input was user, load tips for a specific user.
      elif typ == 'group':
         sql = 'SELECT v.value AS value FROM %swetterturnier_bets AS v ' + \
                     'LEFT OUTER JOIN %swetterturnier_groupusers AS gu ' + \
                     'ON v.userID = gu.userID ' + \
                     'WHERE gu.groupID = %d ' + \
                     'AND v.cityID = %d AND v.paramID = %d ' + \
                     'AND v.tournamentdate = %d AND v.betdate = %d ' #####+ \
                     #####'AND v.status = %d'
         #####cur.execute( sql % (self.prefix, self.prefix, ID, cityID, paramID, tdate, bdate, 1) ) 
         cur.execute( sql % (self.prefix, self.prefix, ID, cityID, paramID, tdate, bdate) ) 
      # - Else ... adapt the exit condition above please.
      else:
         utils.exit('Seems that you allowed anohter type in database.get_bet_data but you have not created a propper rule')


      data = cur.fetchall()
      if not data or len(data) == 0:
         return False
      else:
         res = np.ndarray( len(data), dtype='float' )
         for i in range(len(data)):
            res[i] = float(data[i][0])
         return res


   # -------------------------------------------------------------------
   # - Insert or update a bet value of a given user
   # -------------------------------------------------------------------
   def upsert_bet_data(self,userID,cityID,paramID,tdate,bdate,value):

      # - bdate is either a bet date (days since 1970-01-01) or
      #   an integer lower 5. If the second one is the case
      #   bdate = tdate+bdate to get days.
      if bdate <= 5: bdate = tdate + bdate
      cur = self.db.cursor()

      sql = 'INSERT INTO %swetterturnier_bets ' + \
            '(userID, cityID, paramID, tournamentdate, betdate, value) VALUES ' + \
            '(%d, %d, %d, %d, %d, %d) ON DUPLICATE KEY UPDATE value = VALUES(value)'
            #####'(userID, cityID, paramID, tournamentdate, betdate, value, status) VALUES ' + \
            #####'(%d, %d, %d, %d, %d, %d, %d) ON DUPLICATE KEY UPDATE value = VALUES(value)'
   
      #####print( sql % (self.prefix, userID, cityID, paramID, tdate, bdate, value) )
      cur.execute( sql % (self.prefix, userID, cityID, paramID, tdate, bdate, value) )
      #####cur.execute( sql % (self.prefix, userID, cityID, paramID, tdate, bdate, value, 1) )


   # -------------------------------------------------------------------
   # - Insert or update the points 
   #   NOTE: the method inserts or updates the points. For normal 
   #   players we only have to update because the bets are allready
   #   places.
   #   For the deadman (has no bet values, only points) we need to
   #   set a default 'value' (bet value) because the database expects
   #   a value (no default value set for column value).
   # -------------------------------------------------------------------
   def upsert_points_data(self,userID,cityID,paramID,tdate,bdate,points):

      # - bdate is either a bet date (days since 1970-01-01) or
      #   an integer lower 5. If the second one is the case
      #   bdate = tdate+bdate to get days.
      if bdate <= 5: bdate = tdate + bdate
      cur = self.db.cursor()

      sql = 'INSERT INTO %swetterturnier_bets ' + \
            '(userID, cityID, paramID, tournamentdate, betdate, value, points) VALUES ' + \
            '(%d, %d, %d, %d, %d, %d, %f) ON DUPLICATE KEY UPDATE points = VALUES(points)'
            #####'(userID, cityID, paramID, tournamentdate, betdate, value, points, status) VALUES ' + \
            #####'(%d, %d, %d, %d, %d, %d, %f, %d) ON DUPLICATE KEY UPDATE points = VALUES(points)'
   
      cur.execute( sql % (self.prefix, userID, cityID, paramID, tdate, bdate, -999, points) )
      #####cur.execute( sql % (self.prefix, userID, cityID, paramID, tdate, bdate, -999, points, 1) )


   # -------------------------------------------------------------------
   # - Upsert wetterturnier_betstat table
   # -------------------------------------------------------------------
   def upsert_deadman_points(self,userID,cityID,tdate,points):

      sql = 'INSERT INTO %swetterturnier_betstat ' + \
            '(userID, cityID, tdate, points) VALUES ' + \
            '(%d, %d, %d, %f) ON DUPLICATE KEY UPDATE points = VALUES(points)'
      cur = self.db.cursor()
   
      cur.execute( sql % (self.prefix, userID, cityID, tdate, points) )


   # -------------------------------------------------------------------
   # - Loading bets. 
   # -------------------------------------------------------------------
   def get_obs_data(self,cityID,paramID,tdate,bdate,wmo=None):

      import numpy as np

      #   an integer lower 5. If the second one is the case
      #   bdate = tdate+bdate to get days.
      if bdate <= 5: bdate = tdate + bdate
      cur = self.db.cursor()

      # - 
      sql = 'SELECT o.value AS value FROM %swetterturnier_obs AS o ' + \
            'LEFT OUTER JOIN %swetterturnier_stations AS s ' + \
            'ON o.station = s.wmo ' + \
            'WHERE s.cityID = %d AND o.paramID = %d AND o.betdate = %d'
      if not wmo == None: sql += ' AND o.station = %d' % wmo

      #print sql % (self.prefix,self.prefix,cityID,paramID,bdate)
      cur.execute( sql % (self.prefix,self.prefix,cityID,paramID,bdate) )

      data = cur.fetchall()
      if not data:
         return False
      elif wmo == None:
         res = []
         for elem in data: res.append( elem[0] )
         return res
      else:
         return data[0][0]

   # -------------------------------------------------------------------
   # - Returning parameter ID
   #   Note: to compute the points we have to return ALL, also non-active
   #   ones because it is possible that you are re-computing an old
   #   date where they were used at that time. The point computation
   #   code will skip if there are no data.
   # -------------------------------------------------------------------
   def get_parameter_names(self, active = False):
      cur = self.db.cursor()
      if active:
         cur.execute('SELECT paramName FROM %swetterturnier_param WHERE active = 1' % self.prefix) 
      else:
         cur.execute('SELECT paramName FROM %swetterturnier_param' % self.prefix) 
      data = cur.fetchall()
      if not data:
         return False
      else:
         res = []
         for elem in data: res.append( elem[0] )
         return res


   # -------------------------------------------------------------------
   # - Returning parameter ID
   # -------------------------------------------------------------------
   def get_parameter_id(self,param):
      cur = self.db.cursor()
      cur.execute('SELECT paramID FROM %swetterturnier_param WHERE paramName = \'%s\'' % (self.prefix, param))
      data = cur.fetchone()
      if not data:
         return False
      else:
         return int(data[0])

   
   # -------------------------------------------------------------------
   # - Returns user id. And creates user if necessary.
   # -------------------------------------------------------------------
   def get_user_id_and_create_if_necessary(self, name):

      import utils
      userID = self.get_user_id( utils.nicename( name ) )
      if not userID:
          self.create_user( utils.nicename( name) )
      # - Now loading the newly crates userID
      userID = self.get_user_id( utils.nicename( name ) )
      if not userID:
          utils.exit('OOOH FUCK. Created new user for %s but resulting ID was None in get_user_id_and_create_user_if_necessary.' % name )

      # - Return the id
      return userID
      

   # -------------------------------------------------------------------
   # - Returning user ID
   # -------------------------------------------------------------------
   def get_user_id(self,user):
      cur = self.db.cursor()
      cur.execute('SELECT ID FROM %susers WHERE LOWER(user_login) = \'%s\'' % (self.prefix, user.lower()))
      data = cur.fetchone()
      if not data:
         return False
      else:
         return int(data[0])

   # -------------------------------------------------------------------
   # - Returning username corresponding to the ID
   #   More explicitly: return user_login from the database.
   # -------------------------------------------------------------------
   def get_username_by_id(self,userID):
      try:
         userID = int(userID)
      except:
         utils.exit('Got wrong input to get_username_by_id. Was no integer!')
      cur = self.db.cursor()
      cur.execute('SELECT user_login FROM %susers WHERE ID = %d' % (self.prefix, userID))
      data = cur.fetchone()
      if not data:
         return False
      else:
         return str(data[0])




   # -------------------------------------------------------------------
   # - Returning active groups 
   # -------------------------------------------------------------------
   def get_active_groups(self):
      cur = self.db.cursor()
      sql = 'SELECT groupName FROM %swetterturnier_groups WHERE active = 1'
      cur.execute(sql % self.prefix)
      data = cur.fetchall()

      # - Make nice list
      res = [];
      for elem in data: res.append(elem[0])

      return res

   # -------------------------------------------------------------------
   # - Returning user ID
   # -------------------------------------------------------------------
   def get_group_id(self,group):
      cur = self.db.cursor()
      sql = 'SELECT groupID FROM %swetterturnier_groups WHERE groupName = \'%s\''
      cur.execute(sql % (self.prefix, group))
      data = cur.fetchone()
      if not data:
         return False
      else:
         return int(data[0])


   # -------------------------------------------------------------------
   # - Create a groupuser (add user to group as a member)
   # -------------------------------------------------------------------
   def create_groupuser(self, user, group, since, active ):
   
      uID = self.get_user_id( user )
      gID = self.get_group_id( group )

      if not uID:
         utils.exit('Problems loading userID for %s' % (user))
      if not gID:
         utils.exit('Problems loading groupID for %s' % (group))

      # - Check if groupuser is currently active in db
      c_sql = 'SELECT count(*) FROM %swetterturnier_groupusers ' + \
              'WHERE userID = %d AND groupID = %d AND active = 1 '
      cur = self.db.cursor()
      cur.execute( c_sql % (self.prefix, uID, gID) )
      
      if cur.fetchone()[0] > 0:
         print '    GroupUser allready active/existing.'
      else:
         print '    Created groupuser %s|%s' % (user,group)
         i_sql = 'INSERT INTO %swetterturnier_groupusers ' + \
                 '(userID, groupID, since, active) VALUES ' + \
                 '(%d, %d, \'%s\', %d)'
         cur.execute( i_sql % (self.prefix, uID, gID, since, active) )
         self.db.commit()

   # -------------------------------------------------------------------
   # - Compute mean or std points for a city/tdate/day/parameter. 
   #   NOTE: ignore is a userID, the userID from the deadman.
   #   We will NOT include the deadman into the computation. This would
   #   lead to an iterative process!
   #   Furthermore we have to exclude the groups by excluding all
   #   users with usernames beginning with 'GRP_'.
   # -------------------------------------------------------------------
   def get_deadman_points(self,cityID,tdate,ignore):

      cur = self.db.cursor()
      #sql = 'SELECT b.betdate, b.paramID, AVG(b.points) - STD(b.points) AS points ' + \
      #      'FROM %swetterturnier_bets AS b LEFT OUTER JOIN %susers AS u ' + \
      #      'ON b.userID = u.ID ' + \
      #      'WHERE cityID = %d AND tournamentdate = %d AND userID != %d ' + \
      #      'AND u.user_login NOT LIKE \'%s\' ' +  \
      #      'GROUP BY betdate, paramID'
      sql = 'SELECT (CASE WHEN b.points IS NULL THEN 0 ELSE 1 END ) AS points ' + \
            'FROM %swetterturnier_betstat AS b LEFT OUTER JOIN %susers AS u ' + \
            'ON b.userID = u.ID ' + \
            'WHERE cityID = %d AND tdate = %d AND userID != %d '
      cur.execute( sql % ( self.prefix, self.prefix,cityID,tdate,ignore) )
      data = cur.fetchall()
      if not data:
         return False
      else:
         return data


   # ----------------------------------------------------------------
   # - Close the database 
   # ----------------------------------------------------------------
   def close(self,verbose=True):

      if verbose: print '  * Close database'
      self.db.close()
