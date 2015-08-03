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
# - L@ST MODIFIED: 2015-08-03 14:32 on prognose2.met.fu-berlin.de
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
   - ComputeDeadman.py   (relies on the sumpoints)
   
   Script stops if one of the processes has non-zero exit state.
   """

   import sys, os
   from pywetterturnier import inputcheck
   from pywetterturnier import utils
   from pywetterturnier import database
   import numpy as np

   # - Store input arguments - need them later
   #   to call the subscripts. Only for the Chain.py script.
   main_args = sys.argv[1:]
   # - Evaluating input arguments
   inputs = inputcheck.inputcheck('Chain')
   # - Read configuration file
   config = utils.readconfig('config.conf',inputs)

   # - Initializing class and open database connection
   db = database.database(config)

   # - Loading tdate (day since 1970-01-01) for the tournament.
   #   Normaly Friday-Tornament (tdate is then Friday) while
   #   the bet-dates are for Saturday and Sunday.
   if config['input_tdate'] == None:
      config['input_tdate'] = db.current_tournament()
      print '  * Using latest tournament date: %d' % config['input_tdate']
   else:
      #utils.exit('Sorry, need explicit -t/--tdate input for this script')
      print '  * Using input tdate: %d' % config['input_tdate']

   # - If input_user was given as string we have to find the
   #   corresponding userID first!
   if type(config['input_user']) == type(str()):
      config['input_user'] = db.get_user_id( config['input_user'] )
      if not config['input_user']:
         utils.exit('SORRY could not convert your input -u/--user to corresponding userID. Check name.')
   
   # - Compute the Points for all the dudes first
   import subprocess as sub
   scripts = ['ComputeMeanBets.py',
              'ComputePetrus.py',
              'ComputePersistenz.py',
              'ComputePoints.py',
              'ComputeSumPoints.py',
              'ComputeDeadman.py']


   # - Now calling the other scripts using the necessary
   #   input arguments.
   for script in scripts:

      # - Create next python command. Append ALL input arguments
      #   we hade in this script plus the tdate (if not set in input
      #   arguments).
      cmd = ['python',script]
      for arg in main_args: cmd.append(str(arg))
      if not '-t' in cmd and not '--tdate' in cmd and not '-a' in cmd and not '--alldates' in cmd:
         cmd.append('-t'); cmd.append(str(config['input_tdate']))
      p1 = sub.Popen(cmd,stderr=sub.PIPE)
      err = p1.communicate()
      if not p1.returncode == 0:
         for line in err: print '%s\n' % line
         utils.exit('ERROR WHILE RUNNING %s AS SUBPROCESS FOR DATE %d' % (script,config['input_tdate']))






