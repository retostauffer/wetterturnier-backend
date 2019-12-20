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
# - L@ST MODIFIED: 2018-12-16 11:47 on marvin
# -------------------------------------------------------------------

"""
Function to compute the mitteltipps. 

.. todo:: Could contain a bit more details!
"""

import utils
# - List element to store the two dict dbects
#   containing the bets for Petrus
bet = [{},{}]


def mitteltip(db,typ,ID,city,tdate,betdata=False):
   """Function returning Mitteltips or group bets.
  
   Args:
      db (:class:`database.database`): Database handler object.
      typ (:obj:`str`): Forwarded to :meth:`database.database.get_bet_data`. Please
            read the manual there for more information.
      ID (:obj:`int`): Forwarded to :meth:`database.database.get_bet_data`. Please
         read the manual there for more information.
      city (:obj:`int`): Numeric city ID.
      tdate (:obj:`int`): Tournament date. Days since 1970-01-01'
   
   Returns:
    dict: Contains the mitteltip.
   """

   import numpy as np

   # - Day one, day two
   for day in range(1,3):

      print '    Compute for day %d (%s)' % (tdate+day, utils.tdate2string( tdate+day ))

      #TODO shorten code for parameters with the same rule (like in old ComputePersistenz)
      #Freitag only gets calculated when the day is over (Saturday morning)
      #if typ=="persistenz": bet[day-1][param] = False

      # -------------------------------------------------------------
      # - Parameter N
      # -------------------------------------------------------------
      paramID = db.get_parameter_id('N')
      if betdata: data = betdata[day-1]['N']
      else: data = db.get_bet_data(typ,ID,city['ID'],paramID,tdate,day)
      if type(data) == type(bool()): return False
      for i in [0, 80, 90]:
         if float( len(np.where( data == i )[0]) ) / float( len(data) ) > 0.5:
            bet[day-1]['N'] = i; print "N = %d" % i
         else:
            bet[day-1]['N'] = np.round( np.mean(data), -1 )
            break

      # -------------------------------------------------------------
      # - Parameter TTd
      # -------------------------------------------------------------
      paramID = db.get_parameter_id('TTd')
      if betdata: data = betdata[day-1]['TTd']
      else: data = db.get_bet_data(typ,ID,city['ID'],paramID,tdate,day)
      if type(data) == type(bool()): return False
      bet[day-1]['TTd'] = np.round( np.mean(data), 0 )
   
      # -------------------------------------------------------------
      # - Parameter TTm
      # -------------------------------------------------------------
      paramID = db.get_parameter_id('TTm')
      if betdata: data = betdata[day-1]['TTm']
      else: data = db.get_bet_data(typ,ID,city['ID'],paramID,tdate,day)
      if type(data) == type(bool()): return False
      bet[day-1]['TTm'] = np.round( np.mean(data), 0 )
   
      # -------------------------------------------------------------
      # - Parameter TTn
      # -------------------------------------------------------------
      paramID = db.get_parameter_id('TTn')
      if betdata: data = betdata[day-1]['TTn']
      else: data = db.get_bet_data(typ,ID,city['ID'],paramID,tdate,day)
      if type(data) == type(bool()): return False
      bet[day-1]['TTn'] = np.round( np.mean(data), 0 )
   
      # -------------------------------------------------------------
      # - Parameter Sd
      # -------------------------------------------------------------
      paramID = db.get_parameter_id('Sd')
      if betdata: data = betdata[day-1]['Sd']
      else: data = db.get_bet_data(typ,ID,city['ID'],paramID,tdate,day)
      if type(data) == type(bool()): return False
      elif float( len(np.where( data == 0 )[0]) ) / float( len(data) ) > 0.5:
         bet[day-1]['Sd'] = 0
      else: bet[day-1]['Sd'] = np.round( np.mean(data), -1 )
   
      # -------------------------------------------------------------
      # - Parameter PPP
      # -------------------------------------------------------------
      paramID = db.get_parameter_id('PPP')
      if betdata: data = betdata[day-1]['PPP']
      else: data = db.get_bet_data(typ,ID,city['ID'],paramID,tdate,day)
      if type(data) == type(bool()): return False
      bet[day-1]['PPP'] = np.round( np.mean(data), 0 )
   
      # -------------------------------------------------------------
      # - Parameter ff
      # -------------------------------------------------------------
      paramID = db.get_parameter_id('ff')
      if betdata: ff = betdata[day-1]['ff']
      else: ff = db.get_bet_data(typ,ID,city['ID'],paramID,tdate,day)
      if type(ff) == type(bool()): return False
      bet[day-1]['ff'] = np.round( np.mean(ff), -1 )
   
      # -------------------------------------------------------------
      # - Parameter dd 
      # -------------------------------------------------------------
      paramID = db.get_parameter_id('dd')
      if betdata: dd = betdata[day-1]['dd']
      else: dd = db.get_bet_data(typ,ID,city['ID'],paramID,tdate,day)
      if type(dd) == type(bool()):
         return False
      dd = dd / 10.
      tips = len(dd)
      print "total dd tips:       %d" % tips
      n0 = len(np.where( dd == 0. )[0])
      n990 = len(np.where( dd == 990. )[0])
      print "n0   = %d" % n0
      print "n990 = %d" % n990
      #if the majority has 990 or 0 take this!
      
      if float( n0 ) / float(tips) > 0.5:
         bet[day-1]['dd'] = 0.; print "bet: %d" % 0
      elif float( n990 ) / float(tips) >= 0.5:
         bet[day-1]['dd'] = 9900.; print "bet: %d" % 990
      else:
         """
         TODO: We have to ensure (rule-wise and in bet mask) that NO ONE
         is allowed to bet and can possibly bet ff==0 but also dd!=0
         Also, tips with missing parameters have to be deleted completely!
         """
         u = 0; v = 0
         if len(dd) == len(ff) and typ != "moses":
            #not considering tips without direction for our weighted mean:
            for i in list(range(tips)):
               if dd[i] == 0 or dd[i] == 990 or ff[i] == 0:
                  np.delete(dd, i)
                  np.delete(ff, i)
            tips -= n0 + n990
            print "tips with direction: %d" % tips
            for i in list(range(len(dd))):
               if dd[i] == 0 or dd[i] == 990:
                  continue
               u += ff[i] * np.sin( np.deg2rad(dd[i]) ) 
               v += ff[i] * np.cos( np.deg2rad(dd[i]) )
            print "u = %f" % u
            print "v = %f" % v
            print "sum(ff) = %d" % sum(ff)
            u = u / float( sum(ff) * tips )
            v = v / float( sum(ff) * tips )
            print "u2 = %f" % u
            print "v2 = %f" % v         
         else:
            print "cannot link or weight dd with ff"
            for i in list(range(len(dd))):
               if dd[i] == 0 or dd[i] == 990:
                  continue
               u += np.sin( np.deg2rad(dd[i]) )
               v += np.cos( np.deg2rad(dd[i]) )
            print "u = %f" % u
            print "v = %f" % v
            u = u / float( tips )
            v = v / float( tips )
            print "u2 = %f" % u
            print "v2 = %f" % v

         bet[day-1]['dd'] = np.round( np.arctan2(u,v) * 1800. / np.pi, -2 )
         if bet[day-1]['dd'] < 0:
            bet[day-1]['dd'] = bet[day-1]['dd'] + 3600
         elif bet[day-1]['dd'] > 3600:
            bet[day-1]['dd'] = bet[day-1]['dd'] - 3600
         #dd can not be 0 as result of mean -> change to 360 degrees
         elif bet[day-1]['dd'] == 0:
            bet[day-1]['dd'] = 3600
   
      # -------------------------------------------------------------
      # - Parameter RR 
      # -------------------------------------------------------------
      paramID = db.get_parameter_id('RR')
      if betdata: data = betdata[day-1]['RR']
      else: data = db.get_bet_data(typ,ID,city['ID'],paramID,tdate,day)
      if type(data) == type(bool()): return False
      # - If more than 50% are -3, take -3.
      if float(len(np.where( data < 0. )[0])) / float(len(data)) > 0.5:
         bet[day-1]['RR'] = -30
      # - Else if more than 50% are 0, take it.
      elif float(len(np.where( data < 0. )[0])) / float(len(data)) > 0.5:
         bet[day-1]['RR'] = 0
      # - Else take mean value of all >= 0
      else:
         bet[day-1]['RR'] = np.round(np.mean(data[ np.where( data >= 0. ) ]),0)
   
      # -------------------------------------------------------------
      # - Parameter fx
      # -------------------------------------------------------------
      paramID = db.get_parameter_id('fx')
      if betdata: data = betdata[day-1]['fx']
      else: data = db.get_bet_data(typ,ID,city['ID'],paramID,tdate,day)
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
         print "    n0={0:d},  n4={1:d},  n5={2:d},  n6={3:d},  n7={4:d},  n8={5:d},  n9={6:d}".format(
                n0, n4, n5, n6, n7, n8, n9 )
         print "    n0+n4 = {0:d},  len(data) = {1:d},  (n0+n4)/len(data): {2:.3f}".format(
                (n0+n4), len(data), (n0+n4)/len(data))
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
      if betdata: data = betdata[day-1]['Wv']
      else: data = db.get_bet_data(typ,ID,city['ID'],paramID,tdate,day)
      if type(data) == type(bool()): return False
      bet[day-1]['Wv'] = WVhelper( data )
   
      paramID = db.get_parameter_id('Wn')
      if betdata: data = betdata[day-1]['Wn']
      else: data = db.get_bet_data(typ,ID,city['ID'],paramID,tdate,day)
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


