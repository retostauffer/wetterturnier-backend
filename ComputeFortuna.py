# - ComputeFortuna.py- #
# -------------------- #
# - Start as main script (not as module)
if __name__ == '__main__':

   import sys, os
   import numpy as np
   from scipy.stats import mode
   from glob import glob
   # - Wetterturnier specific methods
   from pywetterturnier import getobs, utils, database, mitteltip

   # - Evaluating input arguments
   inputs = utils.inputcheck('ComputeFortuna')
   # - Read configuration file
   config = utils.readconfig('config.conf', inputs)


   # - Initializing class and open database connection
   db        = database.database(config)

   # - Loading tdate (day since 1970-01-01) for the tournament.
   #   Normaly Friday-Tornament (tdate is then Friday) while
   #   the bet-dates are for Saturday and Sunday if there was
   #   no input tournament date -t/--tdate.
   if config['input_tdate'] == None:
      tdates    = db.current_tournament()
   else:
      tdates     = config['input_tdate']

   print('  * Current tournament is %s' % utils.tdate2string( tdates ))
   # - Loading all different cities (active cities)
   cities     = db.get_cities()
   # - If input city set, then drop all other cities.
   if not config['input_city'] == None:
      tmp = []
      for i in cities:
         if i['name'] == config['input_city']: tmp.append( i )
      cities = tmp

   # ----------------------------------------------------------------
   # - Check if we are allowed to perform the computation of the
   #   Petrus bets on this date
   # ----------------------------------------------------------------
   #check = utils.datelock(config,tdate)
   #if check:
   #   print '    Date is \'locked\' (datelock). Dont execute.'
   #   import sys; sys.exit(0)


   # ----------------------------------------------------------------
   # - Prepare the Fortune Bet
   # ----------------------------------------------------------------
   username = 'Fortuna'
   db.create_user( username )
   userID = db.get_user_id( username )

   # ----------------------------------------------------------------

   # ----------------------------------------------------------------
   # - Loopig over all tournament dates
   # ----------------------------------------------------------------
   from datetime import datetime as dt

   #sinnvolle Tournier dates: #17354 - #17935
   day = 1
   tdates = np.arange(17354, 17935, 7)
   #parameter = 3
   cityID = 1  
 
   userID = db.get_user_id("Donnerstag")
   print('User ID of Donnerstag: %s' %( userID ))

   #for tdate in tdates:
      # - Using obervations of the tournament day for our Persistenz player
   #   tdate_str = dt.fromtimestamp( tdate * 86400 ).strftime('%a, %Y-%m-%d')
   #   print "    Searching for Observations:     %s (%d)" % (tdate_str,tdate)

   # - Returns list object containing two dicts 
   #   where all human bets are in.
   #bet = mitteltip.mitteltip(db,'all',False,city,tdate)
   #Persistenz  ID=1603
   #typ="user"
   #get_bet_data()
   #get_user_ID() 

   for tdate in tdates: 
      #db.get_bet_data('user',userID,city['ID'],paramID,tdate,day) 
      for day in range(1,3):
         for paramID in range(1,13):


            if day == 1: print("Samstag:")
            elif day ==2: print("Sonntag:")
      	    
 	    #temp = db.get_bet_data('user',userID,cityID,parameter,tdate,day)
            climatedata = db.get_obs_data(cityID,paramID,tdate,day,wmo=None)
	    #tempmittel = mitteltip.mitteltip(temp,'all',False,cityID,tdate)
            print(climatedata)


        #print db.get_obs_data(1,parameter,tdate,day,wmo=None)
