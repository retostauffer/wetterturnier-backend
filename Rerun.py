# -------------------------------------------------------------------
# - NAME:        Chain.py 
# - AUTHOR:      Reto Stauffer
# - DATE:        2014-09-21
# - LICENSE: GPL-3, Reto Stauffer, copyright 2014
# -------------------------------------------------------------------
# - DESCRIPTION: Runs all the necessary steps. 
# -------------------------------------------------------------------
# - EDITORIAL:   2014-09-19, RS: Created file on thinkreto.
#                Adapted from ComputePoints.py
# -------------------------------------------------------------------
# - L@ST MODIFIED: 2017-12-20 17:37 on prognose2
# -------------------------------------------------------------------



# - Start as main script (not as module)
if __name__ == '__main__':
   """
   This is Chain.py, a simple controlling script. Starts several
   script in the order as they have to be called to compute all
   necessary things for the wetterturnier. E.g., including:
   - ComputeMeanBets.py  (compute group bets)
   - ComputePetrus.py    (computes Petrus as player)
   - ...
   - ComputeSumPoints.py (computes points)
   - ComputeSleepy.py   (relies on the sumpoints)
   
   Script stops if one of the processes has non-zero exit state.
   """

   import sys, os
   from pywetterturnier import utils, database
   import numpy as np

   # - Store input arguments - need them later
   #   to call the subscripts. Only for the Chain.py script.
   main_args = sys.argv[1:]
   # - Evaluating input arguments
   inputs = utils.inputcheck('Chain')
   # - Read configuration file
   config = utils.readconfig('config.conf',inputs)

   # - Initializing class and open database connection
   db = database.database(config)

   if not db.check_if_table_exists("wetterturnier_rerunrequest"):
      print "[!] Table wetterturnier_rerunrequest does not exist, stop here."
      db.close(); sys.exit(9)

   # - Check whether there are any rerun requests
   cur = db.cursor()
   cur.execute("SELECT tdate,cityID FROM wp_wetterturnier_rerunrequest " + \
               "WHERE done IS NULL GROUP BY tdate,cityID;")
   rerun = cur.fetchall()

   if len(rerun) == 0:
      print "   There are no rerun requests, stop here."; sys.exit(0)
   
   # - Compute the Points for all the dudes first
   import subprocess as sub
   from datetime import datetime as dt
   scripts = ['ComputeMeanBets.py',
              'ComputePetrus.py',
#              'ComputePersistenzen.py',
              'ComputePoints.py',
              'ComputeSumPoints.py',
              'ComputeSleepy.py']


   # - Now calling the other scripts using the necessary
   #   input arguments.
   for rec in rerun:
      tdate    = int(rec[0])
      tdatestr = dt.fromtimestamp(tdate*86400).strftime("%Y-%m-%d") 
      cityID   = int(rec[1])

      city     = db.get_city_name_by_ID( cityID )
      if not city:
         print "[!] OUPS! Cannot find city {0:d} in database!".format(cityID)

      print "  * Rerun for tournament date {0:d} ({1:s})".format(tdate,tdatestr)
      print "    Run computation for city {0:s} ({1:d})".format(city,cityID)

      # Run the scripts in the correct order
      for script in scripts:

         # - Create next python command. Append ALL input arguments
         #   we hade in this script plus the tdate (if not set in input
         #   arguments).
         cmd = ['python',script]
         # Append tournamentdate and city to the arglist
         cmd.append('-t'); cmd.append("{0:d}".format(tdate))
         cmd.append('-c'); cmd.append(city)

         p1 = sub.Popen(cmd,stderr=sub.PIPE)
         err = p1.communicate()
         if not p1.returncode == 0:
            for line in err: print '%s\n' % line
            utils.exit('ERROR WHILE RUNNING %s AS SUBPROCESS FOR DATE %d CITY %s' % (script,tdate,city))


      # update database ans set these jobs to 'done'
      cur = db.cursor()
      now = dt.now().strftime("%Y-%m-%d %H:%M:%S")
      sql = "UPDATE {0:s}{1:s} SET done = '{2:s}' WHERE cityID = {3:d} AND tdate = {4:d}".format(
            config['mysql_prefix'],'wetterturnier_rerunrequest',now,cityID,tdate)
      cur = db.cursor()
      cur.execute(sql)

   db.commit()
   db.close()