def statistics(db,typ,ID,city,tdate,function=False,betdata=False):

   if not function:
      utils.exit( "No function given (min/max/np.median/...)" )
   params = db.get_parameter_names()
   for day in range(1,3):
      for param in params:
         paramID = db.get_parameter_id( param )
         if not betdata:
            data = db.get_bet_data(typ,ID,city['ID'],paramID,tdate,day)
         else: data = betdata[day-1][param]
         if type(data) == bool: return False
         bet[day-1][param] = function( data ) 

   return bet


def random(db,typ,ID,city,tdate,betdata=False):
   
   import numpy as np
   # - Day one, day two
   
   for day in range(1,3):

      print '    Compute for day %d (%s)' % (tdate+day, utils.tdate2string( tdate+day ))

      param = 'dd'
      paramID = db.get_parameter_id(param)
      dd = db.get_bet_data(typ,ID,city['ID'],paramID,tdate,day)
      if type(dd) == bool: return False
      max_dd, min_dd = max(dd), min(dd)
      if max_dd == min_dd: bet[day-1][param] = min_dd
      elif max_dd - min_dd < 1800:
         bet[day-1][param] = np.random.choice( np.arange(min_dd, max_dd+1, 100) )
      elif max_dd - min_dd > 1800:
         dd_list = []
         for i in range(int(max_dd), int(min_dd+3601), 100):
            if i > 3600: i -= 3600
            dd_list.append( i )
         bet[day-1][param] = np.random.choice( dd_list )
      else: bet[day-1][param] = np.random.choice( np.arange(100, 3601, 100) )

      for param in ["N","Sd","ff"]:
         paramID = db.get_parameter_id(param)
         data = db.get_bet_data(typ,ID,city['ID'],paramID,tdate,day)
         if type(data) == bool: return False
         min_data, max_data = min(data), max(data)
         if min_data == max_data:
            bet[day-1][param] = min_data
         elif param == "ff" and bet[day-1]["dd"] == 0:
            bet[day-1][param] = 0.
         elif param == "Sd":
            n0 = np.count_nonzero( data == 0 )
            p0 = n0 / float(len(data))
            if np.random.random() < p0:
               bet[day-1][param] = 0
         else:
            min_data = min(data[data > 0])
            bet[day-1][param] = np.random.randint( min_data, max_data )

      param = "fx"
      paramID = db.get_parameter_id(param)
      data = db.get_bet_data(typ,ID,city['ID'],paramID,tdate,day)
      if type(data) == bool: return False
      n0 = np.count_nonzero( data == 0 )
      p = n0 / float(len(data))
      if np.random.random() < p:
         bet[day-1][param] = 0.
      else:
         min_val = 250
         min_data = min(data[data>=min_val])
         max_data = max(data)
         if min_data == max_data:
            bet[day-1][param] = min_data
         else:
            bet[day-1][param] = np.random.randint( min_data, max_data )
 
      for param in ["Wv","Wn"]:
         paramID = db.get_parameter_id(param)
         data = db.get_bet_data(typ,ID,city['ID'],paramID,tdate,day)
         if type(data) == bool: return False
         W = []
         for i in data:
            if i not in W:
               W.append(i)
         if len(W) == 1:
            bet[day-1][param] = W[0]
         else:
            bet[day-1][param] = np.random.choice( W )

      param = 'RR'
      paramID = db.get_parameter_id(param)
      RR = db.get_bet_data(typ,ID,city['ID'],paramID,tdate,day)
      if type(data) == bool: return False
      max_RR = max(RR)
      RR_0 = RR[RR>=0]
      if len(RR_0) == 0:
         min_RR = -30
      else:
         min_RR = min(RR_0)
      if min_RR == max_RR:
         bet[day-1][param] = min_RR
      elif bet[day-1]["Wv"] > 40 or bet[day-1]["Wn"] > 40:
         bet[day-1][param] = np.random.choice( np.arange(min_RR, max_RR+1, 1) )
      else:
         n_3 = np.count_nonzero( RR == -30 )
         n0 = np.count_nonzero( RR == 0 )
         p_3 = n_3 / float(len(RR))
         p0 = n0 / float(len(RR))
         if np.random.random() < p_3:
            bet[day-1][param] = -30
         elif np.random.random() < p0:
            bet[day-1][param] = 0
         else:
            bet[day-1][param] = np.random.choice( np.arange(min_RR, max_RR+1, 1) )

      for param in ["PPP","TTm"]:
         paramID = db.get_parameter_id(param)
         data = db.get_bet_data(typ,ID,city['ID'],paramID,tdate,day)
         if type(data) == bool: return False
         max_data = max(data)
         min_data = min(data)
         if min_data == max_data:
            bet[day-1][param] = min_data
         else:
            bet[day-1][param] = np.random.choice( np.arange(min_data, max_data+1, 1) )

      for param in ["TTn","TTd"]:
         paramID = db.get_parameter_id(param)
         data = db.get_bet_data(typ,ID,city['ID'],paramID,tdate,day)
         if type(data) == bool: return False
         max_TTm = bet[day-1]["TTm"]
         min_data = min(data)
         max_data = max(data)
         if min_data == max_data:
            bet[day-1][param] = min_data
         elif max_data > max_TTm:
            bet[day-1][param] = np.random.choice( np.arange(min_data, max_TTm+1, 1) )
         else:
            bet[day-1][param] = np.random.choice( np.arange(min_data, max_data+1, 1) )

   return bet
