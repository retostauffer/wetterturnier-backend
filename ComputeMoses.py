# -------------------------------------------------------------------
# - NAME:        ComputeMoses.py
# - AUTHOR:      Reto Stauffer
# - DATE:        2014-09-19
# - LICENSE: GPL-3, Reto Stauffer, copyright 2014
# -------------------------------------------------------------------
# - DESCRIPTION: Compute Moses for the next tournament date.
#                Can be started several times. 
# -------------------------------------------------------------------
# - EDITORIAL:   2014-09-13, RS: Created file on thinkreto.
# -------------------------------------------------------------------
# - L@ST MODIFIED: 2018-01-09 21:12 on prognose2
# -------------------------------------------------------------------


# - Start as main script (not as module)
if __name__ == '__main__':

   import sys, os
   import numpy as np
   from glob import glob
   # - wetterturnier specific packages
   from pywetterturnier import utils, database, mitteltip
   from datetime import datetime as dt
   import numpy as np

   # - Evaluating input arguments
   inputs = utils.inputcheck('ComputeMoses')
   # - Read configuration file
   config = utils.readconfig('config.conf',inputs)
   
   # - Initializing class and open database connection
   db        = database.database(config)
   # - Loading tdate (day since 1970-01-01) for the tournament.
   #   Normaly Friday-Tornament (tdate is then Friday) while
   #   the bet-dates are for Saturday and Sunday if there was
   #   no input tournament date -t/--tdate.
   if config['input_tdate'] == None:
      tdates     = [db.current_tournament()]
   else:
      tdates     = [config['input_tdate']]

   # - Loading all different cities (active cities)
   cities     = db.get_cities()
   # - If input city set, then drop all other cities.
   if not config['input_city'] == None:
      tmp = []
      for elem in cities:
         if elem['name'] == config['input_city']: tmp.append( elem )
      cities = tmp

   # - If moses directory does not exist:
   if not os.path.isdir( config['data_moses'] ):
      utils.exit("Cannot find directory \"{0:s}\" which should contain ".format(config["data_moses"]) + \
               "the necessary coefficient-files for Moses! Stop!")

   # - Reading parameter list
   params = db.get_parameter_names(False)

   # ----------------------------------------------------------------
   # - Prepare the Moses
   # ----------------------------------------------------------------
   username = 'Moses'
   #db.create_user( username )
   moses_userID = db.get_user_id( username )

   # ----------------------------------------------------------------
   # - A small helper function to find the correct coefficient
   #   file. Klaus sends them once a week, normally on 
   #   Tuesday. The name of the file contains a date 
   #   but this is not the tournament date and normally
   #   the name of the files has 'a delay'.
   #   E.g., moses141128.bpw came in 2014-12-04 and therfore
   #         first time in use on the weekend of the 5th of 
   #         december. We have to find the correct one sutable
   #         for our tdate. This is important when
   #         re-computing the moses points somewhen.
   # ----------------------------------------------------------------
   def get_moses_file(tdate,city,offset=5):

      import re
      import datetime as dt

      # - Searching for the newest moses coefficient
      #   file.
      moses_files = glob( "{0:s}/moses*.{1:1s}pw".format(config['data_moses'], city['name'][0].lower()) )
      # - empty?
      if len( moses_files ) == 0:
         print '    %s\n' % 'Cannot find moses coefficients, skip'
         return( False )

      origin = dt.date(1970,1,1)
      moses_files.sort(reverse=True)

      # - Extract date from file name
      file_dates = []
      for file in moses_files:
         mtch = re.match( ".*moses([0-9]{6})\.\wpw$", file )
	 if not mtch is None:
	    file_dates.append( dt.datetime.strptime( mtch.group(1), "%y%m%d").date() )

      # Newest moses file
      newest      = max( file_dates )
      newest_file = "{0:s}/moses{1:s}.{2:1s}pw".format(
                    config['data_moses'], newest.strftime("%y%m%d"), city['name'][0].lower() )
      print "    Newest matching moses file: {0:s} ({1:s})".format(
                    newest.strftime("%Y-%m-%d"), newest_file )

      # If the file is too old: return FALSE. As the file should be computed
      # between each tournament it should never be older than 7 days, I take 5 here
      # just in case.
      if offset == False: return newest_file
      age = (dt.date.today() - newest).days
         
      # Drop a warning and return False if too old.
      if age > offset:
          print "[!] Problems with Moses: coefficient file too old ({0:d} days)".format(age)
          print "    Return 'False', Moses wont be computed!"
          return False

      # Else return file name of the newest file
      return newest_file


   # ----------------------------------------------------------------
   # - Moses: if a player used by the moses equation has not
   #   participated we have to fallback to the Petrus. Loading
   #   Petrus userID first.
   # ----------------------------------------------------------------
   petrus_userID = db.get_user_id( "Petrus" )
   if not petrus_userID:
      print "[!] Cannot find \"Petrus\" (User) needed for Moses. Stop script here."
      sys.exit(0)

   # ----------------------------------------------------------------
   # - Compute Moses for each city 
   # ----------------------------------------------------------------
   for city in cities:
      if config['input_alldates']:
         tdates = db.all_tournament_dates( city['ID'] )
         print 'ALL DATES'

      # -------------------------------------------------------------
      #  - Looping over tdates
      # -------------------------------------------------------------
      for tdate in tdates:
         bet = [{},{}]
         print '\n  * Compute the %s for city %s (ID: %d)' % (username,city['name'], city['ID']) 
      
         # - Searching sutable coefficient file
         #   ... WARNING 200 offset disabled, but we do have a problem
         #       at the moment to get the newest coefficients, so with offset false
         #       we are using old files.
         moses_file = get_moses_file(tdate,city, offset = False )
         if not moses_file: continue
   
         print '  * Found newest moses file %s' % moses_file
         mfid = open(moses_file,'r')
         moses_data = iter(mfid.read().split('\n'))
         moses = {}
         for param in params: moses[param] = {}
         for line in moses_data:
            if line.strip() in params:
               param=line.strip()
            elif len(line.split()) == 2:
               user = line.split()[1]
               if user == "Persistenz": user = "Donnerstag"
               moses[param][user] = line.split()[0]
            else: continue
         db.upsert_moses_coefs(city['ID'], tdate, moses)
