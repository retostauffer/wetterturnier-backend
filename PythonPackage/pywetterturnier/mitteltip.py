# -------------------------------------------------------------------
# - NAME:        mitteltip.py
# - AUTHOR:      Reto Stauffer
# - DATE:        2014-09-20
# -------------------------------------------------------------------
# - DESCRIPTION: Computes mean bet (mitteltips) for groups and
#                for petrus, depending on input.
# -------------------------------------------------------------------
# - EDITORIAL:   2014-09-20, RS: Created file on thinkreto.
# -------------------------------------------------------------------
# - L@ST MODIFIED: 2018-01-07 15:21 on marvin
# -------------------------------------------------------------------

def mitteltip(db,typ,ID,city,tdate):
   """!Function returning Mitteltips or group bets.
  
   @param db. Database handler object, see @ref database.database 
   @param typ. String. Forwarded to @ref database.database.get_bet_data. Please
      read the manual there for more information.
   @param ID. Integer. Forwarded to @ref database.database.get_bet_data. Please
      read the manual there for more information.
   @param city. Integer, city ID.
   @param tdate. Integer, tournament date. Days since 1970-01-01'
   @return dict containing the mitteltip.
   """

   import numpy as np
   import utils

   # - List element to store the two dict dbects
   #   containing the bets for Petrus
   bet = [{},{}]

   # - Day one, day two
   for day in range(1,3):

      print '    Compute for day %d (%s)' % (tdate+day, utils.tdate2string( tdate+day ))

      # -------------------------------------------------------------
      # - Parameter N
      # -------------------------------------------------------------
      paramID = db.get_parameter_id('N')
      data    = db.get_bet_data(typ,ID,city['ID'],paramID,tdate,day)
      if type(data) == type(bool()): return False
      bet[day-1]['N'] = np.round( np.mean(data), -1 )
   
      # -------------------------------------------------------------
      # - Parameter TTd
      # -------------------------------------------------------------
      paramID = db.get_parameter_id('TTd')
      data    = db.get_bet_data(typ,ID,city['ID'],paramID,tdate,day)
      if type(data) == type(bool()): return False
      bet[day-1]['TTd'] = np.round( np.mean(data), 0 )
   
      # -------------------------------------------------------------
      # - Parameter TTm
      # -------------------------------------------------------------
      paramID = db.get_parameter_id('TTm')
      data    = db.get_bet_data(typ,ID,city['ID'],paramID,tdate,day)
      if type(data) == type(bool()): return False
      bet[day-1]['TTm'] = np.round( np.mean(data), 0 )
   
      # -------------------------------------------------------------
      # - Parameter TTn
      # -------------------------------------------------------------
      paramID = db.get_parameter_id('TTn')
      data    = db.get_bet_data(typ,ID,city['ID'],paramID,tdate,day)
      if type(data) == type(bool()): return False
      bet[day-1]['TTn'] = np.round( np.mean(data), 0 )
   
      # -------------------------------------------------------------
      # - Parameter Sd
      # -------------------------------------------------------------
      paramID = db.get_parameter_id('Sd')
      data    = db.get_bet_data(typ,ID,city['ID'],paramID,tdate,day)
      if type(data) == type(bool()): return False
      bet[day-1]['Sd'] = np.round( np.mean(data), -1 )
   
      # -------------------------------------------------------------
      # - Parameter PPP
      # -------------------------------------------------------------
      paramID = db.get_parameter_id('PPP')
      data    = db.get_bet_data(typ,ID,city['ID'],paramID,tdate,day)
      if type(data) == type(bool()): return False
      bet[day-1]['PPP'] = np.round( np.mean(data), 0 )
   
      # -------------------------------------------------------------
      # - Parameter ff
      # -------------------------------------------------------------
      paramID = db.get_parameter_id('ff')
      data    = db.get_bet_data(typ,ID,city['ID'],paramID,tdate,day)
      if type(data) == type(bool()): return False
      bet[day-1]['ff'] = np.round( np.mean(data), -1 )
   
      # -------------------------------------------------------------
      # - Parameter dd 
      # -------------------------------------------------------------
      paramID = db.get_parameter_id('dd')
      data    = db.get_bet_data(typ,ID,city['ID'],paramID,tdate,day)
      if type(data) == type(bool()): return False
      data = data / 10.; u = 0 ; v = 0;
      for elem in data:
         u = u + np.sin( elem * np.pi / 180. )
         v = v + np.cos( elem * np.pi / 180. )
      u = u/float(len(data))
      v = v/float(len(data))
      bet[day-1]['dd'] = np.round( np.arctan2(u,v) * 1800. / np.pi, -2 )
      if bet[day-1]['dd'] < 0:
         bet[day-1]['dd'] = bet[day-1]['dd'] + 3600
      elif bet[day-1]['dd'] > 3600:
         bet[day-1]['dd'] = bet[day-1]['dd'] - 3600
   
      # -------------------------------------------------------------
      # - Parameter RR 
      # -------------------------------------------------------------
      paramID = db.get_parameter_id('RR')
      data    = db.get_bet_data(typ,ID,city['ID'],paramID,tdate,day)
      if type(data) == type(bool()): return False
      # - If more than 50% are 0, take 0.
      if float(len(np.where( data < 0. )[0])) / float(len(data)) > 0.5:
         bet[day-1]['RR'] = -30
      # - Else take mean value of all >= 25
      else:
         bet[day-1]['RR'] = np.round(np.mean(data[ np.where( data >= 0. ) ]),0)
   
      # -------------------------------------------------------------
      # - Parameter ffx
      # -------------------------------------------------------------
      paramID = db.get_parameter_id('fx')
      data    = db.get_bet_data(typ,ID,city['ID'],paramID,tdate,day)
      if type(data) == type(bool()): return False
      # - If more than 50% are 0, take 0.
      if float(len(np.where( data < 25. )[0])) / float(len(data)) > 0.5:
         bet[day-1]['fx'] = 0
      # - Else take mean value of all >= 25
      else:
         bet[day-1]['fx'] = np.round(np.mean(data[ np.where( data >= 25. ) ]), -1 )
   
      # -------------------------------------------------------------
      # - Parameter Wv and Wn 
      # -------------------------------------------------------------
      def WVhelper(data):

         # - Count values first
         data = np.round(data / 10.,0)
         n0 = len(np.where(data == 0.)[0])
         n4 = len(np.where(data == 4.)[0])
         n5 = len(np.where(data == 5.)[0])
         n6 = len(np.where(data == 6.)[0])
         n7 = len(np.where(data == 7.)[0])
         n8 = len(np.where(data == 8.)[0])
         n9 = len(np.where(data == 9.)[0])
         ##print "    n0={0:d},  n4={1:d},  n5={2:d},  n6={3:d},  n7={4:d},  n8={5:d},  n9={6:d}".format(
         ##       n0, n4, n5, n6, n7, n8, n9 )
         ##print "    n0+n4 = {0:d},  len(data) = {1:d},  (n0+n4)/len(data): {2:.3f}".format(
         ##       (n0+n4), len(data), (n0+n4)/len(data))
         # - Decision 0,4 .vs. 5,6,7,8,9
         if float(n0+n4) / float(len(data)) > 0.5:
            if n4 >= n0:
               return 40.
            else:
               return 0.
         # - Decision 5,6,7 .vs. 8,9
         elif (n5+n6+n7) > (n8+n9):
            if (n5+n6) > n7 and n5 > n6:
               return 50.
            elif (n5+n6) > n7:
               return 60.
            else:
               return 70.
         # - Else we have to decide 8 or 9
         else:
            if n8 > n9:
               return 80.
            else:
               return 90.
   
      paramID = db.get_parameter_id('Wv')
      data    = db.get_bet_data(typ,ID,city['ID'],paramID,tdate,day)
      if type(data) == type(bool()): return False
      bet[day-1]['Wv'] = WVhelper( data )
   
      paramID = db.get_parameter_id('Wn')
      data    = db.get_bet_data(typ,ID,city['ID'],paramID,tdate,day)
      if type(data) == type(bool()): return False
      bet[day-1]['Wn'] = WVhelper( data )

   # - Show the tip 
   print ''
   print '    Bet for %s' % utils.tdate2string( tdate + 1 ),
   print '    Bet for %s' % utils.tdate2string( tdate + 2 )
   for k in bet[0].keys():
      print '    - %-5s %5d' % (k,bet[0][k]),
      print '         - %-5s %5d' % (k,bet[1][k])
   print ''



   return bet

