# -------------------------------------------------------------------
# - NAME:        utils.py
# - AUTHOR:      Reto Stauffer
# - DATE:        2014-09-13
# -------------------------------------------------------------------
# - DESCRIPTION: Some helper functions.
# -------------------------------------------------------------------
# - EDITORIAL:   2014-09-13, RS: Created file on thinkreto.
#                2014-12-31, RS: Inputs str('None') will be
#                converted to None.
#                2015-08-05, RS: Moved inputcheck into utils.
# -------------------------------------------------------------------
# - L@ST MODIFIED: 2017-06-23 20:01 on thinkreto
# -------------------------------------------------------------------

"""@package docstring
Documentation for this module.

More details.
"""

# -------------------------------------------------------------------
# - Parsing input arguments
# -------------------------------------------------------------------
def inputcheck(what):
   """!Checking input arguments for several scripts.
   Using the same inputcheck routine for most of the Wetterturnier
   python backend scripts. The arguments are evaluated in here
   and added to a list object which will be returned. Please
   have a look into the usage (most scripts can be called with
   input argument -h/--help to display the usage).

   @bug Input argument what is not in use. Maybe kill it or
   at least set some defaults.

   @args what. String, to handle some specal cases. At the moment
   the input argument is not used at all!
   """

   import sys, getopt

   # - Evaluating input arguments from the __main__ script.
   try:
      opts, args = getopt.getopt(sys.argv[1:], "c:u:t:p:ahi", ["city=", "user=", "tdate=","param=","alldates","help","ignore"])
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
   """!Script usage

   @bug change iputcheck, add propper usage.
   """

   import utils

   if what == None:
      print """
      Run into the usage from the inputcheck module with None type.
      You should set an explcit 'what' type when calling the usage
      so that I can give you a propper exit statement and some
      explanation which input options are allowed.
      """
   else: 
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
   #else:
   #   print """
   #   Run into the usage from the inputcheck module with an unknown
   #   type. 
   #   """

   utils.exit('This is/was the usage (what: %s).' % what)


# -------------------------------------------------------------------
# - Reading configuration file
# -------------------------------------------------------------------
def readconfig(file='config.conf',inputs=None):
   """!Reading config file. There is a 'global' wetterturnier backend
   config file which is necessary to handle all the actions.
   This method also checks some parameters. E.g., if a required directory or
   file does not exist, the script stops.

   @args file. String, file name of the config file. Default is config.conf.
   @args inputs, dict. Usually the input dict from @ref utils.inputcheck.
   Default is None. If it is adict: all parameters will be added to 
   the config dict which will be generated in this method.
   In case a key exists in the config dict (created in here) and is duplicated
   in the inputs dict the script will stop immediately.
   @return dict containing all necessary configs.
   """

   import sys, os
   import utils

   if not os.path.isfile(file):
      utils.exit('Cannot read file %s. Not readable or not existing' % file)

   # - Import ConfigParser
   from ConfigParser import ConfigParser
   CNF = ConfigParser()
   CNF.read(file)

   # - Checks if directory exists.
   def check_directory( name ):
      if not os.path.isdir( name ):
         utils.exit('Directory %s does not exist as requried by config file.' % name)
   # - Checks if file exists.
   def check_file( name ):
      if not os.path.isfile( name ):
         utils.exit('File %s does not exist as requried by config file.' % name)

   # ----------------------------------------------------------------
   # - Reading mysql config
   config = {} 
   try:
      config['mysql_host']       = CNF.get('database','mysql_host')
      config['mysql_user']       = CNF.get('database','mysql_user')
      config['mysql_pass']       = CNF.get('database','mysql_pass')
      config['mysql_db']         = CNF.get('database','mysql_db')
      config['mysql_prefix']     = CNF.get('database','mysql_prefix')

      config['mysql_obstable']   = CNF.get('database','mysql_obstable')
   except:
      utils.exit('Problems reading the database config from the config file %s' % file)

   # ----------------------------------------------------------------
   # - Reading migration flags
   try:
      config['migrate_groups']         = CNF.getboolean('migrate','groups')
      config['migrate_mitspieler']     = CNF.getboolean('migrate','mitspieler')
      config['migrate_mitspielerfile'] = CNF.get('migrate','mitspielerfile')
      config['migrate_wpconfig']       = CNF.get('migrate','wpconfig')
      tmp = CNF.get('migrate','citytags')
      config['migrate_citytags'] = []
      for elem in tmp.split(','): config['migrate_citytags'].append(elem.strip())
   except:
      config['migrate_mitspieler'] = False
      config['migrate_groups']     = False
      config['migrate_citytags']   = None

   # ----------------------------------------------------------------
   # - Loading operational and test judgingclass
   try:
      config['judging_operational'] = CNF.get('judging','operational')
      config['judging_test']        = CNF.get('judging','test')
   except:
      utils.exit('Problems reading necessary judging config!') 

   # ----------------------------------------------------------------
   # - Some configs where the data are.
   #   data_moses:     where Klaus Knuepffer stores the moses equations 
   try:
      config['data_moses']       = CNF.get('data','moses')
   except:
      utils.exit('Problems rading all required data infos from config file')
   if not os.path.isdir( config['data_moses'] ):
      print "[WARNING] Could not find directory %s necessary for ComputeMoses" % config['data_moses'] 
      print "          ComputeMoes will crash!"

   # ----------------------------------------------------------------
   # - The rawdir is used by archive.py to import old 
   #   wetterturnier data. Should never be used in the final version.
   try:
      config['rawdir']           = CNF.get('system','rawdir')
   except:
      utils.exit('Problems rading all required system infos from config file')

   # ----------------------------------------------------------------
   # - Reading all stations
   tmp = CNF.items('stations')
   stn = {}
   for elem in tmp:
      stn[elem[0]] = int(elem[1])
   config['stations']         = stn

   # ----------------------------------------------------------------
   # - Adding inputs if set
   if not inputs == None:
      for k in inputs.keys():
         # - Duplicated?
         if k in config.keys():
            utils.exit("inputs dict contains keys which are generated in this " + \
                     "method as well. Duplication! Exit. Key is: %s" % k)
         # - Else append
         if inputs[k] == 'None':
            config[k] = None 
         else:
            config[k] = inputs[k]

   return config


