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

   sql = 'SELECT user_email FROM %susers WHERE user_email NOT LIKE ""'

   cur = db.cursor()
   cur.execute( sql % db.prefix )

   for i in cur.fetchall():
      print(i[0])
