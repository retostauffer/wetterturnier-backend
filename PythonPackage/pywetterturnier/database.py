# -------------------------------------------------------------------
# - NAME:        database.py
# - AUTHOR:      Reto Stauffer
# - DATE:        2014-09-13
# -------------------------------------------------------------------
# - DESCRIPTION: Database class handling the database connection.
# -------------------------------------------------------------------
# - EDITORIAL:   2014-09-13, RS: Created file on thinkreto.
# -------------------------------------------------------------------
# - L@ST MODIFIED: 2018-12-16 11:49 on marvin
# -------------------------------------------------------------------

import pymysql as MySQLdb
#import MySQLdb
#import mysqlclient
from . import utils

#move to class?
def sql_tuple(IDs, strings=False):
   """Format a list of integers (IDs) to a tuple fitting the SQL IN(...) statement"""
   if not hasattr(IDs, '__len__') and type(IDs) == int:
      sql_str = "("+str(IDs)+")"
   elif len(IDs) in [0,1]:
      IDs = list(IDs)
      if len(IDs) == 0:
         IDs.append(0)
      sql_str = str(tuple(IDs))[0:-2]+")"
   else: sql_str = str(tuple(IDs))
   if strings:
      sql_str = sql_str.replace("'","")
      sql_str = sql_str.replace("(","")
      sql_str = sql_str.replace(")","")
   return sql_str

