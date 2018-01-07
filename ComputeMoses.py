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
# - L@ST MODIFIED: 2018-01-07 16:25 on prognose2
# -------------------------------------------------------------------



# - Start as main script (not as module)
if __name__ == '__main__':

   import sys, os
   import numpy as np
   from glob import glob
   # - wetterturnier specific packages
   from pywetterturnier import utils
   from pywetterturnier import database
   from datetime import datetime as dt
   
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
      utils.exit("Cannot find directory \"%s\" which should contain " + \
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

      # - Searching for the newest moses coefficient
      #   file.
      moses_files = glob( "%s/moses*.%1spw" % (config['data_moses'], city['name'][0].lower()) )
      # - empty?
      if len( moses_files ) == 0:
         print '    %s\n' % 'Cannot find moses coefficients, skip'
         return( False )

      # - Else, ake the newest one
      import datetime as dt
      origin = dt.date(1970,1,1)
      moses_files.sort(reverse=True)
      for file in moses_files:
         try:
            date = file.split('moses')[1].split('.')[0]
         except:
            print '    Problems extracting date from %f in get_moses_files. Skip.' % file
            continue

         # - Convert the date
         try:
            year = 2000 + int(date[0:2])
            mon  = int(date[2:4])
            day  = int(date[4:])
            date = dt.date(year,mon,day)
         except:
            print '    Problems converting %s to date, skip' % date
            continue
         moses_tdate = (dt.date(year,mon,day)-origin).days
         if (moses_tdate - offset ) > tdate: continue
         
         # - Else return
         print '    Found sutable Moses file called %s' % file
         return( file )

      return( False ) # nothing found

   

   # ----------------------------------------------------------------
   # - Compute Moses for each tdate 
   # ----------------------------------------------------------------
   for tdate in tdates:

      # -------------------------------------------------------------
      #  - Looping over cities
      # -------------------------------------------------------------
      for city in cities:
      
         print '\n  * Compute the %s for city %s (ID: %d)' % (username,city['name'], city['ID']) 
      
         # - Searching sutable coefficient file
         moses_file = get_moses_file(tdate,city)
         if not moses_file: continue
   
         print '  * Found newest modes file %s' % moses_file
         mfid = open(moses_file,'r')
         moses_data = mfid.read().split('\n')

         if config["data_moses_out"]:
            fid = open("{0:s}/Moses_{1:s}.dat".format(config["data_moses_out"],city["name"]),"w")
            fid.write( "{0:30s} {1:s}\n".format("Moses coefficients from file",os.path.basename(moses_file)) )
            fid.write( "{0:30s} {1:s}\n".format("Processed",dt.now().strftime("%Y-%m-%d %H:%M")) )
            fid.write( "{0:30s} {1:s} ({2:d})\n".format("For city",city["name"],city["ID"]) )

            # Write file 1:1
            fid.write("\n")
            fid.write( "\n".join(moses_data) )
            fid.close()

         # -------------------------------------------------------------
         # - Looping over all parameters, search for Moses coefficients
         #   and try to find the bets of the users.
         # -------------------------------------------------------------
         # - The results dict, needed later
         res = {}
         for param in params:
   
            print '  - Scanning Moses parameter %s' % param
            # - Loading parameter ID
            paramID = db.get_parameter_id( param )
            param_found = False
   
            # - Looping over textfile content and search
            #   for the correct entries.
            for line in moses_data:
   
               # - Found the line (Beginning of the parameter block)
               if line.strip() == param:
                  print '    Found definition for this parameter, read coefficients now'
                  param_found = True
                  continue
   
               # - If we have not found the coefficient definiton block
               #   yet, just continue searching for it.
               if not param_found: continue
               # - If line is empty we are at the end of the
               #   Moses parameter coefficient block.
               if len(line.strip()) == 0: break 
   
               # - Here now reading the content of the Moses
               #   coefficients. We need one coeffcient (float)
               #   and a username.
               if param_found:
   
                  # - Parse the data from the line
                  try:
                     coef = float(line.split(' ')[0])
                     username = str(line.split(' ')[1])
                     nicename = utils.nicename( username )
                  except:
                     print '[!] Problems interpreting moses line: %s' % line
                     continue
   
                  # - Loading user ID. WARNING: could also be
                  #   a group. We have to search for both.
                  userID  = db.get_user_id( nicename )
                  groupID = db.get_user_id( "GRP_%s" % nicename )
   
                  if not userID: userID = groupID
   
                  if not userID:
                     print '    - Problems getting userID for user %s (%s)' % (nicename,username)
                     utils.exit('Reto, should not happen. What doing now?')
      
                  print '    - Moses coeff: %10.5f for userID %4d %s (%s)' % (coef,userID,nicename,username)
   
                  # - Loading bet value for bet date 1 and two
                  print '      | ', 
                  for day in range(1,3):
   
                     # - Initialize results dict for the current day
                     dayhash = "day_%d" % day
                     if not dayhash in res.keys():
                        res[dayhash] = {}
                     if not param   in res[dayhash].keys():
                        res[dayhash][param] = {"values":[],"coefficients":[]}
   
                     # - Loading forecasted values for user 'userID', city 'city['ID']
                     #   and parameter 'paramID' for day 'day'.
                     #   If there are no data, continue!
                     value = db.get_bet_data('user',userID,city['ID'],paramID,tdate,day)
                     if type(value) == type(bool()):
                        value = None
                     else:
                        value = float(value[0])
   
                     # - Append to results dict
                     res[dayhash][param]["values"].append( value )
                     res[dayhash][param]["coefficients"].append( coef )
   
                     # - Else (if there were data) we have to process them.
                     #   The final modes is value1*coef1 + value2*coef2 + ...
                     #   where we have to weight at the end if one of the
                     #   values was not available. 
                     if value == None:
                        print 'day%d %8s, ' % (day,"NONE"),
                     else:
                        print 'day%d %8.1f, ' % (day,value),
   
                  print ''
   
   
         # - Looping trough the results and start to process the data. 
         import re
         bet = {}; tmp = res.keys(); tmp.sort()
         for dayhash in tmp: 
   
            # - If this is a valid day hash
            if len(re.findall(r"^day_[0-9]",dayhash)) == 1:
               
               # - Extracting day as integer
               tmp = re.search(r".?[0-9]",dayhash)
               day = int(dayhash[tmp.start()+1:])
               print "    Found entries for day: %d" % day
               # - To store the moses bets for this day
               bet[dayhash] = {}
   
               # - Looping trough parameters
               for param in res[dayhash]:
   
                  val  = np.asarray( res[dayhash][param]['values'] )
                  coef = np.asarray( res[dayhash][param]['coefficients'] )
   
                  counter = 0; sum_val = None; sum_coef = None;
                  for i in range(0,len(val)):
                     # - If not valid: skip
                     if val[i] == None: continue
                     # - If first valid value: set sum_val and sum_coef
                     if not sum_val and not sum_coef:
                        sum_val = 0.; sum_coef = 0.
                     # - Add values to sum
                     sum_val  += val[i] * coef[i]
                     sum_coef += coef[i]
                     counter  += 1
                     
                  # - Compute final re-weighted value
                  if counter > 0:
                     final_value = sum_val / sum_coef
   
                     # - Bring to full tens
                     if param in ['N','ff','Wv','Wn','fx','dd']:
                        final_value = np.int(np.round(final_value/10.)*10)
                     else:
                        final_value = np.int(np.round(final_value))

                     # Iv Wv/Wv: if final_value < 4: set to o
                     if param in ['Wv','Wn'] and final_value > 0. and final_value < 40.:
                        print "    Wv/Wn is %d due to equation. Setting bet to 0!".format(
                                 int(final_value) )
                        final_value = 0.
   
                     print "    Final Moses value for day %d, param %-8s %8d (%d)" % \
                                 (day,param,final_value,counter)
                     # - Append result
                     bet[dayhash][param] = final_value
   
   
         # -------------------------------------------------------------
         # - Inserting into database now
         # -------------------------------------------------------------
         print '  * Inserting data into database now'
         for day in range(1,3):
            dayhash = "day_%d" % day
            for param in bet[dayhash].keys():
               paramID = db.get_parameter_id( param )
               #print moses_userID,city['ID'],paramID,tdate,day,bet[dayhash][param]
               db.upsert_bet_data(moses_userID,city['ID'],paramID,tdate,day,bet[dayhash][param])
   






   db.close()
