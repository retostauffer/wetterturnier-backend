# -------------------------------------------------------------------
# - NAME:        TestPoints.py 
# - AUTHOR:      Reto Stauffer
# - DATE:        2014-09-21
# - LICENSE: GPL-3, Reto Stauffer, copyright 2014
# -------------------------------------------------------------------
# - DESCRIPTION: Compute points for all players. 
#                Using a preset judging class (see config).
#                If the juding class is not callable: EXIT
#
#                This is mainly to test what the points should/would
#                be in the live tournament as the ComputePoints 
#                routine uses the same judging class.
#
#                Requires the pywetterturnier package.
# -------------------------------------------------------------------
# - EDITORIAL:   2014-09-19, RS: Created file on thinkreto.
#                Adapted from ComputePetrus.py
#                2015-08-03, RS: Much nicer usage, nicer output.
# -------------------------------------------------------------------
# - L@ST MODIFIED: 2015-08-04 09:32 on prognose2.met.fu-berlin.de
# -------------------------------------------------------------------



# - Start as main script (not as module)
if __name__ == '__main__':
   """
   Main routine. There is nothing else, has to be started as the
   main routine. Computes expected points given observations and
   forecasted values.
   """

   import sys, os
   import numpy as np
   from pywetterturnier import utils
   from optparse import OptionParser

   os.environ['PYTHON_EGG_CACHE'] = '/var/www/egg-cache'

   # ----------------------------------------------------------------
   # - Reading input arguments, define usage.
   # ----------------------------------------------------------------
   usage =  """
   help:  %prog -h/--help 
   usage: %prog -o <OBS> -v <VALUES> [options]

   examples:
   1) Two observed values, one forecasted value
     - %prog -p TTn -o 14.3,16.1 -v 12.1

   2) Two observed values, several forecast values
     - %prog -p TTm -o 14.3,16.1 -v 12.1,13.1,14.1,15.1

   3) Wind direction. If wind speed on at least one
      station (-o/--obs) is below 6 knots: only half 
      points will be subtracted.
    - %prog -p dd -o 100,120 -v 160              # -s not given: ff assumd to be 0
    - %prog -p dd -o 100,120 -v 160 -s 3,10,10   # -s given, minimum ff 3.0, less penalty
    - %prog -p dd -0 100,120 -v 160 -s 11,15.5   # -s given, minimum > 6kt: double penalty
   """
   parser = OptionParser(usage=usage.replace("%prog",__file__))

   # - Which parameter, required, string
   parser.add_option("-p","--param",action="store",dest="param",type="string",default=None,
                 help="Required, parameter to judge. String.") 
   # - Observations, required.
   parser.add_option("-o","--obs",action="store",dest="obs",type="string",default=None,
                 help="Required, observations. Numeric values. Either one single value " + \
                      "or a list of observations separated by commas. No blanks!")
   # - Values, required (forecast values)
   parser.add_option("-v","--values",action="store",dest="values",type="string",default=None,
                 help="Required, forecasted values/bets. Numeric values. Either one single value " + \
                      "or a list of values separated by commas. No blanks!")
   # - Special, additional values 
   parser.add_option("-s","--special",action="store",dest="special",type="string",default=None,
                 help="Optional, additional observations which are necessary for certain " + \
                      "parameters (e.g., judging for wind direction also depends on " + \
                      "observed wind speed (in this case -s/--special has to be " + \
                      "observed wind speed, single value, or comma separated list.")
   # - Quiet mode
   parser.add_option("-q","--quiet",action="store_true",dest="quiet",default=False,
                     help="Optional, logical. If set, output will be more quiet. Default False.")

   inputs, args = parser.parse_args()
   # - Missing input -o
   if not inputs.param:  print(parser.usage);    utils.exit( "Missing required input -p/--param.")
   if not inputs.obs:    print(parser.usage);    utils.exit( "Missing required input -o/--obs.")
   if not inputs.values: print(parser.usage);    utils.exit( "Missing required input -v/--values.")
   # ----------------------------------------------------------------


   # ----------------------------------------------------------------
   # - Reading config file
   # ----------------------------------------------------------------
   config = utils.readconfig('config.conf')


   # ----------------------------------------------------------------
   # - Checking if parameter is allowed
   # ----------------------------------------------------------------
   from pywetterturnier import database
   if not inputs.quiet: print("  * Checking if parameter %s is allowed" % inputs.param)
   db = database.database(config)
   paramID = db.get_parameter_id( inputs.param )
   db.close(False)
   if not paramID: utils.exit("[!] Parameter %s unknown! Stop." % inputs.param)
   

   # ----------------------------------------------------------------
   # - Helper function: comma separated inuts to numpy arrays
   # ----------------------------------------------------------------
   def input_to_list( x, msg ):
      """
      Inputs to this script can be lists of numeric values.
      Therefore we have to convert them into numpy arrays which
      will be done by this script. If input is NONE, an empty
      array will be returned.
      Inputs:     x   required   string (e.g., '13.3' or '13.3,14.4')
                  msg required   short message in case the function calls exit.
      Output:     numpy.array object containing either nothing (empty) or
                  the values from input x as float numbers.
      """
      if not x: return np.asarray([])
      tmp = x.split(",")
      res = []
      for elem in tmp:
         try:
            res.append( float(elem) )
         except:
            utils.exit("Problems: %s have to be numeric!" % msg)
      return np.asarray(res)


   # ----------------------------------------------------------------
   # - Convert inputs to numpy.arrays first
   # ----------------------------------------------------------------
   inputs.values  = input_to_list( inputs.values  , "forecast values")
   inputs.obs     = input_to_list( inputs.obs     , "observations")
   inputs.special = input_to_list( inputs.special , "special observations")


   # ----------------------------------------------------------------
   # - Import judgingclass as defined by config.conf file. Note:
   #   dynamic load. If not loadable, exit.
   # ----------------------------------------------------------------
   modname = "pywetterturnier.judgingclass%s" % config['judging_test']
   if not inputs.quiet: print("  * Try to load test-judgingclass from module %s" % modname)
   try:
      from importlib import import_module 
      judging = import_module(modname)
   except Exception as e:
      print(e)
      utils.exit("Problems loading the judgingclass %s" % modname)

   # - Initialize judging
   jug = judging.judging(inputs.quiet)
   # - Compute points
   par = inputs.param
   
   if par == "RR":
      val=[]; obs=[]; spe=[]
      for i in range(len(inputs.values)):
         val.append(int(inputs.values[i]*10))
      for i in range(len(inputs.obs)):
         obs.append(int(inputs.obs[i]*10))
      for i in range(len(inputs.special)):
         spe.append(int(inputs.special[i]*10))

   else:
      val = inputs.values*10.
      obs = inputs.obs*10.
      spe = inputs.special*10.

   points = jug.get_points(obs, par, val, spe)


   # ----------------------------------------------------------------
   # - Show output
   # ----------------------------------------------------------------
   if not inputs.quiet:
      print('\n  * Observations were:  ', end=' ')
      for o in inputs.obs: print('%8.3f ' % (o), end=' ')
      print('')
      for i in range(len(inputs.values)):
         print('    - Forecast %8.3f leads to %5.2f points' % (inputs.values[i],points[i])) 
   else:
      print('points')
      for i in range(len(inputs.values)):
         print('%5.2f' % (points[i])) 



