# -------------------------------------------------------------------
# - NAME:        CheckMergeUsers.py
# - AUTHOR:      Reto Stauffer
# - DATE:        2017-06-27
# -------------------------------------------------------------------
# - DESCRIPTION:
# -------------------------------------------------------------------
# - EDITORIAL:   2017-06-27, RS: Created file on thinkreto.
# -------------------------------------------------------------------
# - L@ST MODIFIED: 2017-06-27 14:02 on thinkreto
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
   inputs = utils.inputcheck('CheckMergeUsers')
   # - Read configuration file
   config = utils.readconfig('config.conf',inputs)
   # - Initializing class and open database connection
   db        = database.database(config)
   tdates = db.all_tournament_dates( None )

   # ----------------------------------------------------------------
   # Usage notification
   # ----------------------------------------------------------------
   if not config['input_user']:
      print "[!] Stop. Input -u/--user has to be set"
      print "    Example: --user reto,rto,tro would"
      print "    check whether we can merge these three"
      print "    users in the database. The FIRST one "
      print "    is the leading user (the others will be"
      print "    removed and set to the leading user)."
      sys.exit(9)
   else:
      users = []
      userids = []
      for rec in config['input_user'].split(","):
         rec = rec.strip()
         if not rec in users: users.append(rec)
      if len(rec) < 2:
         print "Input -u/--usres: at least two required!"; sys.exit(9)

   # ----------------------------------------------------------------
   # Check if users exist
   # ----------------------------------------------------------------
   userids = [None] * len(users)
   for u in range(0,len(users)):
      userids[u] = db.get_user_id( users[u] )
      if not userids[u]:
         print "[!] Stop. User \"%s\" could not be found." % users[u]
         sys.exit(9)
      if u == 0:
         print "   MASTER user:   %-20s   [uid %5d]" % (users[u],userids[u])
      else:
         print "   Slave user:    %-20s   [uid %5d]" % (users[u],userids[u])

   # ----------------------------------------------------------------
   # Bit inefficient, however, allows to show the data in a talbe form
   # ----------------------------------------------------------------
   sql = "SELECT count(*) AS count FROM wp_wetterturnier_betstat WHERE " + \
         "userID = %d AND tdate = %d"

   # Show header
   print " %10s %6s " % ("date","tdate"),
   for u in range(0,len(users)):
      print " %10s " % users[u],
   print "" # line break

   # Final variable. If set to False we would not allow to merge.
   # If 'True' merging would be allowed.
   merging_allowed = True
   cur = db.cursor()
   for tdate in tdates:
      # Initialize
      counts = [None] * len(users)
      for u in range(0,len(users)):
         cur.execute( sql % (userids[u],tdate) )
         counts[u] = cur.fetchone()[0]

      # If no bets for this tournament at all: skip
      if np.max(counts) == 0: continue

      # Show frontend
      print " %10s %6d " % (utils.tdate2string(tdate),tdate),
      for u in range(0,len(users)):
         print " %10d " % counts[u],
      if len(np.where(np.array(counts) > 0)[0]) == 1:
         print "    merge ok"
      else:
         merging_allowed = False
         print "    [ERROR] MERGING NOT ALLOWED (OVERLAP)"


   if not merging_allowed:
      print "\n\n  !!!!   MERGING NOT ALLOWED !!!!!\n\n"
      db.close()
      sys.exit(9)


   # ----------------------------------------------------------------
   # Else merge user
   # ----------------------------------------------------------------
   print "\n\n  ++++ merging is allowed ++++\n\n"
   print " * Merge users now"

   cur = db.cursor()
   for u in range(1,len(users)):

      print "   Merge %s [%d] >>> %s [%d]" % (users[u],userids[u],users[0],userids[0])
      # Update wetterturnier tables
      bets = "UPDATE wp_wetterturnier_bets SET userID = %d WHERE userID = %d" % \
             (userids[u],userids[0])
      betstat = "UPDATE wp_wetterturnier_betstat SET userID = %d WHERE userID = %d" % \
             (userids[u],userids[0])

      # Remove information from wp_user and wp_usermeta
      usr     = "DELETE FROM wp_users WHERE ID = %d" % userids[u]
      usrmeta = "DELETE FROM wp_usermeta WHERE user_id = %d" % userids[u]

      # Execute commands
      cur.execute( bets )
      cur.execute( betstat )
      cur.execute( usr )
      cur.execute( usrmeta )

   db.commit()
      
   db.close()
