#        moses = db.get_moses_coefs(city['ID'], tdate)
         print moses
         # -------------------------------------------------------------
         # - Looping over all parameters, search for Moses coefficients
         #   and try to find the bets of the users.
         for param in params:
            print param
            paramID = db.get_parameter_id( param )  
            for day in range(2):
               print "day %d" % int(day+1)
               bet[day][param] = np.array([])
               users           = moses[param]
               for user in users:
                  if user == "Persistenz": user = "Donnerstag" 
                  userID  = db.get_user_id( user )
                  groupID = db.get_user_id( "GRP_%s" % user )

                  if not userID: userID = groupID 

                  if not userID:
                     print '    - Problems getting userID for user %s' % (user)
                     utils.exit('Reto, should not happen. What doing now?')
                  
                     #   and parameter 'paramID' for day 'day'.
                     #   If there are no data, continue!
                  value = db.get_bet_data('user',userID,city['ID'],paramID,tdate,day+1)
                  coef  = moses[param][user]
                  # - If value is False the player did not submit his/her bet!
                  
                  if value == False: continue
                  else:
                     bet[day][param] = np.append( bet[day][param], np.repeat( value, int(float(coef)*100000) ) )
                     print bet[day][param]
               #   Use Petrus fallback.
               if len(bet[day][param]) == 0:
                  bet[day][param] = db.get_bet_data('user',petrus_userID,city['ID'],paramID,tdate,day+1)
            print bet
         bet = mitteltip.mitteltip(db,'moses',False,city,tdate,bet)
         print bet
      # - If bet is False, continue
         if bet == False: continue

      # -------------------------------------------------------------
      # - Inserting into database now
      # -------------------------------------------------------------
         print '    Inserting data into database now'
         for day in range(1,3):
            for k in bet[day-1].keys():
               paramID = db.get_parameter_id(k)
               db.upsert_bet_data(userID,city['ID'],paramID,tdate,day,bet[day-1][k])

   db.commit()
   db.close()

