"""
Sd_Tag
Abzüge von maximaler Punktzahl 8:
3 Punkte pro 10 Prozent
3 Punkte Zusatzabzug für Entscheidung 0/1 %

Sd_1h_12Z (Sonnenscheindauer von 11Z bis 12Z)
Abzüge von maximaler Punktzahl 8:
1 Punkt pro 10 Minuten
3 Punkte Zusatzabzug für Entscheidung 0/1 Minuten
3 Punkte Zusatzabzug für Entscheidung 59/60 Minuten

dd
Abzüge von maximaler Punktzahl 7:
1 Punkt pro 10 Richtungsgrad
0,5 Punkte / 10° bei ff einer Station < 3 m/s
0,5 Punkte / 10° für Abweichung von 60° bis 180°
0,3 Punkte / 10° für Abweichung von 60° bis 180° und ff einer Station < 3 m/s
Windstille ja/nein 6 Punkte Abzug

ff
Abzüge von maximaler Punktzahl 7:
3 Punkte pro m/s

fx (Windspitze von 0 bis 24Z)
Abzüge von maximaler Punktzahl 7:
3 Punkte pro m/s
fx auch unter 12,6 m/s relevant

PPP
Abzüge von maximaler Punktzahl 7:
3 Punkte pro hPa

T_Min (18Z Vortag bis 6Z)
Abzüge von maximaler Punktzahl 7:
3 Punkte pro °C

T_12Z (Temperatur um 12Z)
Abzüge von maximaler Punktzahl 7:
3 Punkte pro °C

T_Max (6Z bis 18Z)
Abzüge von maximaler Punktzahl 7:
3 Punkte pro °C

Td
Abzüge von maximaler Punktzahl 7:
3 Punkte pro °C

RR_max_1h (höchste 1-stündige Niederschlagsmenge von 0Z bis 24Z)
Abzüge von maximaler Punktzahl 8:
1 Punkt pro l/m²
5 – 1 l/m² 2-facher Abzug
1 – 0 l/m² 4-facher Abzug

RR_Tag (Niederschlagsumme von 0Z bis 24Z)
Abzüge von maximaler Punktzahl 8:
1 Punkt pro l/m²
5 – 1 l/m² 2-facher Abzug
1 – 0 l/m² 4-facher Abzug
"""

# -------------------------------------------------------------------
# - NAME:        judgingclass.py
# - AUTHOR:      Reto Stauffer / Juri Hubrig
# - DATE:        2022-09-02
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
# - L@ST MODIFIED: 2018-01-22 12:04 on marvin
# -------------------------------------------------------------------

# - Need numpy everywhere
import numpy as np

