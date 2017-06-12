# -------------------------------------------------------------------
# - NAME:        judgingclass.py
# - AUTHOR:      Reto Stauffer
# - DATE:        2014-09-21
# -------------------------------------------------------------------
# - DESCRIPTION: This is the judgingclass with the rules used
#                after 2002-12-06.
#                Note: you can simply make a copy of this
#                class, adapt the scoring rules. Furthermore you
#                have to define/change/adapt the rule in the
#                ComputePoints.py script.
# -------------------------------------------------------------------
# - EDITORIAL:   2014-09-21, RS: Created file on thinkreto.
# -------------------------------------------------------------------
# - L@ST MODIFIED: 2017-06-12 16:52 on prognose2.met.fu-berlin.de
# -------------------------------------------------------------------

# - Need numpy everywhere
import numpy as np

class judging(object):
   """!This is a judgingclass - a class used to compute the points
   a user gets on a specific weekend. Please note that it is possible
   that the rules change somewhen and that there is a second judgingclass.
   
   The class contains public attributes tdate_min and tdate_max as a
   safety-instrument. As soon as you would like to compute points
   for a specific tournament which falls outside this limits the script
   will stop in the operational mode not to re-compute old bets with
   a wrong judgingclass.
   """

   # ----------------------------------------------------------------
   # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
   # Additional safety thing. If set (not NONE)
   # These settings will be checked when method get_points is called
   # with tdate input. In this case: 
   #  - if tdate is smaller than tdate_min    --> ERROR
   #  - if tdate bigger or equal to tdate_max --> ERROR
   # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
   # If you create a new judging class please modify not only 
   # tdate_min of the new class, be sure that you also set the
   # tdate_max in the old judgingclass to avoid that older tournament
   # dates can be based on the wrong judgingclass.
   # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
   # ----------------------------------------------------------------

   ## Do not use this judgingclass in the operational mode for tournaments
   #  smaller or equal to this date (days since 1970-01-01).
   tdate_min = 12027
   ## If set - do not use this judgingclass in the operational mode
   #  for tournaments > this date (days sicne 1970-01-01).
   tdate_max = None

   def __init__(self,quiet=False):
      """!Initialize new juding object.
      @param quiet. Boolean, default is False. Redudes the output
         to a minimum if set to True. Used for some applications.
      @note actually I would like to connect this script to a php
         scrpt to give the users the oportunity to 'test' the 
         judgingclass. And therefore the script has to be quiet and
         just prints what I need. Not done yet.
      """

      if not quiet:
         print '    Initializing judging class 2002-12-06 py'
      self.quiet = quiet

   # ----------------------------------------------------------------
   # - Prepares data to insert them into the database.
   #   Creates list tuple out of two lists.
   # ----------------------------------------------------------------
   def _prepare_for_database_(self,userID,cityID,paramID,tdate,betdate,values):
      """!Prepares ID/value pairs for database.
      Creates a tuple list which can be used with
      @b database.database.executemany. Used later with
      the method 'points_to_database' within this class to update
      the bets table.
      @param userID, cityID, paramID, tdate, betdate. Lists containing integers,
         all these integers define the 'unique key' in the database.
      @param values. List containing numeric values connected to the ID's.
      """

      if not len(userID) == len(values):
         utils.exit('In judging.prepare_for_database got different lengths of userIDs and values!')

      # - Create result
      res = []
      for i in range(len(values)):
         res.append( (values[i],userID[i],cityID[i],paramID[i],tdate[i],betdate[i]) )

      return res

   
   # ----------------------------------------------------------------
   # - Inserts data into database. They have to be prepared
   # ----------------------------------------------------------------
   def points_to_database(self,db,userID,cityID,paramID,tdate,betdate,values):
      """!Updates the bets database.
      @param userID, cityID, paramID, tdate, betdate. Lists containing integers,
         all these integers define the 'unique key' in the database.
      @param values. List containing numeric values connected to the ID's.
      """

      # - Prepare tuple list object
      data = self._prepare_for_database_(userID,cityID,paramID,tdate,betdate,values)

      sql = 'UPDATE '+db.prefix+'wetterturnier_bets SET points = %s ' + \
            'WHERE userID=%s and cityID=%s and paramID=%s and tdate=%s and betdate=%s'

      cur = db.cursor()
      cur.executemany( sql, data )
      

   # ----------------------------------------------------------------
   # - Handling all different point computation methods.
   #   Stops if there is an undefined class.
   # ----------------------------------------------------------------
   def get_points(self,obs,what,data,special=None,tdate=None):

      import utils
      import numpy as np

      # - If tdate is set: check if this special date is
      #   allowed in this judgingclass or not. Please note
      #   that this is not used in the TestPoints.py case.
      if not tdate == None:
         if not self.tdate_min == None:
            if self.tdate_min > tdate:
               import sys
               utils.exit("judgingclass %s not allowed for tournament date %d" % \
                        (__name__,tdate))
         if not self.tdate_max == None:
            if self.tdate_max <= tdate:
               import sys
               utils.exit("judgingclass %s not allowed for tournament date %d" % \
                        (__name__,tdate))

      # - What to plot?
      method_to_use = '__points_%s__' % what

      # - Not available?
      if not method_to_use in dir(self):
         utils.exit('Method %s does not exist in judgingclass' % method_to_use)


      # - Loading method dynamical and call it.
      if not self.quiet:
         print '    - Using method: %s' % method_to_use
      call = getattr(self,method_to_use)
      return np.round( call(obs,data,special), 2 )


   # -----------------------------------------------------------------
   # - Compute residuals
   # -----------------------------------------------------------------
   def __residuals__(self,obs,data):

      # - Observations min/max. If it is only one value min is
      #   equal to max.
      obs  = np.asarray(obs)
      min  = np.min(obs)
      max  = np.max(obs)

      # - Compute residuals
      resid = np.ndarray(len(data),dtype='float'); resid[:] = -999.
      resid[ np.where(np.logical_and(data >= min, data <= max)) ] = 0.
      resid[ np.where(data < min) ] = np.abs(min - data[ np.where(data < min) ])
      resid[ np.where(data > max) ] = np.abs(max - data[ np.where(data > max) ])

      return resid

   # ----------------------------------------------------------------
   # - Compute TTm (maximum temperature) points
   #   Compute TTn (minimum temperature) points
   #   Compute TTd (dewpoint temperature) points
   #   - They are using the same method (forwarding)
   # ----------------------------------------------------------------
   def __points_TTm__(self,obs,data,special):
      return self.__points_TTmTTnTTd__(obs,data,special,0.3)
   def __points_TTn__(self,obs,data,special):
      return self.__points_TTmTTnTTd__(obs,data,special,0.3)
   def __points_TTd__(self,obs,data,special):
      return self.__points_TTmTTnTTd__(obs,data,special,0.2)
   # - Here TTm and TTn are getting computed
   def __points_TTmTTnTTd__(self,obs,data,special,factor):

      if not self.quiet:
         print '    - Called TTm/TTn/TTd point computation method'
      data   = np.asarray(data)
      resid  = self.__residuals__(obs,data)

      # - Full points
      points = np.ndarray(len(data),dtype='float'); points[:] = 10.
      # - Deduction for the first 10 tenth
      #   Minus 0.1 Points for each difference unit
      points = points - np.minimum( resid, 10. )*0.1
      # - Deduction for the rest
      #   Minus 0.3 points for each difference unit
      points = points - np.maximum( resid - 10., 0. )*factor

      # - Show data (development stuff)
      #for i in range(len(data)):
      #   print '%5d %5d %6.2f' % (data[i], resid[i], points[i])
      return points


   # ----------------------------------------------------------------
   # - Compute N (cloud cover) points 
   # ----------------------------------------------------------------
   def __points_N__(self,obs,data,special):

      if not self.quiet:
         print '    - Called N point computation method'
      data   = np.asarray(data)
      resid  = self.__residuals__(obs,data)

      # - Full points
      points = np.ndarray(len(data),dtype='float'); points[:] = 6.
      # - For a difference of 1-3 (10 - 30 in difference units)
      #   deduction of 1 per difference unit.
      idx = np.where(np.logical_and(resid > 0, resid < 30))
      points[idx] = points[idx] - resid[idx]/10.
      #   Minus 4 points if residual is 3 (30) 
      idx = np.where(resid == 30)
      points[idx] = points[idx] - 4. 
      #   Minus 6 points if residual is 4 (40) 
      idx = np.where(resid >= 40)
      points[idx] = points[idx] - 6. 
      # - Special: if observation was 0 or 8 and the 
      #   residual is not equal to 0: subtract one
      #   more point.
      obs    = np.asarray(obs); min = np.min(obs); max = np.max(obs)
      if min == 80. or max == 0.:
         idx = np.where(resid > 0)
         points[idx] = points[idx] - 1.

      # - Points cannot be negative
      points = np.maximum( points, 0)

      # - Show data (development stuff)
      #for i in range(len(data)):
      #   print '%2d|%2d:  %2d %2d %6.2f' % (min/10., max/10., data[i]/10., resid[i]/10., points[i])
      return points


   # ----------------------------------------------------------------
   # - Compute Sd (sunshine duration) points 
   # ----------------------------------------------------------------
   def __points_Sd__(self,obs,data,special):

      if not self.quiet:
         print '    - Called Sd point computation method'
      data   = np.asarray(data)
      resid  = self.__residuals__(obs,data)

      # - Full points
      points = np.ndarray(len(data),dtype='float'); points[:] = 5.
      # - Deduction for each percent. 
      #   Minus 0.01 Points for each difference unit
      #   Note: i store 1/10 percent in the database.
      points = points - resid*0.01
      # - If user bet was wrong (resid > 0) and one of the
      #   observations was 0 (0%) or 10 (1%): subtract additional 1.5 points. 
      obs    = np.asarray(obs); min = np.min(obs); max = np.max(obs)
      # - Additinoal 1.5 points less between observed 0% and bet 1% or
      #   higher the other way around.
      # - minus 1.5 points. Why + 0.1? I allready subtracted
      #   0.1 points because 0/10 makes 10 difference units times
      #   0.01 above makes 0.1 points deduction. Therefore I
      #   have to subtract only 1.5 additional points here.
      idx = np.where( np.logical_and(max == 0., data > 0.) )
      points[idx] = points[idx] - 1.5 + 0.1
      # - The same the other way around
      idx = np.where( np.logical_and(min > 0., data == 0.) )
      points[idx] = points[idx] - 1.5 + 0.1

      # - Cannot be negative
      points = np.maximum( points, 0)

      # - Show data (development stuff)
      #for i in range(len(data)):
      #   print '%3d|%3d:  %3d %3d %6.2f' % (min/10., max/10., data[i]/10., resid[i]/10., points[i])
      return points


   # ----------------------------------------------------------------
   # - Compute dd (wind direction) 
   # ----------------------------------------------------------------
   def __points_dd__(self,obs,data,special):

      if not self.quiet:
         print '    - Called dd point computation method'
      data   = np.asarray(data)
      obs    = np.asarray(obs);
      try:
         min = np.min(obs[np.where( np.logical_and(obs > 0., obs <= 3600. ))])
      except:
         min = None
      try:
         max = np.max(obs[np.where( np.logical_and(obs > 0., obs <= 3600. ))])
      except:
         max = None
      # - Change minimum if angle (difference) is bigger than 180 degrees.
      if not max == None and not min == None:
         if max - min > 1800.:
            tmp = max
            max = min + 3600.
            min = tmp 
      # - If min or max is none, min and max are equal
      if not min == None and max == None: max = min
      if min == None and not max == None: min = max

      # - Lowest observed wind speed. Has to be on speical!
      #   If nothing is observed, assume ffmin == 0 (gives
      #   less negative points, however, that is not the players
      #   fault if there is no ff observation).
      if len(special) == 0:
         ffmin = 0
      else:
         ffmin = np.min( special )

      # - Max points
      maxpoints = 9.
      #   Give everyone max points at the beginning
      p_normal  = np.ndarray( len(data), dtype='float'); p_normal[:]   = -999.
      p_special = np.ndarray( len(data), dtype='float'); p_special[:]  = -999.
      all_resid = np.zeros( len(data), dtype='float')

      # - Checking if we have had calm and/or variable conditions
      calm = False; variable = False; normal = False
      #falsch#if len( np.where(obs ==    0.)[0] ) > 0:                           calm     = True
      #falsch#if len( np.where(obs == 9900.)[0] ) > 0:                           variable = True
      if len( np.where(obs ==    0.)[0] ) == len(obs):                    calm     = True
      if len( np.where(obs == 9900.)[0] ) == len(obs):                    variable = True
      if len( np.where( np.logical_and(obs > 0., obs <= 3600.) )[0] ) > 0: normal = True

      # -------------------------------------------------------------
      # - Compute the normal residuals for dd if and only if
      #   there were "normal" dd observations.
      # -------------------------------------------------------------
      if normal:
         idx = np.where( np.logical_and( data > 0., data <= 3600. ) )

         # - If we do have two 'normal' observations and the difference
         #   is exactely 180 degrees all degree-bets are in between the
         #   two observations (there is no 'good' or 'bad' side - clock
         #   or counter clock wise).
         dd_min  = np.min( obs[np.where(np.logical_and(obs > 0.,obs<=3600.))] )
         dd_max  = np.max( obs[np.where(np.logical_and(obs > 0.,obs<=3600.))] )
         dd_diff = np.abs( dd_min-dd_max )
         
         if len(idx[0]) > 0:
            # - Normal penalty
            #   If minimum wind was less than 6kt: 1.0 points per 10 deg
            #   If minimum wind was >=        6kt: 0.5 points per 10 deg
            #   Please note that the 'data' (bets) are in 1/10th of degrees
            #   and therefore 1.0/100. = 0.01, 0.5/100. = 0.005
            if dd_diff == 1800.: 
               p_normal[idx]  = maxpoints
               all_resid[idx] = 0. 
            else:
               the_obs = np.asarray([min,max]) 
               residA = self.__residuals__(the_obs-3600.,data[idx])
               residB = self.__residuals__(the_obs,      data[idx])
               residC = self.__residuals__(the_obs+3600.,data[idx])
               resid  = np.minimum(residA,residB)
               resid  = np.minimum(resid, residC)
               if ffmin < 60.:
                  p_normal[idx] = maxpoints - resid*0.005
               else:
                  p_normal[idx] = maxpoints - resid*0.01

               all_resid[idx] = resid

      # -------------------------------------------------------------
      # - Deduction for people forecasted 0/990 (if wrong)
      #         forecast   observed    deduction
      #        ----------------------------------
      #   (a)        0.       9900.        5
      #   (b)     9900.          0.        5
      #   (c)   0/9900.   >0/<3600.        7
      #   (d)   0/9900.   >0/<3600.        7
      #        ----------------------------------
      # -------------------------------------------------------------
      if calm or variable:
         if calm:
            # - Full points for people obs 0 and forecast 0
            p_special[np.where( data == 0. )] = maxpoints
            # - If calm observed but forecast was in between >0/<=3600: -7
            idx = np.where( np.logical_and( data > 0., data <= 3600. ) )
            p_special[idx] = maxpoints - 7
            # - If calm observed but 9900 forecasted: -5
            idx = np.where( data == 9900. )
            p_special[idx] = maxpoints - 5
         if variable:
            # - Full points for people obs 9900 and forecast 9900
            p_special[np.where( data == 9900. )] = maxpoints
            # - If variable observed but forecast was in between >0/<=3600: -7
            idx = np.where( np.logical_and( data > 0., data <= 3600. ) )
            p_special[idx] = maxpoints - 7
            # - If variable observed but 0 forecasted: -5
            idx = np.where( data == 0. )
            p_special[idx] = maxpoints - 5
      # - If 0 forecasted but not 'normal' wind direction observed 
      if not calm:
         idx = np.where( data == 0. )
         p_special[idx] = maxpoints - 7
      # - If 9900 forecasted but not 'normal' wind direction observed 
      if not variable:
         idx = np.where( data >= 9900. )
         p_special[idx] = maxpoints - 7

      # - Now take maximum points
      points = np.maximum( p_special, p_normal )
      points = np.maximum( points, 0 )

      # - Show data (development stuff)
      #print "  FFMIN: %7.2f" % ffmin
      #if calm:     print '  CALM CONDITION TRUE'
      #if variable: print '  VARIABLE CONDITION TRUE'
      #print obs
      #print min, max
      #if min == None and max == None:
      #   for i in range(len(data)):
      #      print '--- | ---  bet %3d %6.2f | n: %7.2f s: %7.2f | %7.2f' \
      #             % (data[i]/10., all_resid[i]/100, p_normal[i], p_special[i], points[i])
      #else:
      #   for i in range(len(data)):
      #      print '%3d|%3d:  bet %3d %6.2f | n: %7.2f s: %7.2f | %7.2f' \
      #             % (min/10., max/10., data[i]/10., all_resid[i]/100, p_normal[i], p_special[i], points[i])
      return points


   # ----------------------------------------------------------------
   # - Compute ff (mean wind speed) points 
   # ----------------------------------------------------------------
   def __points_ff__(self,obs,data,special):

      if not self.quiet:
         print '    - Called ff point computation method'
      data   = np.asarray(data)
      resid  = self.__residuals__(obs,data)

      # - Full points
      points = np.ndarray(len(data),dtype='float'); points[:] = 6.
      # - Deduction
      #   Minus 0.1 Points for each difference unit
      points = points - resid*0.1

      # - Show data (development stuff)
      #for i in range(len(data)):
      #   print '%5d %5d | %5d %5d %6.2f' % (np.min(obs), np.max(obs), data[i], resid[i], points[i])
      return points

   # ----------------------------------------------------------------
   # - Compute fx (wind gusts) points 
   # ----------------------------------------------------------------
   def __points_fx__(self,obs,data,special):

      # - Getting min and max from the obs
      data   = np.asarray(data)
      obs    = np.asarray(obs);
      min = np.min(obs)
      max = np.max(obs)

      # - To avoid wrong inputs: knots below 25 (250.)
      #   are set to 0!
      data[np.where( data < 250. )] = 0

      if not self.quiet:
         print '    - Called fx point computation method'
      data   = np.asarray(data)
      resid  = self.__residuals__(obs,data)

      # - Full points
      maxpoints = 4.
      points = np.ndarray(len(data),dtype='float'); points[:] = maxpoints
      # - Default mode is minus 0.25 Points 
      #   for the first 0-15 knots difference, afterwards
      #   minus 0.5 points for all above 15 knots difference. 
      def normal_penalty( resid ):
         return np.minimum( resid, 150. )*0.025 + np.maximum( resid-150., 0)*0.05

      # - Non-special penalty is if fx >= 250 and forecast >= 250 (250=25kt)
      if max >= 250.:
         idx = np.where( data >= 250. )
         points[idx] = points[idx] - normal_penalty( resid[idx] )

      # - For these where forecast (data) was 0. but obs was >= 250:
      #   Special rule. First: -3 points and then normal penalty
      #   for residuals - 250.
      idx = np.where( np.logical_and( data == 0, min >= 250. ) )
      points[idx] = maxpoints - 3 - normal_penalty( np.maximum(resid[idx]-250.,0) )
      # - For these where forecast (data) was >= 250. but obs was == 0:
      #   Special rule. First: -3 points and then normal penalty
      #   for residuals - 250.
      idx = np.where( np.logical_and( data >= 250, max == 0. ) )
      points[idx] = maxpoints - 3 - normal_penalty( np.maximum(resid[idx]-250.,0) )

      # - Now correcting:
      #   For all resid == 0: set points to maxpoints.
      idx = np.where( resid == 0. )
      points[idx] = maxpoints

      # - Show data (development stuff)
      #for i in range(len(data)):
      #   print '%5d %5d | %5d %5d %6.2f' % (min, max, data[i], resid[i], points[i])
      return points

   # ----------------------------------------------------------------
   # - Compute Wv (maximum temperature) points
   #   Compute Wv (minimum temperature) points
   #   - They are using the same method (forwarding)
   # ----------------------------------------------------------------
   def __points_Wv__(self,obs,data,special):
      return self.__points_WvWn__(obs,data,special)
   def __points_Wn__(self,obs,data,special):
      return self.__points_WvWn__(obs,data,special)
   # - Here Wn and WvWn are getting computed
   def __points_WvWn__(self,obs,data,special):

      if not self.quiet:
         print '    - Called WvWn point computation method'
      data   = np.asarray(data)

      # Deduction matrix list. Note that 1/2/3 will never be
      # ranked (and cannot be forecasted). If something is wrong
      # with my judgment class this leads to -89 points. If this
      # occures we have to check this stuff.
      #        bet was  0   1   2   3   4   5   6   7   8   9
      point_matrix = [[ 0.,99.,99.,99., 5., 7., 7., 7., 6., 6.,], # observed 0
                      [99.,99.,99.,99.,99.,99.,99.,99.,99.,99.,], # observed 1
                      [99.,99.,99.,99.,99.,99.,99.,99.,99.,99.,], # observed 2
                      [99.,99.,99.,99.,99.,99.,99.,99.,99.,99.,], # observed 3
                      [ 8.,99.,99.,99., 0., 3., 5., 5., 9., 9.,], # observed 4
                      [10.,99.,99.,99., 3., 0., 2., 4., 6., 8.,], # observed 5
                      [10.,99.,99.,99., 6., 1., 0., 3., 3., 4.,], # observed 6
                      [10.,99.,99.,99., 6., 4., 4., 0., 3., 4.,], # observed 7
                      [ 7.,99.,99.,99., 8., 5., 2., 2., 0., 2.,], # observed 8
                      [ 8.,99.,99.,99., 9., 7., 5., 6., 3., 0.,]] # observed 9

      # - Start with -999 Points (should never stay negative - else we do
      #   have a but.
      points = np.ndarray(len(data),dtype='float'); points[:] = -999

      # - Compute points for all observations and always take
      #   the maximum of these.
      for o in obs:
         for i in range(len(data)):
            #            maxpoints -              observed      bet value
            tmp       =     10    - point_matrix[int(o/10)][int(data[i])/10]
            # Minimum points: 0!
            if tmp < 0:
               points[i] = 0.
            if tmp > points[i]:
               points[i] = tmp

      # - Show data (development stuff)
      #for i in range(len(data)):
      #   omin = np.min( np.asarray(obs) )
      #   omax = np.max( np.asarray(obs) )
      #   print 'obs: %5d %5d bet: %5d %6.2f' % (omin, omax, data[i], points[i])
      return points

   # ----------------------------------------------------------------
   # - Compute PPP (station pressure) points 
   # ----------------------------------------------------------------
   def __points_PPP__(self,obs,data,special):

      if not self.quiet:
         print '    - Called PPP point computation method'
      data   = np.asarray(data)
      resid  = self.__residuals__(obs,data)

      # - Full points
      points = np.ndarray(len(data),dtype='float'); points[:] = 10.
      # - Deduction
      #   Minus 0.1 points for each unit difference (bets are stored in hPa*10)
      points = points - resid*0.1

      # - Show data (development stuff)
      #for i in range(len(data)):
      #   print '%5d %5d %6.2f' % (data[i], resid[i], points[i])
      return points


   # ----------------------------------------------------------------
   # - Compute RR (precipitation) points 
   # ----------------------------------------------------------------
   def __points_RR__(self,obs,data,special):


      # - Getting min and max from the obs
      data   = np.asarray(data)
      obs    = np.asarray(obs);
      min = np.min(obs)
      max = np.max(obs)

      if not self.quiet:
         print '    - Called RR point computation method'
      data   = np.asarray(data)
      # - WARNING: compute residuals only to 0mm observation!
      #   The penalty for observed -3.0 will be added later on.
      resid  = self.__residuals__(np.maximum(obs,0),np.maximum(data,0))

      # - Maximum number of points to reach
      maxpoints = 10.
      deduction = np.zeros(len(data),dtype='float'); deduction[:] = 0. 

      # - Precipitation scoring is quiet fancy. I am doing this
      #   with a vector defining the penalty for different
      #   amounts of OBSERVED prcipitation and its penalties.
      #   If observation is 0.0: start from zero element (giving the 1.0 points penalty)
      #   If observation is 0.1: start from first element (giving 0.1 points penalty)
      #   .. up to 5.0. Afterwards the user gets 0.05 points penalty for each difference.
      full_penalty = np.zeros( (50), dtype='float' );
      full_penalty[0] = 1.
      full_penalty[1:] = 0.1

      # -------------------------------------------------------------
      # - For players ABOVE the maximum, compute points:
      # -------------------------------------------------------------
      # - Now take the penalty vector if max is in that range.
      if max < 0:
         penalty = full_penalty
      elif max < len(full_penalty):
         penalty = full_penalty[max:]
      else:
         penalty = []

      idx = np.where( data > max )[0]
      # - For the first len(penalty) deviances
      if len(penalty) > 0:
         for i in idx:
            imax = int( np.minimum( resid[i], len(penalty) ) )
            deduction[i] = deduction[i] + np.sum(penalty[0:imax])
      # - For these with more difference as len(penalty)-1
      deduction[idx] = deduction[idx] + np.maximum(0,resid[idx]-len(penalty)) * 0.05
      # - Only half points deduction for all forecasted values >= 0.1mm
      #   if and only if the forecast was bigger than the observed values.
      idx = np.where( np.logical_and( deduction > 0., data > max, data > 0 ) )
      deduction[idx] = deduction[idx] * 0.5
      # - PROBLEM: if data == 0 and max > 0 the user gehts
      #   1.0 points deduction between 0.0 and 0.1 mm. BUT
      #   I devided the points by 2. This does not yield
      #   for the first point 1.0 between 0.0 and 0.1. Therefore  
      #   we have to add 0.5 points (half of 1.0) again if
      #   - User forecast was == 0
      #   - Observed maximum was > 0 (bigger than forecast)
      #   - Deduction is not equal to 0.
      if len(penalty) > 0:
         if penalty[0] == 1.:
            idx = np.where( np.logical_and( deduction > 0., data > max ) )
            deduction[idx] = deduction[idx] + 0.5

      # -------------------------------------------------------------
      # - For players BELOW the minimum, compute points:
      # -------------------------------------------------------------
      # - Now take the penalty vector from user tip
      #   up to minimum observed value BUT tip was not -3.0mm
      idx = np.where( data < min )[0]
      imax = np.minimum( min, len(full_penalty) )
      for i in idx:
         imin = np.maximum( data[i], 0 )
         deduction[i] = deduction[i] + np.sum( full_penalty[imin:imax] )
      if min > 50.:
         tmp = self.__residuals__( min, np.maximum(50, data[idx]) )
         deduction[idx] = deduction[idx] + tmp * 0.05

      # - Special case: min(obs) was >= 0 but forecast was -3.0
      #   remove 3 more points.
      if min >= 0:
         idx = np.where( data < 0)
         deduction[idx] =  deduction[idx] + 3 
      # - Same for case: max(obs) was < 0 (-3.0) but forecast was >=0
      if max < 0:
         idx = np.where( data >= 0)
         deduction[idx] = deduction[idx] + 3

      # - Compute points and round to one tenth
      ####deduction = np.round( deduction, 1 )
      points = maxpoints - deduction

      # - Show data (development stuff)
      #if min >=0: print ' WET CONDITIONS'
      #if max < 0: print ' DRY CONDITIONS'
      #for i in range(len(data)):
      #   print '%5d %5d | bet %5d | resid: %5d | %6.2f  (ded: %6.2f)' % (min,max,data[i], resid[i], points[i], deduction[i])

      return points


































