# -------------------------------------------------------------------
# - NAME:        ComputePoints.py
# - AUTHOR:      Reto Stauffer
# - DATE:        2014-09-21
# - LICENSE: GPL-3, Reto Stauffer, copyright 2014
# -------------------------------------------------------------------
# - DESCRIPTION: Compute points for all players. 
# -------------------------------------------------------------------
# - EDITORIAL:   2014-09-19, RS: Created file on thinkreto.
#                Adapted from ComputePetrus.py
# -------------------------------------------------------------------
# - L@ST MODIFIED: 2018-01-19 15:20 on marvin
# -------------------------------------------------------------------

import sys, os
sys.path.append('PyModules')


# - Start as main script (not as module)
if __name__ == '__main__':

   import numpy as np
   # - Wetterturnier specific modules
   from pywetterturnier import utils, database
   # - Evaluating input arguments
   inputs = utils.inputcheck('ComputeStats')
   # - Read configuration file
   config = utils.readconfig('config.conf',inputs)

   # - Initializing class and open database connection
   db        = database.database(config)
   post_id   = config['input_param']
   t         = config['input_tdate']

   excluded_users = ["WB-Berlin","Foehni"]

   for i in ("Automaten", "Referenztipps", "MM-MOS", "WAV2", "Aviatik"):
      group_users = db.get_users_in_group( group=i )
      for j in group_users:
         excluded_users.append(j)

   print(excluded_users)

   sql = "SELECT user_login FROM %susers WHERE ID NOT IN %s %sORDER BY user_login ASC"

   skip = str("")
   for i in ("GRP_%", "Acinn%", "%-MOS%"):
      skip += "AND user_login NOT LIKE '%s' " %i

   cur = db.cursor()
   cur.execute( sql % ( db.prefix, db.sql_tuple( excluded_users ), skip[:-1] ) )
   data = cur.fetchall()

   data = data[:t]

   for i in data:
      print(i[0])

   count = len(data)

   users_str = str("")
   for i in enumerate(data):
      user = i[1][0]
      users_str += 'i:%d;a:2:{s:2:"id";i:%d;s:8:"response";s:%d:"%s";}' % (i[0], i[0]+1, len(user), user)

   _poll_responses = "a:%d:{%s}" % ( len(data), users_str )

   print(_poll_responses)

   #insert in database; table wp_postmeta

   sql = "UPDATE %spostmeta SET meta_value='%s' WHERE post_id=%s AND `meta_key` = '_poll_responses'"

   print(post_id)

   cur = db.cursor()
   cur.execute( sql % ( db.prefix, _poll_responses, post_id ) )
   db.commit()