class judging(object):
   """This is a judgingclass - a class used to compute the points
   a user gets on a specific weekend. Please note that it is possible
   that the rules change somewhen and that there is a second judgingclass.

   The class contains public attributes tdate_min and tdate_max as a
   safety-instrument. As soon as you would like to compute points
   for a specific tournament which falls outside this limits the script
   will stop in the operational mode not to re-compute old bets with
   a wrong judgingclass.

   Args:
      quiet (:obj:`bool`): Default False, can be set to True to procude
        some more output.
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

   ## Do not use this judgingclass before 2022 rule change (2022-09-02)!
   tdate_min = 19802
   ## If set - do not use this judgingclass in the operational mode
   #  for tournaments > this date (days sicne 1970-01-01).
   tdate_max = None

   def __init__(self,quiet=False):
      """Initialize new juding object.

      Args:
         quiet (:obj:`bool`): Default is False. Redudes the output
            to a minimum if set to True. Used for some applications.
      """

      if not quiet:
         print('    Initializing judging class 2002-12-06 py')
      self.quiet = quiet

   # ----------------------------------------------------------------
   # - Prepares data to insert them into the database.
   #   Creates list tuple out of two lists.
   # ----------------------------------------------------------------
   def _prepare_for_database_(self,userID,cityID,paramID,tdate,betdate,values):
      """Prepares ID/value pairs for database.
      Creates a tuple list which can be used with
      database.database.executemany. Used later with
      the method 'points_to_database' within this class to update
      the bets table.

      Args:
        userID (:obj:`list`):  List containing :obj:`int`, numeric user ID.
        cityID (:obj:`list`):  List containing :obj:`int`, numeric city ID.
        paramID (:obj:`list`): List containing :obj:`int`, numeric parameter ID.
        tdate (:obj:`list`):   List containing :obj:`int`, numeric tournament date, days since 1970-01-01.
        betdate (:obj:`list`): List containing :obj:`int`, numeric betdate, days since 1970-01-01.
        values (:obj:`list`):  List containing the values (points).

      Returns:
        list of tuples: Re-structures the inputs to a list. The list has the
        same length as the input lists but each list element is a tuple containing
        the inputs. This object is then used for the executemany statement (write
        data to database).
      """

      if not len(userID) == len(values):
         utils.exit('In judging.prepare_for_database got different lengths of userIDs and values!')

      # - Create result
      return [ (values[i], userID[i], cityID[i], paramID[i], tdate[i], betdate[i]) for i in range(len(values)) ]

   
   # ----------------------------------------------------------------
   # - Inserts data into database. They have to be prepared
   # ----------------------------------------------------------------
   def points_to_database(self,db,userID,cityID,paramID,tdate,betdate,values):
      """Updates the bets database. All inputs are lists and have to be of the
      same length. (userID, cityID, paramID, tdate, betdate) define the unique
      ID in the wetterturnier_bets database. Argument values is a list as well
      containing the compute points.

      Args:
        userID (:obj:`list`):  List containing :obj:`int`, numeric user ID.
        cityID (:obj:`list`):  List containing :obj:`int`, numeric city ID.
        paramID (:obj:`list`): List containing :obj:`int`, numeric parameter ID.
        tdate (:obj:`list`):   List containing :obj:`int`, numeric tournament date, days since 1970-01-01.
        betdate (:obj:`list`): List containing :obj:`int`, numeric betdate, days since 1970-01-01.
        values (:obj:`list`):  List containing the values (points).
      """

      # - Prepare tuple list object
      data = self._prepare_for_database_(userID,cityID,paramID,tdate,betdate,values)

      sql = 'INSERT INTO '+db.prefix+'wetterturnier_bets SET points=%s, ' + \
            'userID=%s, cityID=%s, paramID=%s, tdate=%s, betdate=%s ' + \
            'ON DUPLICATE KEY UPDATE points=VALUES(points)'

      cur = db.cursor()
      cur.executemany( sql, data )
      

   # ----------------------------------------------------------------
   # - Handling all different point computation methods.
   #   Stops if there is an undefined class.
   # ----------------------------------------------------------------
   def get_points(self,obs,what,data,special=None,tdate=None):
      """Compute the points. This is a generic function which is used 
      to compute the points for all required parameters. The inputs
      define what has to be computed.

      Args:
        obs (:obj:`...`): Observations
        what (:obj:`str`): Which parameter, this defines the method to be called (internally).
        special (:obj:`float`): Some rules have 'special' sub-rules. This
            speical is a float observation required to compute the points.
        tdate (obj:`int`): tournament date, days since 1970-01-01 or None.
            Used to test whether or not it is allowed to compute the
            points for this specific tournament date with this judginclass.
            Second level securety check not to use the wrong judgingclass
            for a specific date.

      Returns:
        np.ndarray with floats: Returns a np.ndarray with the points rounded
        to one digit.
      """

      from . import utils
      import numpy as np

      # - If obs is none at all: return None
      if obs is None: return(None)
      # - Filter non-None obs
      tmp = []
      for i in obs:
         if not i is None: tmp.append( i )
      
      if len(tmp) == 0:
         return [0.] * len(data)
      obs = tmp

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
         print('    - Using method: %s' % method_to_use)
      call = getattr(self,method_to_use)
      # Round to one digit after the comma
      return np.round( call(obs,data,special), 1 )


   # -----------------------------------------------------------------
   # - Compute residuals
   # -----------------------------------------------------------------
   def __residuals__(self,obs,data):
      """Helper function to compute the residuals.
      If input 'data' lies in between minimum and maximum of 'obs' this
      was a perfect hit (and 0.0 will be returned). Else the minimal
      absolute difference to the closest 'obs' will be returned.

      Args:
        obs (): Observations.
        data (): Forecasted values.

      Returns:
        np.ndarray of type float: np.ndarray containing the residuals.
      """

      # - Observations MIN/MAX. If it is only one value MIN is equal to MAX.
      obs  = np.asarray(obs)
      MIN  = np.min(obs)
      MAX  = np.max(obs)

      # - Compute residuals
      resid = np.ndarray(len(data),dtype='float'); resid[:] = -999.
      resid[ np.where(np.logical_and(data >= MIN, data <= MAX)) ] = 0.
      resid[ np.where(data < MIN) ] = np.abs(MIN - data[ np.where(data < MIN) ])
      resid[ np.where(data > MAX) ] = np.abs(MAX - data[ np.where(data > MAX) ])

      return resid

   # ----------------------------------------------------------------
   # - Compute TTm (maximum temperature) points
   #   Compute TTn (minimum temperature) points
   #   Compute TTd (dewpoint temperature) points
   #   - They are using the same method (forwarding)
   # ----------------------------------------------------------------
   def __points_TT12__(self,obs,data,special):
      return self.__points__TTmTTnTTd__(obs,data,special,0.5)
   def __points_TTm__(self,obs,data,special):
      """Function to compute points for TTm (maximum temperature).
      This is only an alias to __points_TTmTTnTTd__ as they all use
      the same rule.
      """
      return self.__points_TTmTTnTTd__(obs,data,special,0.3)
   def __points_TTn__(self,obs,data,special):
      """Function to compute points for TTn (minimum temperature)
      This is only an alias to __points_TTmTTnTTd__ as they all use
      the same rule.
      """
      return self.__points_TTmTTnTTd__(obs,data,special,0.3)
   def __points_TTd__(self,obs,data,special):
      """Function to compute points for TTd (dew-point temperature)
      This is only an alias to __points_TTmTTnTTd__ as they all use
      the same rule.
      """
      return self.__points_TTmTTnTTd__(obs,data,special,0.2)
   # - Here TTm and TTn are getting computed
   def __points_TTmTTnTTd__(self,obs,data,special,factor):
      """Rule function to compute points for minimum/maximum temperature
      and dew-point temperature.

      Args:
        obs (): Observations.
        data (): Forecasted values.
        special (): Special observations for additional rules.
            These are not used to compute the points in this function.
        factor (): Factor for the loss of points for non-perfect forecasts.
            As this factor differs for TTm/TTn and TTd it is specified
            via input argument.
      
      Returns:
         Returns the corresponding points.
      """

      if not self.quiet:
         print('    - Called TTm/TTn/TTd point computation method')
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
   # - Compute Sd (sunshine duration) points 
   # ----------------------------------------------------------------
   def __points_Sd__(self,obs,data,special):
      """Rule function to compute points for relative sunshine duration.

      Args:
        obs (): Observations.
        data (): Forecasted values.
        special (): Special observations for additional rules.
      
      Returns:
         Returns the corresponding points.
      """

      if not self.quiet:
         print('    - Called Sd point computation method')
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
      obs    = np.asarray(obs); MIN = np.min(obs); MAX = np.max(obs)
      # - Additinoal 1.5 points less between observed 0% and bet 1% or
      #   higher the other way around.
      # - minus 1.5 points. Why + 0.1? I allready subtracted
      #   0.1 points because 0/10 makes 10 difference units times
      #   0.01 above makes 0.1 points deduction. Therefore I
      #   have to subtract only 1.5 additional points here.
      idx = np.where( np.logical_and(MAX == 0., data > 0.) )
      points[idx] = points[idx] - 1.5 + 0.1
      # - The same the other way around
      idx = np.where( np.logical_and(MIN > 0., data == 0.) )
      points[idx] = points[idx] - 1.5 + 0.1

      # - Cannot be negative
      points = np.maximum( points, 0)

      # - Show data (development stuff)
      #for i in range(len(data)):
      #   print '%3d|%3d:  %3d %3d %6.2f' % (MIN/10., MAX/10., data[i]/10., resid[i]/10., points[i])
      return points


   # ----------------------------------------------------------------
   # - Compute dd (wind direction) 
   # ----------------------------------------------------------------
   def __points_dd__(self,obs,data,special):
      """
      TODO: crashes if only one dd observed and no wind speed => try/catch fallback
      Rule function to compute points for wind direction parameter.

      Args:
        obs (): Observations.
        data (): Forecasted values.
        special (): Special observations for additional rules.
      
      Returns:
         Returns the corresponding points.
      """

      if not self.quiet:
         print('    - Called dd point computation method')
      data   = np.asarray(data)
      obs    = np.asarray(obs);
      try:
         MIN = np.min(obs[np.where( np.logical_and(obs > 0., obs <= 3600. ))])
      except:
         MIN = None
      try:
         MAX = np.max(obs[np.where( np.logical_and(obs > 0., obs <= 3600. ))])
      except:
         MAX = None
      # - Change minimum if angle (difference) is bigger than 180 degrees.
      if not MAX == None and not MIN == None:
         if MAX - MIN > 1800.:
            tmp = MAX
            MAX = MIN + 3600.
            MIN = tmp 
      # - If min or MAX is none, MIN and MAX are equal
      if not MIN == None and MAX == None: MAX = MIN
      if MIN == None and not MAX == None: MIN = MAX

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

      #if at least one wind direction is zero, it's calm
      if len( np.where(obs ==    0.)[0] ) > 0:
         calm     = True
      #if at least one direction is variable...
      if len( np.where(obs == 9900.)[0] ) > 0:
         variable = True
      if len( np.where( np.logical_and(obs > 0., obs <= 3600.) )[0] ) > 0:
         normal = True

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
               the_obs = np.asarray([MIN, MAX]) 
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

      return points


   # ----------------------------------------------------------------
   # - Compute ff (mean wind speed) points 
   # ----------------------------------------------------------------
   def __points_ff__(self,obs,data,special):
      """Rule function to compute points for wind speed.

      Args:
        obs (): Observations.
        data (): Forecasted values.
        special (): Special observations for additional rules.
      
      Returns:
         Returns the corresponding points.
      """

      if not self.quiet:
         print('    - Called ff point computation method')
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
   # - Compute PPP (station pressure) points 
   # ----------------------------------------------------------------
   def __points_PPP__(self,obs,data,special):
      """Rule function to compute points for reduced surface air pressure.

      Args:
        obs (): Observations.
        data (): Forecasted values.
        special (): Special observations for additional rules.
      
      Returns:
         Returns the corresponding points.
      """

      if not self.quiet:
         print('    - Called PPP point computation method')
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
