# -------------------------------------------------------------------
# - NAME:        inputcheck.py
# - AUTHOR:      Reto Stauffer
# - DATE:        2014-09-28
# -------------------------------------------------------------------
# - DESCRIPTION: Checking input arguments I got from the
#                getopt parser. There are different
#                input options for different scripts, this
#                input checker can handle them.
# -------------------------------------------------------------------
# - EDITORIAL:   2014-09-28, RS: Created file on thinkreto.
#                2015-01-05, RS: Doing getopt evaluation in here.
# -------------------------------------------------------------------
# - L@ST MODIFIED: 2015-07-23 13:41 on prognose2.met.fu-berlin.de
# -------------------------------------------------------------------

# -------------------------------------------------------------------
# - Parsing input arguments
# -------------------------------------------------------------------
def inputcheck(what):

   import sys, getopt

   # - Evaluating input arguments from the __main__ script.
   try:
      opts, args = getopt.getopt(sys.argv[1:], "c:u:t:p:ahi", ["city=", "user=", "tdate=","param=","alldates","help","ignore"])
      print opts, args
   except getopt.GetoptError as err:
      print str(err) # will print something like "option -a not recognized"
      usage(what)


   inputs = {} # result
   inputs['input_city']      = None
   inputs['input_user']      = None
   inputs['input_tdate']     = None
   inputs['input_alldates']  = False 
   inputs['input_param']     = None 
   inputs['input_ignore']    = False
   inputs['input_force']     = False

   # - Overwrite the defaults if inputs are set
   for o, a in opts:
      if o in ("-h","--help"):
         usage(what)
      elif o in ("-a","--alldates"):
         inputs['input_alldates']  = True
      elif o in ("-c", "--city"):
         if not a in ['Berlin','Zuerich','Wien','Innsbruck','Leipzig']:
            print 'Your input on -c/--city not recognized.'
            usage(what)
         inputs['input_city'] = str(a)
      elif o in ("-u", "--user"):
         # - Check if is integer (uderID) or string
         try:
            user = int(a)
         except:
            user = str(a) 
         inputs['input_user'] = user 
      elif o in ("-f", "--force"):
         inputs['input_force'] = True
      elif o in ("-i", "--ignore"):
         inputs['input_ignore'] = True
      elif o in ("-p", "--param"):
         inputs['input_param'] = a
      elif o in ("-t", "--tdate"):
         try:
            inputs['input_tdate'] = int( a )
         except:
            print '-t/--tdate input has to be an integer!'; usage(what)
      else:
         assert False, "unhandled option"

   # - If alldates is True and additionally
   #   a tdate is set: stop.
   if inputs['input_alldates'] and not inputs['input_tdate'] == None:
      import utils
      utils.exit('Input -a/--alldates and -t/--tdate cannot be combined!')


   return inputs


# -------------------------------------------------------------------
# - Show the usage and exit.
# -------------------------------------------------------------------
def usage(what=None):

   import utils

   if what == 'ComputePoints':
      print """
      Sorry, wrong usage for type ComputePoints.
      Allowed inputs for this script are:
      
      -u/--user:     A userID or a user_login name. Most 
                     script accept this and compute the points
                     or whatever it is for this user only.
      -c/--city:     City hash to be one of these strings:
                     Berlin, Wien, Zuerich, Innsbruck, Leipzig. 
      -a/--alldates  Cannot be combined with the -t/--tdate option.
                     If set loop over all available dates. 
      -t/--tdate:    Tournament date in days since 1970-01-01
      -a/--alldates: ignores -t input. Takes all tournament dates
                     from the database to compute the points.
      -f/--force:    Please DO NOT USE. This was for testing
                     purpuses to bypass some securety features
                     of the scripts!!!! But these securety
                     features are there for some reason. So
                     please do not use.
      """
   elif what == None:
      print """
      Run into the usage from the inputcheck module with None type.
      You should set an explcit 'what' type when calling the usage
      so that I can give you a propper exit statement and some
      explanation which input options are allowed.
      """
   else:
      print """
      Run into the usage from the inputcheck module with an unknown
      type. 
      """

   utils.exit('This is/was the usage (what: %s).' % what)

