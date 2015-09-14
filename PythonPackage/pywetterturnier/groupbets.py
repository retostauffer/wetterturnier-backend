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
# - L@ST MODIFIED: 2015-08-04 11:42 on prognose2.met.fu-berlin.de
# -------------------------------------------------------------------


# unused? # class groupbets(object):
# unused? # 
# unused? #    # ----------------------------------------------------------------
# unused? #    # - Init
# unused? #    # ----------------------------------------------------------------
# unused? #    def __init__(self,config):
# unused? #       """The database class is handling the connection to the
# unused? #       mysql database and different calls and stats."""
# unused? # 
# unused? #       from database import database
# unused? # 
# unused? #       self.config = config
# unused? #       self.db = database(config)
# unused? # 
# unused? # 
# unused? #    # ----------------------------------------------------------------
# unused? #    # - Reading groups 
# unused? #    # ----------------------------------------------------------------
# unused? #    def get_groups(self,tdate):
# unused? # 
# unused? #       from datetime import datetime as dt
# unused? # 
# unused? #       print '  * Loading groups active at tdate %d' % tdate
# unused? # 
# unused? #       bgn = dt.fromtimestamp( (1+tdate) * 86400 ).strftime('%Y-%m-%d %H:%M:%S')
# unused? #       end = dt.fromtimestamp( (0+tdate) * 86400 ).strftime('%Y-%m-%d %H:%M:%S')
# unused? #       sql = 'SELECT groupName, groupID FROM %swetterturnier_groups ' + \
# unused? #             ' WHERE ( since < \'%s\' AND until > \'%s\' ) ' + \
# unused? #             ' OR ( since < \'%s\' AND until = \'0000-00-00 00:00:00\')'
# unused? # 
# unused? #       #print  sql % (self.config['mysql_prefix'], bgn, end, bgn) 
# unused? #       cur = self.db.cursor()
# unused? #       cur.execute( sql % (self.config['mysql_prefix'], bgn, end, bgn) )
# unused? # 
# unused? #       # - Getting groups
# unused? #       cols = cur.description
# unused? #       data = cur.fetchall()
# unused? #       res  = {}
# unused? #       for grp in data:
# unused? #          res[str(grp[0])] = int(grp[1])
# unused? # 
# unused? #       # - Show groups
# unused? #       for grp in res.keys():
# unused? #          print '    - %s (ID: %d)' % (grp, res[grp])
# unused? #       
# unused? #       return res 
# unused? # 
# unused? # 
# unused? #    # ----------------------------------------------------------------
# unused? #    # - Create a wordpress user for the group if not existing.
# unused? #    # ----------------------------------------------------------------
# unused? #    def check_and_create_groupuser( self, groups ):
# unused? # 
# unused? #       print '  * %s' % 'Checking user names for group names'
# unused? #       print '    %s' % 'Username will be GRP_groupname'
# unused? # 
# unused? # 
# unused? #       # - Loop over all groups. If there is no user for the group
# unused? #       #   we have to create it first.
# unused? #       cur = self.db.cursor()
# unused? #       sql = 'SELECT ID FROM %susers ' + \
# unused? #             ' WHERE user_login = \'%s\''
# unused? #       usrsql = 'INSERT INTO %susers (user_login,user_nicename,display_name) ' + \
# unused? #                ' VALUES (\'%s\', \'%s\', \'%s\')'
# unused? # 
# unused? #       def getid(cur,sql,grp):
# unused? #          cur.execute( sql % (self.config['mysql_prefix'],grp) )
# unused? #          return cur.fetchall()
# unused? # 
# unused? #       # - Loop over groups
# unused? #       res = {}
# unused? #       for grp in groups.keys():
# unused? # 
# unused? #          thegrp = 'GRP_'+grp
# unused? #          data = getid(cur,sql,thegrp)
# unused? # 
# unused? #          # - If user for the group does not exist, create.
# unused? #          if len(data) == 0:
# unused? #             print '    %s has no wordpress user. Create %s' % (grp,thegrp)
# unused? #             cur.execute( usrsql % (self.config['mysql_prefix'],thegrp,thegrp,thegrp) )
# unused? #             self.db.commit()
# unused? #             data = getid(cur,sql,thegrp)
# unused? #          else:
# unused? #             res[grp] = int(data[0][0])
# unused? # 
# unused? # 
# unused? #       return res
# unused? # 
# unused? # 
# unused? #    # ----------------------------------------------------------------
# unused? #    # - Getting date of the current tournament
# unused? #    # ----------------------------------------------------------------
# unused? #    def current_tournament(self):
# unused? # 
# unused? #       return self.db.current_tournament()
# unused? # 
# unused? # 
# unused? #    # ----------------------------------------------------------------
# unused? #    # - Getting users wich are within the group.
# unused? #    # ----------------------------------------------------------------
# unused? #    def users_in_group( self, grp, grpID, tdate ):
# unused? # 
# unused? #       from datetime import datetime as dt
# unused? # 
# unused? #       print '  * Loading users for group %s active at tdate %d' % (grp, tdate) 
# unused? # 
# unused? #       bgn = dt.fromtimestamp( (1+tdate) * 86400 ).strftime('%Y-%m-%d %H:%M:%S')
# unused? #       end = dt.fromtimestamp( (0+tdate) * 86400 ).strftime('%Y-%m-%d %H:%M:%S')
# unused? #       sql = 'SELECT userID FROM %swetterturnier_groupusers ' + \
# unused? #             ' WHERE groupID = %d ' + \
# unused? #             ' AND ( ( since < \'%s\' AND until > \'%s\' ) ' + \
# unused? #             '       OR ( since < \'%s\' AND until = \'0000-00-00 00:00:00\') )'
# unused? # 
# unused? #       #print  sql % (self.config['mysql_prefix'], bgn, end, bgn) 
# unused? #       cur = self.db.cursor()
# unused? #       cur.execute( sql % (self.config['mysql_prefix'], grpID, bgn, end, bgn) )
# unused? # 
# unused? #       # - Getting groups
# unused? #       cols = cur.description
# unused? #       data = cur.fetchall()
# unused? #       res  = []
# unused? #       for usr in data:
# unused? #          res.append(int(usr[0]))
# unused? # 
# unused? #       return res
# unused? # 
# unused? # 
# unused? #    # ----------------------------------------------------------------
# unused? #    # - Compute mean tip 
# unused? #    # ----------------------------------------------------------------
# unused? #    def compute_bets( self, grp, tdate, userIDs ):
# unused? # 
# unused? #       print '  * %s' % 'Compute mean values'
# unused? # 
# unused? #       # - basic sql question
# unused? #       sqllist = []
# unused? #       sqllist.append('SELECT cityID, paramID, tournamentdate, betdate, ')
# unused? #       sqllist.append('AVG(value) AS value FROM %swetterturnier_bets WHERE \n')
# unused? #       sqllist.append('tournamentdate = %d \n')
# unused? #       sqllist.append('AND (\n')
# unused? #       sqllist.append('   %s\n')
# unused? #       sqllist.append(') GROUP BY cityID, paramID, betdate\n')
# unused? # 
# unused? #       # - User selection
# unused? #       usrlist = []
# unused? #       for usr in userIDs:
# unused? #          usrlist.append('userID=%d' % usr)
# unused? # 
# unused? #       sql = ''.join(sqllist)
# unused? #       usr = ' OR '.join(usrlist)
# unused? #       sql = sql % (self.config['mysql_prefix'],tdate,usr)
# unused? # 
# unused? #       # - Calling database
# unused? #       cur = self.db.cursor()
# unused? #       cur.execute( sql )
# unused? #       data = cur.description
# unused? #       cols = []
# unused? #       for elem in data: cols.append( str(elem[0]) )
# unused? #       data = cur.fetchall()
# unused? # 
# unused? #       # - Print data
# unused? #       #c_fmt = '%-10s ' * len(cols)
# unused? #       #d_fmt = '%10.2f  ' * len(cols)
# unused? #       #print c_fmt % tuple(cols)
# unused? #       #for row in data:
# unused? #       #   print d_fmt % row
# unused? # 
# unused? #    
# unused? #       # - Return data
# unused? #       return cols, data
# unused? # 
# unused? # 
# unused? #    # ----------------------------------------------------------------
# unused? #    # - Insert mean tips into database
# unused? #    # ----------------------------------------------------------------
# unused? #    def upsert_bets(self, cols, data, tdate, usrID, status=2):
# unused? # 
# unused? #       import numpy as np
# unused? # 
# unused? #       cur = self.db.cursor()
# unused? # 
# unused? #       # - Insert that stuff into the database now
# unused? #       sql = 'INSERT INTO ' + self.config['mysql_prefix'] + 'wetterturnier_bets ' + \
# unused? #             '(userID, ' + ', '.join(cols) + ') VALUES ' + \
# unused? #             '(' + str(usrID) + ', ' + ', '.join( np.repeat('%s',len(cols)) ) + ') ' + \
# unused? #             'ON DUPLICATE KEY UPDATE value=VALUES(value)'
# unused? # 
# unused? # 
# unused? #       cur.executemany( sql, data )
# unused? #       self.db.commit()