class database(object):
   """This is the main database handler class.
   As soon as an object of this class is initialized python automatically
   (tries) to connect to the database. The database class offers a bunch
   of methods to get/write data into the databae. Not all commands are
   in this class, some SQL statements are defined within the other
   classes and methods.
   Please see :py:meth:utils.readconfig for more details about the config object.

   Args:
     config (:py:meth:`utils.readconfig`): Database handler
   """
   # ----------------------------------------------------------------
   # ----------------------------------------------------------------
   def __init__(self,config):

      """The database class is handling the connection to the
      mysql database and different calls and stats.
      """

      self.config = config
      self.db = self.__connect__()

      self.prefix = self.config['mysql_prefix']

   #import outsourced statistic and moses functions
   from .stats import compute_stats, get_stats, upsert_stats
   from .moses import get_moses_coefs, upsert_moses_coefs

   def sql_tuple(self, IDs, strings=False):
      """Format a list of integers (IDs) to a tuple fitting the SQL IN(...) statement"""
      if not hasattr(IDs, '__len__') and type(IDs) == int:
         sql_str = "("+str(IDs)+")"
      elif len(IDs) in [0,1]:
         IDs = list(IDs)
         if len(IDs) == 0:
            IDs.append(0)
         sql_str = str(tuple(IDs))[0:-2]+")"
      else: sql_str = str(tuple(IDs))
      if strings:
         sql_str = sql_str.replace("'","")
         sql_str = sql_str.replace("(","")
         sql_str = sql_str.replace(")","")
      return sql_str


   # ----------------------------------------------------------------
   # ----------------------------------------------------------------
   def get_participants_in_group(self,groupID,cityID,tdate,playing=True):
      """Active players in a specific group.
      Getting active players from a certain group for a certain
      city and weekend.

      Args:                                                                                                        
         groupID (:obj:`int`): ID of the group.
         cityID  (:obj:`int`): ID of the current city.
         tdate   (:obj:`int`): tournament date as integer representation.

      Returns:
         list: List containing the user ID's of the players from
         that specific group who were participating in the tournament for
         the city given. Can be a list of length 0 as well.
      """
      cur = self.cursor()
      if not playing:
         sql = "SELECT userID FROM %swetterturnier_groupusers WHERE groupID=%d"
         cur.execute( sql % ( self.prefix, groupID ) )
      else:
         from datetime import datetime as dt
         fmt = "%Y-%m-%d %H:%M:%S"
         bgn = dt.fromtimestamp(tdate).strftime(fmt)
         end = dt.fromtimestamp(tdate+1).strftime(fmt)

         #TODO should be safe from SQL injection
         #problem is: console sometimes prints \n or \ which causes SQL injection save variant below to fail
         sql = f"""
            SELECT
               gu.userID
            FROM
               {self.prefix}wetterturnier_groupusers AS gu
            LEFT OUTER JOIN
               {self.prefix}wetterturnier_betstat AS bet
            ON
               gu.userID=bet.userID
            WHERE
               groupID = {groupID} AND tdate = {tdate}
            AND
               bet.cityID = {cityID}
            AND
               (gu.until IS NULL OR (gu.since > '{bgn}' AND gu.until < '{end}'))
            AND
               bet.submitted IS NOT NULL
         """
         #var = 2 * [ self.prefix ] + [ groupID, tdate, cityID, bgn, end ]
         #print( sql.format(**{"self.prefix":self.prefix, "tdate":tdate, "groupID":groupID, "cityID":cityID, "bgn":bgn, "end":end }) )
         #print( sql % tuple(var) ) 
         #cur.execute( sql, {"self.prefix":self.prefix, "groupID":groupID, "cityID":cityID, "bgn":bgn, "end":end } )
         cur.execute( sql )

      return [int( i[0] ) for i in cur.fetchall()]

   # ----------------------------------------------------------------
   # ----------------------------------------------------------------
   def __connect__(self):
      """Open database connection.
      In case python is not able to open the database connection
      the script will stop immediately.
      Returns:
          MySQLdb: Database handler object.
      """

      print('  * Establishing database connection')
      host   = self.config['mysql_host']
      user   = self.config['mysql_user']
      passwd = self.config['mysql_pass']
      db     = self.config['mysql_db']
      port   = self.config['mysql_port']
      try:
         res = MySQLdb.connect(host=host,user=user,password=passwd,database=db,port=port)
      except Exception as e:
         print(e)
         utils.exit("Could not connect to the database. Stop.")
      return res


   # ----------------------------------------------------------------
   # Convenient helper functions to MySQLdb.
   # ----------------------------------------------------------------
   def cursor(self):
      """Simple wrapper to `MySQL.cursor`
      
      Returns:
          MySQLdb.curser: Object, database cursor.
      """
      return self.db.cursor()
   def execute(self,sql):
      """Simple wrapper to `MySQL.execute`
      
      Args:
           sql (string): SQL statement to be executed.
      Returns:
           tuple: Return from `MySQLdb.execute`.
      """
      return self.db.execute(sql)
   def executemany(self,sql,data):
      """Simple wrapper to `MySQL.executemany`.

      Args:
         sql  (:obj:`str`): MySQL query statement.
         data (:obj:`tuple` or :obj:`list`): Object to be forwarded to `MySQL.executemany`.

      Returns:
         Return from :meth:`MySQLdb.executemany`.
      """
      return self.db.executemany(sql,data)
   def commit(self):
      """Simple wrapper to :meth:`MySQL.commit`."""
      self.db.commit()


   # ----------------------------------------------------------------
   # - Check if table exists
   # ----------------------------------------------------------------
   def check_if_table_exists(self,table):
      """Checks wheter a table exists in the database. Note that the
      table name is the table name without prefix! For example: if you
      wanna check whether wp_users exists the the variable tablename
      has to be 'users' only. The prefix is used as specified in the
      config file.

      Args:
         table (:obj:`str`): Table name **without** prefix.
      Returns:
         bool: True if table exists, False if not.
      """
      cur = self.db.cursor()
      sql = "SELECT count(*) FROM information_schema.tables WHERE " + \
            "table_schema = '{0:s}' AND table_name = '{1:s}{2:s}';".format(
            self.config['mysql_db'],self.config['mysql_prefix'],table)
      cur.execute(sql)
      res = cur.fetchone()
      if int( res[0] ) == 0:
         return False
      else:
         return True


   # ----------------------------------------------------------------
   # - Create a group
   # -------------------------------------------------------------------
   def create_group(self, name, desc ):
      """Checks and/or creates group.   
      Checks the Wetterturnier database table ``groups`` and checks if
      the group is already existing. If existing, the job of this method
      is done. Else a new group will be created.
      Used for the migration of the groups in the old Wetterturnier archive.

      Args:
         name (:obj:`str`): Group name.
         desc (:obj:`str`): Group description.
      """ 
   
      c_sql = 'SELECT count(*) FROM %swetterturnier_groups WHERE ' + \
              'groupName =\'%s\''
      i_sql = 'INSERT INTO %swetterturnier_groups ' + \
              '(groupName, groupDesc, active) VALUES (\'%s\', \'%s\', 1)'
   
      # - Check if allready existing
      cur = self.db.cursor()
      cur.execute( c_sql % (self.prefix,name) )
      N = cur.fetchone()[0]
      if N > 0:
         print('    Group %s already existing.' % name)
         return

      # - Create group
      print('    Group %s created.' % name)
      cur.execute( i_sql % (self.prefix,name,desc) )
      self.db.commit()


   # -------------------------------------------------------------------
   # - Create a user
   # -------------------------------------------------------------------
   def create_user(self, name, password = None ):
      """Check and/or create new Wetterturnier user.
      Creates a new user. If user already exists, the job of this method is
      done. Return. If not, create new user.

      Please note: if a user does not exist this script creates a small php
      script and executes the php via console. This php script creates the
      new user via wordpress API.

      As we are using wordpress we have to take care
      how we are creating users. To be on the save side I am using the wordpress
      internal function to add a user. 
      Therefore a temporary php file will be created containing the necessary
      lines of code calling wp_create_user (in php) to add the user.
      The php file then will be called using the local php interpreter.
      After doing that the script is using @ref database.get_user_id to check
      if the user was added propperly. If not: stop.

      Args:
         name (:obj:`str`): User name. 
         password (:obj:`str`, optional): If set to None the user wont get a password (actually
         I *have to set* a password, in this case the user password is just its user name
         backwards. E.g., Reto gets paswort oteR.
      """

      import os
      from . import utils


      # - If wpconfig is missing we cannot create the new user.
      #   In this case, stop. This is just for the development
      #   server.
      # - If the file wp-config.php does not exist, stop.
      if not os.path.isfile( self.config['migrate_wpconfig'] ):
         utils.exit('Sorry, {0:s} does not exist. Stop. Necessary to create wp users'.format(
                     self.config['migrate_wpconfig']))

      
   
      # - If name length is equal to zero, stop too.
      if len(name.strip()) == 0:
         utils.exit('BUMM got empty username for database.create_user')
   
      # - Check if allready existing
      sql = 'SELECT count(*) FROM %susers WHERE ' + \
              'user_login =\'%s\''
      cur = self.db.cursor()
      cur.execute( sql % (self.prefix, name) )
      N = cur.fetchone()[0]
      if N > 0:
         print('    User %s already existing.' % name)
         return

      # - Python wants to create a new user. We do not allow him
      #   this here (depends on the config file). Stop and print
      #   some output to check.
      devel_allow = []
      if not self.config['allow_create_users'] and not name in devel_allow:
         print(" ---- SCRIPT WANTED TO CREATE A USER BUT IS NOT ALLOWED (config) ----")
         print("                     Username:   %s" % name)
         import sys;
         sys.exit(9)

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
      print('    Create php file to create the user')
      phpfile = '%s/create_user.php' % self.config['rawdir']
      fid = open( phpfile,'w+');
      fid.write( '\n'.join( str ) )
      fid.close()

      print('    Calling php file now ...')
      print(' ---------------------------- ')
      os.system('cat %s' % phpfile)
      print(' ---------------------------- ')
      os.system('php %s' % phpfile)

      userID = self.get_user_id( name )
      if not userID:
         utils.exit('OH DEAR, CREATED USER BUT GOT NO userID IN RETURN')




   # -------------------------------------------------------------------
   # - Getting dict containing all active cities in the database. 
   # -------------------------------------------------------------------
   def get_cities(self, sort=True, active=True ):
      """Loading city information from the database.
      Loads all active cities from the database which can then be used
      to loop over or whatever you'll do with it. 

      Args:
         sort (:obj:`bool`): True if the cities should be sorted by their cityID.
         active (:obj:`bool`): True if only active cities should be shown.

      Returns:
         list: A list containing one dict per city where each dict
         consists of the keys 'name', 'hash' and 'ID'.
   
      .. todo:: Would be nice to return cityclass objects or something. However,
         needs some effort as I have to change a few lines of code.
      """

      #print '  * %s' % 'looking active cities'
      sql = 'SELECT * FROM %swetterturnier_cities'
      if active: sql += ' WHERE active = 1'
      if sort: sql+=' ORDER BY ID'

      cur = self.cursor()
      cur.execute( sql % self.prefix )
      data = cur.fetchall()

      if len(data) == 0:
         utils.exit('Cannot load city data from database in database.current_tournament')
      
      return [ { 'ID' : int(i[0]), 'name' : str(i[1]), 'hash' : str(i[2]) } for i in data]

   def get_city_names(self):
      """Loading city information from the database.
      Loads all names of currently active cities from the database. 

      Returns:
         list: A list containing the names of all active cities.
      """

      print('  * %s' % 'looking active cities')
      sql = 'SELECT name FROM %swetterturnier_cities WHERE active = 1 ' + \
            'ORDER BY ID'

      cur = self.cursor()
      cur.execute( sql % self.prefix )
      data = cur.fetchall()

      if len(data) == 0:
         utils.exit('Cannot load city data from database in database.current_tournament')
      
      return [i[0] for i in data]

   # -------------------------------------------------------------------
   # - Loading stations from database for a given city
   # -------------------------------------------------------------------
   def get_stations_for_city(self,cityID,active=True,tdate=False):
      """Loading all stations mached to a certain city.

      Args:
         cityID (:obj:`int`): ID of the city in the database.

      Returns:
         list: List object containing `N` :py:obj:`stationclass.stationclass` objects.
      """

      sql = "SELECT * FROM %swetterturnier_stations WHERE cityID = %d" % (self.prefix,cityID)
      if active: sql += " AND active = 1"
      if tdate:
         sql += f" AND (since<={tdate} OR since=0) AND (until>{tdate} OR until=0)"
      cur = self.db.cursor()
      cur.execute( sql )
      desc = cur.description

      from .stationclass import stationclass

      res = [stationclass( desc, i, self.db, self.config["mysql_prefix"] ) for i in cur.fetchall()]

      print(res)
      return res

   # -------------------------------------------------------------------
   # - Current tournament
   # -------------------------------------------------------------------
   def current_tournament(self, verbose=False, active=False):
      """Returns tdate for current tournament.
      The tdate is the number of days since 1970-01-01. Loading the
      ``max(tdate)`` from the dates table which is smaller than the
      current date (utcnow).

      Return:
         int: Integer date (days since 1970-01-01)

      .. todo:: Reto just take care of the idea that we could start two tournaments
         in a row. Can this method then handle the requests?
      """

      import numpy as np
      import datetime as dt

      if verbose: print('  * %s' % 'Searching current tournament date')
      today = int(np.floor(float(dt.datetime.now().strftime("%s"))/86400))
      if verbose: print(today)
      sql = 'SELECT max(tdate) FROM %swetterturnier_dates WHERE tdate <= %d'
      if active: sql += ' AND status = 1'
      cur = self.cursor()
      cur.execute( sql % (self.prefix ,today) )
      tdate = cur.fetchone()[0]

      if verbose: print(f'    Current tournament date is: {tdate:d}')

      return tdate


   # -------------------------------------------------------------------
   # - Get all tournament dates 
   # -------------------------------------------------------------------
   def all_tournament_dates(self,cityID=None):
      """Returns all defined tournament dates ever played in a city.
      Searches for all unique tournament dates in the bets table and
      returns them as a list.

      Args:
         cityID (:obj:`int`): ID of the city. If NONE all dates of all 
         cities (unique) will be returned.

      Returns:
         each element represents one tournament played for the city. Dates in
         days since 1970-01-01.
      """

      if not cityID:
         print('  * Loading all available tournament dates')
         sql = 'SELECT tdate FROM %swetterturnier_bets GROUP BY tdate' % \
               self.config['mysql_prefix']
      else:
         print('  * %s' % 'Searching all tournament dates for city %d' % cityID)
         sql = 'SELECT tdate FROM %swetterturnier_bets WHERE cityID = %d GROUP BY tdate' % \
               (self.config['mysql_prefix'] ,cityID)

      ## - DEVELOPMENT: ONLY DATES 2015+
      #print "[!] RETO: DEVELOPMENT IN all_tournament_dates YOU ARE ONLY"
      #print "    PICKING DATES 2015+ AND NOT ALL ..."
      #sql = 'SELECT tdate FROM %swetterturnier_bets ' + \
      #      'WHERE cityID = %d AND tdate > 16436 GROUP BY tdate'

      cur = self.cursor()
      cur.execute( sql )
      tdates = [int(i[0]) for i in cur.fetchall() if i[0]]
      print('    Found %d different dates' % len(tdates))

      tdates.sort()
      return tdates

   # -------------------------------------------------------------------
   # - Given an ID this method returns the city name.
   # -------------------------------------------------------------------
   def get_city_name_by_ID(self,cityID):
      """Returns the full city name given a valid cityID. If the city
      cannot be found in the database False will be returned.
      
      Args:
         cityID (:obj:`int`): Numeric city ID.

      Returns
         str: City name (:obj:`str`) or False (:obj:`bool`) if the city could
         not be found in the database.
      """
      sql = "SELECT name FROM {0:s}{1:s} WHERE ID = {2:d}".format(self.config['mysql_prefix'],"wetterturnier_cities",cityID)
      cur = self.cursor(); cur.execute(sql)
      res = cur.fetchone()
      if len(res) == 0: return False
      return str(res[0])

   # -------------------------------------------------------------------
   # - Opposite of above function
   # -------------------------------------------------------------------
   def get_city_ID_by_name(self,city):
      """Returns the city ID by a given name or hash, both is accepted
      Args:
         city (:obj:`str`): Name or 3 letter hash of city
      Returns
         int: City ID (:obj:`int`): Numeric city ID or False (:obj:`bool`) if the city name or hash could
         not be found in the database.

      """
      sql = "SELECT ID FROM {0:s}{1:s} WHERE name = {2:s} OR hash = {2:s}".format(self.config['mysql_prefix'],"wetterturnier_cities",city)
      cur = self.cursor(); cur.execute(sql)
      res = cur.fetchone()
      if not res: return False
      else: return int(res[0])
   
   # -------------------------------------------------------------------
   # - Returns all bets for a given tdate and
   #   a parameter. Returns ID and values. That's what we need
   #   to compute and store the points. Returns two lists with ID and values.
   #   This will be used by the judgingclass to compute the points.
   # -------------------------------------------------------------------
   def get_cityall_bet_data(self,cityID,paramID,tdate,day,nosleepy=True,nullonly=False):
      """Returns bets for a given city/parameter/date/day.
      Returns all bets for a given city, parameter for a given bet day of a specified
      tournament. Note that there is no userID. This method returns the bets for all 
      users.

      Args:
         cityID (:obj:`int`):  Numeric ID of the city.
         paramID (:obj:`int`): Integer, parameter ID.
         tdate (:obj:`int`)    tournament date (if tournament starts on Friday, this is
                               date of this friday). Days since 1970-01-01.
         day (:obj:`int`): [1/2] where 1 means tdate+1 (leading to a Saturday if
                               tdate is a Friday). 2 means Sunday. Value between 0 and 5, however, only
                               1 and 2 are useful as we do not have bets for the other days. 
      Returns:
         Returns a set of lists containing the 'unique key identifier' for
         the database and the 'value' to update the database.  
         Namely: userID, cityID, paramID, tdate, betdate and values.
      """

      # - If day is smaller equal 6 then the betdate
      #   is tdate + day. Else day == betdate
      if day <= 6:
         betdate = tdate + day
      else:
         betdate = day

      cur = self.db.cursor()
      sql = 'SELECT userID, cityID, paramID, tdate, betdate, value FROM %swetterturnier_bets ' + \
            'WHERE cityID = %d AND paramID = %d AND betdate = %d AND ' + \
            'tdate = %d'

      # - If there is a userID on self.config['input_user']:
      #   only return the data for this user!
      if type(self.config['input_user']) == int:
         sql += ' AND userID = %d' % self.config['input_user']

      # - Only compute points where points are NULL
      #   in the database
      if nullonly:
         sql += ' AND points IS NULL '

      if nosleepy:
         deadID = self.get_user_id('Sleepy')
         sql += ' AND userID != %d ' % deadID
      cur.execute( sql % (self.prefix, cityID, paramID, betdate, tdate) )
      #####cur.execute( sql % (self.prefix, cityID, paramID, betdate, tdate, 1) ) 

      data = cur.fetchall()
      if not data or len(data) == 0:
         return False, False
      else:
         # Elements required for the unique key (for the update)
         userID, cityID, paramID, tdate, betdate, values = [[] for _ in range(6)]
         for i in data:
            userID.append(  int( i[0] ))
            cityID.append(  int( i[1] ))
            paramID.append( int( i[2] ))
            tdate.append(   int( i[3] ))
            betdate.append( int( i[4] ))
            values.append(  int( i[5] ))
         return userID, cityID, paramID, tdate, betdate, values

   # -------------------------------------------------------------------
   # - Loading bets. 
   # -------------------------------------------------------------------
   def get_bet_data(self,typ,ID,cityID,paramID,tdate,bdate):
      """Returns bet data used to compute e.g., Petrus.
      Returns a set of bets for a given city, parameter, and bet date for a specified
      tournament date. Note: has different modes.

      Args:
         typ (:obj:`str`):  If ``typ == 'all'``: all users (human forecasters, automated forecasters and
                            group bets) **EXCLUDING** the Sleepy will be returned.
                            If ``type == 'user'`` the bet of a specific user will be returned.
                            If ``type == 'group'`` the bet of a specific group will be returned.
                            User or group (if type == 'user' or 'group') are defined by the input argument ID
                            which is the userID or the groupID.
        
         typ (:obj:`str`):     Any of type ``'all'``, ``'user'``, or ``'group'``.
         ID (:obj:`int`):      Ignored when ``type = 'all'``. Else the input has to be of type ineger
                               defining the userID (for ``type = 'user'``) or groupID (for ``type = 'group'``).
         cityID (:obj:`int`):  Numeric ID of the city.
         paramID (:obj:`int`): Numeric parameter ID.
         tdate (:obj:`int`):   Tournament date (if tournament starts on Friday, this is
                               the date of this Friday). Days since 1970-01-01.
         betdate (:obj:`int`): If value is lower equal 6: assume that the real betdate
                               is tdate + betdate (1: next day, 2: two days ahead, ...). If betdate is bigger
                               than 6 betdate is just taken as set. 

      Returns:
         list: Returns a list containing all the bets.

      .. todo:: Reto the sleepy does not get bets - he just gets points. Maybe I can
         disable/remove the 'all' function if I am not using it anymore.
      """

      import numpy as np

      # - Typ is either "all" for Petrus (takes all human bets),
      #   "user" to get the bet of one user (ID = userID), or
      #   "group" to get the bets for a group (ID = groupID)
      l = ['persistenz','all','user','group','human','petrus','mswr']
      if not typ in l:
         utils.exit('Wrong typ input to database.get_bet_data. Has to be all, user, or group')
      
      if typ == 'persistenz':
         # - actually not getting bet - but obs data instead, for 1 day
         
         data = self.get_obs_data(cityID,paramID,tdate,tdate)

         if not data or len(data) == 0:
            return False
         else:
            res = np.ndarray( len(data), dtype='float' )
            for i in range(len(data)):
               res[i] = float(data[i])
            return res
      
      # - bdate is either a bet date (days since 1970-01-01) or
      #   an integer lower equal 6. If the second one is the case
      #   bdate = tdate+bdate to get days.
      if bdate <= 6: bdate = tdate + bdate
      cur = self.db.cursor()

      # - Ignore the sleepy!
      deadID = self.get_user_id('Sleepy')

      # - For averaged bets, load all bets for a given tdate/betdate, city and parameter.
      
      if typ == 'all': 
         # - Also ignore Referenztipps. They look like players but they
         #   should not be included into mitteltips. Else Persistenz
         #   is included into the computation of the Persistenz.
         ref = self.get_group_id('Referenztipps')
         cur.execute( 'SELECT userID FROM %swetterturnier_groupusers WHERE groupID = %d' % (self.prefix, ref) )
         ref = [int(i[0]) for i in cur.fetchall()]
         # - Create final statement
         sql = []
         sql.append("SELECT bet.value AS value FROM %swetterturnier_bets AS bet" % self.prefix)
         sql.append("LEFT OUTER JOIN %susers AS usr" % self.prefix)
         sql.append("ON bet.userID = usr.ID")
         sql.append("INNER JOIN %swetterturnier_betstat AS stat" % self.prefix)
         sql.append("ON bet.userID=stat.userID AND bet.cityID=stat.cityID AND bet.tdate=stat.tdate")
         sql.append("WHERE usr.user_login NOT LIKE \"%s\"" % "GRP_%")
         sql.append("AND bet.cityID = %d AND bet.paramID = %d" % (cityID,paramID))
         sql.append("AND bet.tdate = %d AND bet.betdate = %d" % (tdate,bdate))
         sql.append("AND bet.userID != %d" % deadID)
         sql.append("AND bet.userID NOT IN%s" % sql_tuple(ref))
         #print("\n".join(sql))
         cur.execute( "\n".join(sql) )
      # - If input was user, load tips for a specific user.
      elif typ == 'user':
         # - Create sql statement 
         sql = []
         sql.append("SELECT bet.value AS value FROM %swetterturnier_bets AS bet" % self.prefix)
         sql.append("INNER JOIN %swetterturnier_betstat AS stat" % self.prefix)
         sql.append("ON bet.userID=stat.userID AND bet.cityID=stat.cityID AND bet.tdate=stat.tdate")
         sql.append("WHERE bet.userID = %d" % ID) 
         sql.append("AND bet.cityID = %d AND bet.paramID = %d" % (cityID,paramID))
         sql.append("AND bet.tdate = %d AND bet.betdate = %d" % (tdate,bdate))
         #print("\n".join( sql ))
         cur.execute( "\n".join(sql) ) 
      # - If input was user, load tips for a specific user.
      elif typ == 'group':
         sql = 'SELECT v.value AS value FROM %swetterturnier_bets AS v ' + \
                     'LEFT OUTER JOIN %swetterturnier_groupusers AS gu ' + \
                     'ON v.userID = gu.userID ' + \
                     'WHERE gu.groupID = %d ' + \
                     'AND v.cityID = %d AND v.paramID = %d ' + \
                     'AND v.tdate = %d AND v.betdate = %d '
         sql = []
         sql.append("SELECT bet.value AS value FROM %swetterturnier_bets AS bet" % self.prefix)
         sql.append("LEFT OUTER JOIN %swetterturnier_groupusers AS gu" % self.prefix)
         sql.append("ON bet.userID = gu.userID")
         sql.append("INNER JOIN %swetterturnier_betstat AS stat" % self.prefix)
         sql.append("ON bet.userID=stat.userID AND bet.cityID=stat.cityID AND bet.tdate=stat.tdate")
         sql.append("WHERE gu.groupID = %d" % ID) 
         sql.append("AND bet.cityID = %d AND bet.paramID = %d" % (cityID,paramID))
         sql.append("AND bet.tdate = %d AND bet.betdate = %d" % (tdate,bdate))

         # Now we have to ensure that the players where active during these days
         # in this group
         from datetime import datetime as dt
         # Convert tdate into 'YYYY-mm-dd HH:MM:SS'
         strdate_bgn = dt.fromtimestamp(tdate*86400).strftime("%Y-%m-%d 00:00:00")
         strdate_end = dt.fromtimestamp((tdate+1)*86400).strftime("%Y-%m-%d 00:00:00")
         sql.append("AND (gu.since IS NULL OR gu.since < '{0:s}') AND (gu.until IS NULL OR gu.until >= '{1:s}')".format(
                    strdate_end,strdate_bgn))
         #print("\n".join(sql))

         # Execute query
         cur.execute( "\n".join(sql) ) 
      elif typ == 'human' or typ == 'petrus':
         # - get only human players, no sleepy no groups, no automats, no reference tips
         # - look for Petrus, Moses and Persistenz ID to exclude them:
         PetrusID = self.get_user_id('Petrus')
         MosesID = self.get_user_id('Moses')
         if typ == 'human':
            DonnerstagID = self.get_user_id('Donnerstag')
            FreitagID    = self.get_user_id('Freitag')
         # - Create statement
         sql = []
         sql.append("SELECT bet.value AS value FROM %swetterturnier_bets AS bet" % self.prefix)
         sql.append("LEFT OUTER JOIN %susers AS usr" % self.prefix)
         sql.append("ON bet.userID = usr.ID")
         sql.append("INNER JOIN %swetterturnier_betstat AS stat" % self.prefix)
         sql.append("ON bet.userID=stat.userID AND bet.cityID=stat.cityID AND bet.tdate=stat.tdate")
         sql.append("WHERE usr.user_login NOT LIKE \"%s\"" % "GRP_%")
         sql.append("AND bet.cityID = %d AND bet.paramID = %d" % (cityID,paramID) )
         sql.append("AND bet.tdate = %d AND bet.betdate = %d" % (tdate,bdate) )
         if typ == 'human':
            ref = self.get_group_id('Automaten')
            cur.execute( 'SELECT userID FROM %swetterturnier_groupusers WHERE groupID = %d' % (self.prefix, ref) )
            mosIDs = [str(i[0]) for i in cur.fetchall()]
            try: mosIDs = "," + ",".join(mosIDs)
            except: mosIDs = ""

            sql.append("AND bet.userID NOT IN (%d,%d,%d,%d,%d%s)" % (deadID,PetrusID,MosesID,DonnerstagID,FreitagID,",".join(mosIDs)) )
         else:
            sql.append("AND bet.userID NOT IN (%d,%d,%d)" % (deadID,PetrusID,MosesID))
         #print("\n".join(sql))
         cur.execute( "\n".join(sql) )
      
      # MSwr: get GFS and EZ bets to compute the mix
      elif typ == "mswr":
         EZ  = self.get_user_id('MSwr-EZ-MOS')
         GFS = self.get_user_id('MSwr-GFS-MOS')
         sql = f"SELECT bet.value AS value FROM {self.prefix}wetterturnier_bets AS bet "
         sql+= f"LEFT OUTER JOIN {self.prefix}users AS usr "
         sql+= f"ON bet.userID = usr.ID "
         sql+= f"INNER JOIN {self.prefix}wetterturnier_betstat AS stat "
         sql+= f"ON bet.userID=stat.userID AND bet.cityID=stat.cityID AND bet.tdate=stat.tdate "
         sql+= f"WHERE bet.cityID = {cityID} AND bet.paramID = {paramID} "
         sql+= f"AND bet.tdate = {tdate} AND bet.betdate = {bdate} AND bet.userID IN ({EZ},{GFS}) "
         sql+= f"ORDER BY bet.userID DESC"
         #print(sql)
         cur.execute(sql)

      # - Else ... adapt the exit condition above please.
      else:
         utils.exit('Seems that you allowed another type in database.get_bet_data but you have not created a propper rule')


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
      """Helper function to update the bets database.
      Upserts the bets database setting a new 'value' for a given player.

      Args:
         userID   (:obj:`int`): User ID.
         cityID   (:obj:`int`): City ID.
         paramID  (:obj:`int`): Parameter ID.
         tdate    (:obj:`int`): Tournament date. Days since 1970-01-01.
         betdate  (:obj:`int`): Bet (forecast) date. Days since 1970-01-01.
         value    (:obj:`int`): Bet/forecast value. Note that the value has to be scaled
                                already as we store e.g. temperature in 1/10th of degrees celsius. 
      """

      # - bdate is either a bet date (days since 1970-01-01) or
      #   an integer lower equal 6. If the second one is the case
      #   bdate = tdate+bdate to get days.
      if bdate <= 6: bdate = tdate + bdate
      cur = self.db.cursor()

      sql = 'INSERT INTO %swetterturnier_bets ' + \
            '(userID, cityID, paramID, tdate, betdate, value) VALUES ' + \
            '(%d, %d, %d, %d, %d, %d) ON DUPLICATE KEY UPDATE ' + \
            'value = IF ( placedby = 0, VALUES(value), value );'
   
      cur.execute( sql % (self.prefix, userID, cityID, paramID, tdate, bdate, value) )

      # # Rowcount (affected rows)
      # rowcount = cur.rowcount
      # if rowcount == 0:
      #     print "      [!] Not updated (same value or admin lock)"

      # Setting the betstat entry
      sql = 'INSERT INTO %swetterturnier_betstat ' + \
            '(userID, cityID, tdate, updated, submitted) VALUES ' + \
            '(%d, %d, %d, "%s", "%s") ON DUPLICATE KEY UPDATE ' + \
            'updated = VALUES(updated)'

      from datetime import datetime as dt
      now = dt.now().strftime("%Y-%m-%d %H:%M:%S")
      cur.execute( sql % (self.prefix, userID, cityID, tdate, now, now) )


   # -------------------------------------------------------------------
   # - Insert or update the points 
   #   NOTE: the method inserts or updates the points. For normal 
   #   players we only have to update because the bets are already
   #   placed.
   #   For the sleepy (has no bet values, only points) we need to
   #   set a default 'value' (bet value) because the database expects
   #   a value (no default value set for column value).
   # -------------------------------------------------------------------
   def upsert_points_data(self,userID,cityID,paramID,tdate,bdate,points):
      """Helper function to update the bets database.
      Upserts the bets database updating the points for a given player. 
      This is for the payers. They get points for each of the parameters.

      Args:
         userID   (:obj:`int`):   user ID.
         cityID   (:obj:`int`):   City ID.
         paramID  (:obj:`int`):   Parameter ID.
         tdate    (:obj:`int`):   Tournament date. Days since 1970-01-01.
         betdate  (:obj:`int`):   Bet (forecast) date. Days since 1970-01-01.
         points   (:obj:`float`): Points the player got for that specific entry.
      """

      # - bdate is either a bet date (days since 1970-01-01) or
      #   an integer lower equal 6. If the second one is the case
      #   bdate = tdate+bdate to get days.
      if bdate <= 6: bdate = tdate + bdate
      cur = self.db.cursor()

      sql = 'INSERT INTO %swetterturnier_bets ' + \
            '(userID, cityID, paramID, tdate, betdate, value, points) VALUES ' + \
            '(%d, %d, %d, %d, %d, %d, %f) ON DUPLICATE KEY UPDATE points = VALUES(points)'
   
      cur.execute( sql % (self.prefix, userID, cityID, paramID, tdate, bdate, -999, points) )


   # -------------------------------------------------------------------
   # - Upsert wetterturnier_betstat table
   # -------------------------------------------------------------------
   def upsert_sleepy_points(self,userID,cityID,tdate,points):
      """Helper function to update the points for the Sleepy player. 
      Upserts the betstat database updating the points for the Sleepy. 
      Actually for any player. But the userID should be the one from the
      Sleepy here. The Sleepy just gets points for the full weekend,
      not points for specific parameters.

      Args:
         userID   (:obj:`int`):   User ID of the **Sleepy** user.
         cityID   (:obj:`int`):   City ID.
         paramID  (:obj:`int`):   Parameter ID.
         tdate    (:obj:`int`):   Tournament date. Days since 1970-01-01.
         betdate  (:obj:`int`):   Bet (forecast) date. Days since 1970-01-01.
         points   (:obj:`float`): Points the player got for that specific entry.
      """

      sql = 'INSERT INTO %swetterturnier_betstat ' + \
            '(userID, cityID, tdate, points) VALUES ' + \
            '(%d, %d, %d, %f) ON DUPLICATE KEY UPDATE points = VALUES(points)'
      cur = self.db.cursor()
   
      cur.execute( sql % (self.prefix, userID, cityID, tdate, points) )
      print("   Updated rows:  {:d}".format(cur.rowcount))
      self.db.commit()


   # -------------------------------------------------------------------
   # - Loading bets. 
   # -------------------------------------------------------------------
   def get_obs_data(self,cityID,paramID,tdate,bdate,wmo=None):
      """Loading observation data from the obs database (the obs which
      are already in the format as they are used for the judging).
      If input ``wmo == None``: return all obs for all stations for a given
      city/parameter/tdate/bdate. If input wmo is an integer value, only
      the observation for this specific station will be returned.

      Args:
         userID   (:obj:`int`): User ID of the @b Sleepy user.
         cityID   (:obj:`int`): City ID.
         paramID  (:obj:`int`): Parameter ID.
         tdate    (:obj:`int`): Tournament date. Days since 1970-01-01.
         betdate  (:obj:`int`): Bet (forecast) date. Days since 1970-01-01.
         wmo      (:obj:`int` or :obj:`None`): None (which is default) or WMO station number.

      Returns:
         list or float: Returns either a list containing numeric values (if wmo == None)
         or a single numeric value. If there are no data at all, a boolean
         False will be returned.
      """ 

      import numpy as np

      #   an integer lower equal 6. If the second one is the case
      #   bdate = tdate+bdate to get days.
      if bdate <= 6: bdate = tdate + bdate
      cur = self.db.cursor()

      # - 
      sql = 'SELECT o.value AS value FROM %swetterturnier_obs AS o ' + \
            'LEFT OUTER JOIN %swetterturnier_stations AS s ' + \
            'ON o.station = s.wmo ' + \
            'WHERE s.cityID = %d AND o.paramID = %d AND o.betdate = %d'
      if not wmo == None: sql += ' AND o.station = %d' % wmo

      #print sql % (self.prefix,self.prefix,cityID,paramID,bdate)
      cur.execute( sql % (self.prefix,self.prefix,cityID,paramID,bdate) )
      cur.execute( sql % (self.prefix,self.prefix,cityID,paramID,bdate) )

      data = cur.fetchall()
      #print data
      if not data:
         return False
      elif wmo == None:
         return [i[0] for i in data]
      else:
         return data[0][0]

   # -------------------------------------------------------------------
   # - Returning parameter ID
   #   Note: to compute the points we have to return ALL, also non-active
   #   ones because it is possible that you are re-computing an old
   #   date where they were used at that time. The point computation
   #   code will skip if there are no data.
   # -------------------------------------------------------------------
   def get_parameter_names(self,active=True,sort=False,cityID=False,tdate=False):
      """Returns all parameter names.
      If input active is set, only active parametres will be returned.
      
      Args:
        active (:obj:`bool`, optional): If True only active parameters will
        be returned.
        sort (:obj:`bool`): True if the params should be sorted by the sort column in the wetterturnier_params table.

      Return:
        list or bool: False if no parameters can be found. Else a list will
        be returned containing the parameter shortnames as strings.
      """
      cur = self.db.cursor()
      sql = "SELECT paramName FROM %swetterturnier_param" % self.prefix
      if tdate: active = True
      if active: sql += " WHERE active = 1"
      if tdate:
         sql += f" AND (since <= {tdate} OR since = 0) AND (until > {tdate} OR until = 0)"
      if sort: sql += " ORDER BY sort"
      cur.execute( sql )
      data = cur.fetchall()

      return [i[0] for i in data]


   # -------------------------------------------------------------------
   # - Returning parameter ID
   # -------------------------------------------------------------------
   def get_parameter_id(self,param):
      """Returns parameter ID given a parameter Name.

      Args:
         param (:obj:`str`): Parameter short name (e.g., TTm)

      Return:
         False if the parameter cannot be found in the database or
         the corresponding integer parameter ID.
      """
      cur = self.db.cursor()
      cur.execute('SELECT paramID FROM %swetterturnier_param WHERE paramName = \'%s\'' % (self.prefix, param))
      data = cur.fetchone()
      if not data:
         return False
      else:
         return int( data[0] )


   def get_max_points(self,param):
      """Return max points given per parameter saved in database (for bonus points)
      """
      cur = self.db.cursor()
      cur.execute("SELECT pmax FROM %swetterturnier_param WHERE paramName = \'%s\'" % (self.prefix, param))
      data = cur.fetchone()
      if not data:
         return False
      res = data[0]
      if res:
         return res
      else: return False
 
   
   def get_parameter_precission(self,paramID):
      cur = self.db.cursor()
      cur.execute(f"SELECT valpre FROM {self.prefix}wetterturnier_param WHERE paramID={paramID}")
      try: return cur.fetchone()[0]
      except: return False


   # -------------------------------------------------------------------
   # - Returns user id. And creates user if necessary.
   # -------------------------------------------------------------------
   def get_user_id_and_create_if_necessary(self, name):
      """Returns user ID and create user if necessary.
      All-in-one wonder method. Searching for the user ID of a given
      user. If the user does not exist: create the user first and then
      return the user ID.
      See also: :meth:`database.create_user`, :meth:`database.get_user_id`

      Args:
        name (:obj:`str`): User name.

      Returns:
        int: Numeric userID.
      """

      userID = self.get_user_id( utils.nicename( name, self.config['conversion_table'] ) )
      if not userID:
          self.create_user( utils.nicename( name, self.config['conversion_table'] ) )
      # - Now loading the newly crates userID
      userID = self.get_user_id( utils.nicename( name,self.config['conversion_table'] ) )
      if not userID:
          utils.exit('OOOH FUCK. Created new user for %s but resulting ID was None in get_user_id_and_create_user_if_necessary.' % name )

      # - Return the id
      return userID
      

   # -------------------------------------------------------------------
   # - Returning user ID
   # -------------------------------------------------------------------
      """Returns user ID given a username. If the user cannot be found,
      the method returns False. There is a vice versa function called
      :py:meth:`database.get_username_by_id`.
      Args:
        user (:obj:`str`): User name.
      
      Returns:
        bool or int: False if user does not exist, else the integer user ID.
      """
   def get_user_id(self, user):
      for i in ["user_login","user_nicename","display_name"]:
         cur = self.db.cursor()
         cur.execute('SELECT ID FROM %susers WHERE LOWER(%s) = \'%s\'' % (self.prefix, i, user.lower()))
         data = cur.fetchone()
         if data == None:
            continue
         else:
            return int( data[0] )         


   # -------------------------------------------------------------------
   # - Returning username corresponding to the ID
   #   More explicitly: return user_login from the database.
   # -------------------------------------------------------------------
   def get_username_by_id(self,userID, which="user_login"):
      """Returns username given a user ID.
      Returns the username for a given user ID. If the user cannot be found,
      the return value will be False. There is a vice versa function called
      :py:meth:`database.get_user_id`.
       
      Args:
        userID (:obj:`int`): Numeric user ID.
    
      Returns:
         bool or str: False if user cannot be identified, else string username.
      """
      try:
         userID = int(userID)
      except:
         utils.exit('Got wrong input to get_username_by_id. Was no integer!')
      cur = self.db.cursor()
      cur.execute('SELECT %s FROM %susers WHERE ID = %d' % ( which, self.prefix, userID ))
      data = cur.fetchone()
      if not data:
         return False
      else:
         return str(data[0])


   def get_all_users(self,typ="ID"):
      """Returns all user IDs in database
      Args:
        user (:obj:`str`): User name.
      
      Returns:
        bool or int: False if user does not exist, else the integer user ID.
      """
      cur = self.db.cursor()
      cur.execute('SELECT ID FROM %susers' % (self.prefix))
      data = cur.fetchall()

      return [int( i[0] ) for i in data]


   def get_groups(self, active=False):
      """Returns all active group names from database.

      Returns:
        list: List of strings containing all group names (of active groups).
      """
      cur = self.db.cursor()
      sql = 'SELECT groupName FROM %swetterturnier_groups'
      if active: sql += ' WHERE active = 1'
      cur.execute(sql % self.prefix)

      # - Make nice list
      return [i[0] for i in cur.fetchall()]

   # -------------------------------------------------------------------
   # - Returning only active groups 
   # -------------------------------------------------------------------
   get_active_groups = lambda self : self.get_groups( active=True)


   # -------------------------------------------------------------------
   # - Returning user ID
   # -------------------------------------------------------------------
   def get_group_id(self,group):
      """Returns group ID given a group name.

      Args:
        group (:obj:`str`): Group name.
      
      Returns:
        bool or int: False if the group cannot be found, else the integer group ID
      """
      cur = self.db.cursor()
      sql = 'SELECT groupID FROM %swetterturnier_groups WHERE groupName = \'%s\''
      cur.execute(sql % (self.prefix, group))
      data = cur.fetchone()
      if not data:
         return False
      else:
         return int(data[0])


   def get_users_in_group(self, groupID=None, group=False, active=True, sort=False):
      """Returns all members of a given groupID or group name.

      Args:
        groupID (:obj:`int`): groupID.
        group (:obj:`str`): The group name.
        active (:obj:`bool`): True if only active members should be returned.
        sort (:obj:`bool`): True if the user should be sorted by the sort column in the wetterturnier_groupusers table. 
      
      Returns:
        List of userIDs for the given group.
      """
      if group:
         return self.get_users_in_group( groupID = self.get_group_id(group) )
      else:
         cur = self.cursor()
         sql = 'SELECT userID FROM %swetterturnier_groupusers WHERE groupID = %d'
         if active: sql+=' AND active=1'
         if sort: sql+=' ORDER BY sort'
         cur.execute(sql % (self.prefix, groupID))
         
         # - Make nice list
         return [int(i[0]) for i in cur.fetchall()]

   # -------------------------------------------------------------------
   # - Create a groupuser (add user to group as a member)
   # -------------------------------------------------------------------
   def create_groupuser(self, user, group, since, active ):
      """Adds an existing user to an existing group.
      If the user is already an actie member of the group: don't add him/her again.

      Args:
         user (:obj:`str`):       User name.
         group (:obj:`str`):      Group name.
         since (:obj:`datetime`): Usually current time. Add user to a group.
                                  the user was a member of the group.
         active (:obj:`id`):      If user is an actie member of the group or not.
                                  Typically 1 as you are adding the user in that split second.
      """
   
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
         print('    GroupUser allready active/existing.')
      else:
         print('    Created groupuser %s|%s' % (user,group))
         i_sql = 'INSERT INTO %swetterturnier_groupusers ' + \
                 '(userID, groupID, since, active) VALUES ' + \
                 '(%d, %d, \'%s\', %d)'
         cur.execute( i_sql % (self.prefix, uID, gID, since, active) )
         self.db.commit()

   # -------------------------------------------------------------------
   # - Compute mean or std points for a city/tdate/day/parameter. 
   #   NOTE: ignore is a userID, the userID from the sleepy.
   #   We will NOT include the sleepy into the computation. This would
   #   lead to an iterative process!
   #   Furthermore we have to exclude the groups by excluding all
   #   users with usernames beginning with 'GRP_'.
   # -------------------------------------------------------------------
   def get_sleepy_points(self,cityID,tdate,ignore):
      """Loading the points from the Sleepy user.
      Returns tuple including betdate, parameterID, sleepy points
      for a given city/tournament date.
      Points are computed as follows: ``Sleepy Points = Average(Points) - Standarddeviation(Points)``
      where ``Points`` are all Group/User points gained in the tournament
      **EXCLUDING** the Sleepy. If the Sleepy would not be excluded the
      points would drift towards -Inf as the average decreases iteratively
      and the standard deviation increases iteratively. 

      Args:
         cityID (:obj:`int`): Numeric city ID.
         tdate (:obj:`int`):  Tournament date, days since 1970-01-01.
         ignore (:obj:`int`): Numeric user ID, ID of the user which should
                              be ignored (e.g., Sleepy's ID).
      Returns:
         float: Sleepy points
      """

      cur = self.db.cursor()
      sql = 'SELECT b.points AS points ' + \
            'FROM %swetterturnier_betstat AS b LEFT OUTER JOIN %susers AS u ' + \
            'ON b.userID = u.ID ' + \
            'WHERE cityID = %d AND tdate = %d AND userID NOT IN%s ' + \
            'AND NOT b.points IS NULL'
      cur.execute( sql % ( self.prefix, self.prefix,cityID,tdate,sql_tuple(ignore)) )
      data = cur.fetchall()

      if not data:
         return False
      else:
         # - Else prepare the data to compute the Sleepy poins
         points = []
         for i in data:
            if i[0] == None: continue
            points.append(float(i[0]))   # store total points to a list

         if len(points) == 0: return False
         else:
            import numpy as np
            return np.round(np.mean(points)  - np.mean(np.abs(points  - np.mean(points))),1)
            #maybe use MAD instead
            #points    = np.round(np.median(data)  - np.mean(np.abs(data  - np.median(data ))),1)


   def get_moses_coefs(self, cityID, tdate):
      cur = self.db.cursor()
      moses = {}
      params = self.get_parameter_names()
      for param in params:
         moses[param] = {}
         paramID = self.get_parameter_id( param )
         sql = "SELECT userID, coef FROM %swetterturnier_coefs WHERE cityID=%d AND tdate=%d AND paramID=%d"
         cur.execute( sql % ( self.prefix, cityID, tdate, paramID ) )
         data = cur.fetchall()
         for i in data:
            user = self.get_username_by_id( i[0] )
            moses[param][user] = i[1]
      return moses


   def upsert_moses_coefs(self, cityID, tdate, moses):
      cur = self.db.cursor()
      for param in list(moses.keys()):
         paramID = self.get_parameter_id( param )
         for user in list(moses[param].keys()):
            #print user
            userID = self.get_user_id( user )
            coef = moses[param][user]; #print coef
            sql = "INSERT INTO %swetterturnier_coefs (cityID, userID, paramID, tdate, coef) VALUES %s ON DUPLICATE KEY UPDATE coef=VALUES(coef)"
            #print sql % ( self.prefix, str(tuple( [cityID, userID, paramID, tdate, coef] ) ) )
            cur.execute( sql % ( self.prefix, str(tuple( [cityID, userID, paramID, tdate, coef] ) ) ) )


   def get_participants_in_city(self, cityID, tdate=False, human=False, sort=False, what="display_name" ):
      """All users participating in a tournament.
      Getting all players who take place in a certain tournament for a
      given city and tdate.

      Args:                                                                                                        
         cityID  (:obj:`int`): ID of the current city.
         tdate   (:obj:`int`): tournament date as integer representation.
         human   (:obj:`bool`): Load only human players.
         sort    (:obj:`int`): Order users by their...
         what    (:obj:`str`): display_name (default). Other possible arguments:
         "user_login", "nicename"

      Returns:
         list: List containing the user IDs of the players
         participating in the tournament for a given cityID and tdate.
         Can be a list of length 0 as well.
      """
      cur = self.db.cursor()
      exclude = [self.get_user_id("Sleepy")]

      if human:
         #We need to exclude all groups, referenz tips and automatons
         groups = self.get_groups()
         for group in groups:
            exclude.append( self.get_user_id( "GRP_" + group ) )

         for group in ["Referenztipps", "Automaten"]:
            groupID = self.get_group_id( group )
            userIDs = self.get_participants_in_group( groupID, cityID, tdate, playing=False )
            for userID in userIDs:
               exclude.append( userID )

      exclude = sql_tuple( exclude )

      if sort:
         if what not in ["display_name", "user_login", "nicename"]:
            utils.exit("Wrong input on database.get_participants_in city!")
         sql = "SELECT DISTINCT userID FROM %swetterturnier_bets wb JOIN wp_users wu ON wb.userID=wu.ID WHERE cityID=%d AND tdate=%d AND userID NOT IN%s ORDER BY "+what

      else:
         sql = "SELECT DISTINCT userID FROM %swetterturnier_bets WHERE cityID=%d AND tdate=%d AND userID NOT IN%s"
      
      cur.execute( sql % ( self.prefix, cityID, tdate, exclude ) )

      return [int( i[0] ) for i in cur.fetchall()]


   def find_missing_obs(self, cityID, tdate=False ):
      """
      Check whether too many obs are missing for a given city (and tdate) to compute Moses.
      Returns True if obs are missing and False if everything is OK.
      """
      if not tdate:
         tdate = self.current_tournament()

      params = self.get_parameter_names()

      for param in params:
         paramID = self.get_parameter_id( param )
         for day in range(1,3):
            obs = self.get_obs_data(cityID,paramID,tdate,day)
            if type(obs) == bool:
               print("Obs in city '%s' have to many missing parameters on %s (tdate %d)!" % ( self.get_city_name_by_ID(cityID), utils.tdate2string(tdate), tdate ))
               return True
         
      return False


   def find_missing_bets(self, cityID, tdate=False ):
      """Find incomplete bets for a given tdate and cityID"""
      if not tdate:
         tdate = self.current_tournament()

      userIDs  = self.get_participants_in_city( cityID, tdate, "human" )
      params = self.get_parameter_names( active = True, tdate = tdate )
      missing = []

      for userID in userIDs:
         #another possible solution:
         """
         sql = "SELECT * FROM %swetterturnier_bets WHERE userID=%d AND cityID=%d AND tdate=%d"
         if cur.execute( sql % (self.prefix, table, userID, cityID, tdate) ) < len(params)*2:
            missing.append( userID )
            break
         """
         for param in params:
            paramID = self.get_parameter_id( param )
            for day in range(1,3):
               bet = self.get_bet_data("user",userID,cityID,paramID,tdate,day)
               if type(bet) == bool:
                  print("Bet of user '%s' has missing parameters!" % ( self.get_username_by_id( userID ) ))
                  missing.append( userID )
                  break; break
      if len(missing) == 0:
         return False
      else:
         return missing


   # delete bet and the corresponding betdata for a user in a city/tdate
   def delete_bet(self, userID, cityID, tdate):

      user = self.get_username_by_id( userID )
      city = self.get_city_name_by_ID( cityID )
      date = utils.tdate2string( tdate )
      cur = self.db.cursor()

      #check if bet exists
      sql = "SELECT * FROM %swetterturnier_bets WHERE userID=%d AND cityID=%d AND tdate=%d"
      sql2 = "SELECT * FROM %swetterturnier_betstat WHERE userID=%d AND cityID=%d AND tdate=%d"
      if cur.execute( sql % (self.prefix, userID, cityID, tdate) ) > 0 or cur.execute( sql2 % (self.prefix, userID, cityID, tdate) ) > 0:
         sql = "DELETE FROM %swetterturnier_%s WHERE userID=%d AND cityID=%d AND tdate=%d"
         tables = ["bets","betstat"]
         for table in tables:
            #print sql % ( self.prefix, table, userID, cityID, tdate )
            cur.execute( sql % ( self.prefix, table, userID, cityID, tdate ) )
            self.db.commit()
         for table in tables:
            sql = "SELECT * FROM %swetterturnier_%s WHERE userID=%d AND cityID=%d AND tdate=%d"
            if cur.execute( sql % (self.prefix, table, userID, cityID, tdate) ) > 0:
               utils.exit( "Could not delete bet of user %s in city %s from %s" % (user, city, date) )
         print("Succesfully deleted bet and corresponding betstat of user %s in city %s from %s" % (user, city, date))
      else: print("Bet of user %s in city %s from %s does not exist!" % (user, city, date))


   #----------------------------------------------------------------
   # - Close the database 
   # ----------------------------------------------------------------
   def close(self,verbose=False):
      """Simple wrapper around MySQLdb.close.
      
      Args:
         verbose (:obj:`bool`): If set to True a small statement will
         be printed to stdout.
      """

      if verbose: print('  * Close database')
      self.db.close()
