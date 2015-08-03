# -------------------------------------------------------------------
# - NAME:        deadman.py
# - AUTHOR:      Reto Stauffer
# - DATE:        2014-09-20
# -------------------------------------------------------------------
# - DESCRIPTION: Computes mean bet (deadman) for a given tournament
#                date. All we need is to take mean and standard
#                deviation from the points and store them to the
#                deadman user. 
# -------------------------------------------------------------------
# - EDITORIAL:   2014-09-20, RS: Created file on thinkreto.
#                2014-11-09, RS: Used a copy of mitteltip.py
# -------------------------------------------------------------------
# - L@ST MODIFIED: 2014-09-20 18:27 on sculptor.uberspace.de
# -------------------------------------------------------------------

def deadman(db,city,tdate):

   import utils

   # - List element to store the two dict dbects
   #   containing the bets for the Deadman user
   bet = [{},{}]

   # - Day one, day two
   for day in range(1,3):

      print '    Compute for day %d (%s)' % (tdate+day, utils.tdate2string( tdate+day ))

      #paramnames = db.get_parameter_names()

      #for param in paramnames:

      #   # - Getting parameter ID
      #   paramID = db.get_parameter_id(param)
      #   print '    Compute Deadman for parameter %s (ID: %d)' % (param, paramID)

         mean = db.get_meansd_points(city['ID'],paramID,tdate,day)

      #   print mean
      #   import sys
      #   sys.exit()
      #   # - Store values
      #   #bet[day-1][param] = 


   return bet