# -------------------------------------------------------------------
# - Convert date since 1970-01-01 into a readable string 
# -------------------------------------------------------------------
def tdate2string( date ):
   """! Converts tdate into string of form YYY-MM-DD.
   Note: a so called tdate is nothing else than an integer value
   indicating the days since 1970-01-01 which is used extensively
   in the wetterturnier (especially to optimize the databases).

   @args date. Integer, days since 1970-01-01
   @return string of format %Y-%m-%d
   """

   from datetime import datetime as dt

   return dt.fromtimestamp( date*86400 ).strftime('%Y-%m-%d')


# -------------------------------------------------------------------
# - Manipulate special characters to get propper names 
# -------------------------------------------------------------------
def nicename( string ):
   """!Creates a nice username.
   Mainly used for migration where (from the text files of the old
   wetterturnier archive) a few usernames were including special characters,
   blanks, or other special things. The new Wetterturnier only allows
   propper non-special-character usernames. This function converts
   possibly impropper usernames to its propper equivalent.

   @args string. Possibly impropper user name.
   @return string with nice username without special characters and shit.
   """

   import unicodedata
   import re
   import utils
   string = re.escape(string).strip()


   nicename = unicodedata.normalize('NFKD', unicode(string,'ISO-8859-1')) \
                  .encode('ascii', 'ignore')
   nicename = nicename.replace('/','_')
   nicename = nicename.replace('\_','_')
   nicename = nicename.replace('\\A','Ae')
   nicename = nicename.replace('\\O','Oe')
   nicename = nicename.replace('\\U','Ue')
   nicename = nicename.replace('\\a','ae')
   nicename = nicename.replace('\\o','oe')
   nicename = nicename.replace('\\u','ue')
   nicename = nicename.replace('\\','')
   nicename = nicename.replace('\)','')
   nicename = nicename.replace('\(','')
   nicename = nicename.replace(')','')
   nicename = nicename.replace('(','')
   nicename = nicename.replace('\+','')
   nicename = nicename.replace('+','')
   nicename = nicename.replace('\-','-')
   nicename = nicename.replace('\.','')
   nicename = nicename.replace('\/','')
   nicename = nicename.replace(' ','_')
   nicename = nicename.replace('\e','e')
   # - This is only for the Grossmeister
   nicename = nicename.replace('\m','ss')
   if "\\" in nicename:
       utils.exit('nicename is with special ' + nicename)

   return nicename


# -------------------------------------------------------------------
# - Customized exit handling
# -------------------------------------------------------------------
def exit(msg):
   """!Simple exit wrapper.
   Can be used to create kind of user-defined exit handling.
   """

   import sys
   sys.exit('[!] ERROR: %s' % msg)



