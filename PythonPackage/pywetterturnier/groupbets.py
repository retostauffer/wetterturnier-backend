# -------------------------------------------------------------------
# - NAME:        groupbets.py
# - AUTHOR:      Reto Stauffer
# - DATE:        2014-09-13
# -------------------------------------------------------------------
# - DESCRIPTION: Groupbets creates the mean bets/tips for the
#                groups defined in the database for a given date.
#                The groupbets class is handling this. 
# -------------------------------------------------------------------
# - EDITORIAL:   2014-09-13, RS: Created file on thinkreto.
# -------------------------------------------------------------------
# - L@ST MODIFIED: 2015-01-04 18:01 on prognose2.met.fu-berlin.de
# -------------------------------------------------------------------


class groupbets(object):

   # ----------------------------------------------------------------
   # - Init
   # ----------------------------------------------------------------
   def __init__(self,config):
      """The database class is handling the connection to the
      mysql database and different calls and stats."""

      from database import database

      self.config = config
      self.db = database(config)


   # ----------------------------------------------------------------
   # - Reading groups 
   # ----------------------------------------------------------------
   def get_groups(self,tdate):

      from datetime import datetime as dt

      print '  * Loading groups active at tdate %d' % tdate

      bgn = dt.fromtimestamp( (1+tdate) * 86400 ).strftime('%Y-%m-%d %H:%M:%S')
      end = dt.fromtimestamp( (0+tdate) * 86400 ).strftime('%Y-%m-%d %H:%M:%S')
      sql = 'SELECT groupName, groupID FROM %swetterturnier_groups ' + \
            ' WHERE ( since < \'%s\' AND until > \'%s\' ) ' + \
            ' OR ( since < \'%s\' AND until = \'0000-00-00 00:00:00\')'

      #print  sql % (self.config['mysql_prefix'], bgn, end, bgn) 
      cur = self.db.cursor()
      cur.execute( sql % (self.config['mysql_prefix'], bgn, end, bgn) )

      # - Getting groups
      cols = cur.description
      data = cur.fetchall()
      res  = {}
      for grp in data:
         res[str(grp[0])] = int(grp[1])

      # - Show groups
      for grp in res.keys():
         print '    - %s (ID: %d)' % (grp, res[grp])
      
      return res 


   # ----------------------------------------------------------------
   # - Create a wordpress user for the group if not existing.
   # ----------------------------------------------------------------
   def check_and_create_groupuser( self, groups ):

      print '  * %s' % 'Checking user names for group names'
      print '    %s' % 'Username will be GRP_groupname'


      # - Loop over all groups. If there is no user for the group
      #   we have to create it first.
      cur = self.db.cursor()
      sql = 'SELECT ID FROM %susers ' + \
            ' WHERE user_login = \'%s\''
      usrsql = 'INSERT INTO %susers (user_login,user_nicename,display_name) ' + \
               ' VALUES (\'%s\', \'%s\', \'%s\')'

      def getid(cur,sql,grp):
         cur.execute( sql % (self.config['mysql_prefix'],grp) )
         return cur.fetchall()

      # - Loop over groups
      res = {}
      for grp in groups.keys():

         thegrp = 'GRP_'+grp
         data = getid(cur,sql,thegrp)

         # - If user for the group does not exist, create.
         if len(data) == 0:
            print '    %s has no wordpress user. Create %s' % (grp,thegrp)
            cur.execute( usrsql % (self.config['mysql_prefix'],thegrp,thegrp,thegrp) )
            self.db.commit()
            data = getid(cur,sql,thegrp)
         else:
            res[grp] = int(data[0][0])


      return res


   # ----------------------------------------------------------------
   # - Getting date of the current tournament
   # ----------------------------------------------------------------
   def current_tournament(self):

      return self.db.current_tournament()


   # ----------------------------------------------------------------
   # - Getting users wich are within the group.
   # ----------------------------------------------------------------
   def users_in_group( self, grp, grpID, tdate ):

      from datetime import datetime as dt

      print '  * Loading users for group %s active at tdate %d' % (grp, tdate) 

      bgn = dt.fromtimestamp( (1+tdate) * 86400 ).strftime('%Y-%m-%d %H:%M:%S')
      end = dt.fromtimestamp( (0+tdate) * 86400 ).strftime('%Y-%m-%d %H:%M:%S')
      sql = 'SELECT userID FROM %swetterturnier_groupusers ' + \
            ' WHERE groupID = %d ' + \
            ' AND ( ( since < \'%s\' AND until > \'%s\' ) ' + \
            '       OR ( since < \'%s\' AND until = \'0000-00-00 00:00:00\') )'

      #print  sql % (self.config['mysql_prefix'], bgn, end, bgn) 
      cur = self.db.cursor()
      cur.execute( sql % (self.config['mysql_prefix'], grpID, bgn, end, bgn) )

      # - Getting groups
      cols = cur.description
      data = cur.fetchall()
      res  = []
      for usr in data:
         res.append(int(usr[0]))

      return res


   # ----------------------------------------------------------------
   # - Compute mean tip 
   # ----------------------------------------------------------------
   def compute_bets( self, grp, tdate, userIDs ):

      print '  * %s' % 'Compute mean values'

      # - basic sql question
      sqllist = []
      sqllist.append('SELECT cityID, paramID, tournamentdate, betdate, ')
      sqllist.append('AVG(value) AS value FROM %swetterturnier_bets WHERE \n')
      sqllist.append('tournamentdate = %d \n')
      sqllist.append('AND (\n')
      sqllist.append('   %s\n')
      sqllist.append(') GROUP BY cityID, paramID, betdate\n')

      # - User selection
      usrlist = []
      for usr in userIDs:
         usrlist.append('userID=%d' % usr)

      sql = ''.join(sqllist)
      usr = ' OR '.join(usrlist)
      sql = sql % (self.config['mysql_prefix'],tdate,usr)

      # - Calling database
      cur = self.db.cursor()
      cur.execute( sql )
      data = cur.description
      cols = []
      for elem in data: cols.append( str(elem[0]) )
      data = cur.fetchall()

      # - Print data
      #c_fmt = '%-10s ' * len(cols)
      #d_fmt = '%10.2f  ' * len(cols)
      #print c_fmt % tuple(cols)
      #for row in data:
      #   print d_fmt % row

   
      # - Return data
      return cols, data


   # ----------------------------------------------------------------
   # - Insert mean tips into database
   # ----------------------------------------------------------------
   def upsert_bets(self, cols, data, tdate, usrID, status=2):

      import numpy as np

      cur = self.db.cursor()

      # - Insert that stuff into the database now
      sql = 'INSERT INTO ' + self.config['mysql_prefix'] + 'wetterturnier_bets ' + \
            '(userID, ' + ', '.join(cols) + ') VALUES ' + \
            '(' + str(usrID) + ', ' + ', '.join( np.repeat('%s',len(cols)) ) + ') ' + \
            'ON DUPLICATE KEY UPDATE value=VALUES(value)'


      cur.executemany( sql, data )
      self.db.commit()


      ###### - Update status
      #####sql = 'UPDATE %swetterturnier_bets SET status=%d WHERE ' + \
      #####      'userID=%d AND tournamentdate=%d'
      #####cur.execute( sql % (self.config['mysql_prefix'], status, usrID, tdate) )
      #####self.db.commit()
      













