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
# - L@ST MODIFIED: 2018-01-24 12:12 on marvin
# -------------------------------------------------------------------
"""
Documentation for this module.
More details should be added.
"""

import numpy as np

# -------------------------------------------------------------------
# - Prevent the script to execute some of the routines on certain
#   tournament days. 
# -------------------------------------------------------------------
def datelock(config,tdate):
   """To prevent the scripts to re-compute certain things, e.g.
   the mean bet tips in the archive, this small function is used.
   Problem: we do not know who was in which group in the past, wherefore
   the mean bets will get wrong if recomputed.

   Args:
      config (:obj:`dict`): The config list from :meth:`utils.readconfig`.
      tdate (:obj:`int`): Date as integer, days sincd 1970-01-01.

   Return:
      bool: Returns True if you are allowed to execute the
      comoputation and false otherwise."""

   return eval("{0:d} {1:s}".format(tdate,config['datelock']))

# -------------------------------------------------------------------
# - Parsing input arguments
# -------------------------------------------------------------------
def inputcheck(what):
   """Checking input arguments for several scripts.
   Using the same inputcheck routine for most of the Wetterturnier
   python backend scripts. The arguments are evaluated in here
   and added to a list object which will be returned. Please
   have a look into the usage (most scripts can be called with
   input argument ``-h/--help`` to display the usage).

   .. todo:: A bug! Input argument what is not in use. Maybe kill it or
      at least set some defaults.

   Args:
      what (:obj:`str`): String to handle some specal cases. At the moment
      the input argument is not used at all!
   """
   from pywetterturnier import database
   import sys, getopt
   config = readconfig('config.conf')                  
   db        = database.database(config)
   # - Evaluating input arguments from the __main__ script.
   try:
      opts, args = getopt.getopt(sys.argv[1:], "c:u:s:t:p:d:n:ahiv", ["city=", "user=", "users=", "tdate=","param=","dates=","filename=","alldates","help","ignore","verbose"])
   except getopt.GetoptError as err:
      print(str(err)) # will print something like "option -a not recognized"
      usage(what)


   inputs = {} # result
   inputs['input_city']      = None
   inputs['input_user']      = None
   inputs['input_users']     = None
   inputs['input_tdate']     = None
   inputs['input_alldates']  = False 
   inputs['input_param']     = None 
   inputs['input_dates']     = None
   inputs['input_filename']  = None
   inputs['input_ignore']    = False
   inputs['input_force']     = False
   inputs['input_verbose']   = False

   # - Overwrite the defaults if inputs are set
   for o, a in opts:
      if o in ("-h","--help"):
         usage(what)
      elif o in ("-a","--alldates"):
         inputs['input_alldates']  = True
      elif o in ("-c", "--city"):
         if len(a) <= 2: a = int(a)
         cities = db.get_cities()
         #print "  * %s active cities" % len(cities)
         found  = False
         for i in list(range(len(cities))):
            #print cities[i].values()
            if a in list(cities[i].values()):
               inputs['input_city'] = cities[i]['name']
               found = True
            else:
               continue
         if not found:
            print('Your input on -c/--city was not recognized.')
            usage(what)
      elif o in ("-u", "--user"):
         # - Check if is integer (userID) or string
         try:
            user = int(a)
         except:
            user = str(a) 
         inputs['input_user'] = user
      elif o in ("-s", "--users"):
         try:
            inputs['input_users'] = a.split(",")
         except:
            print("Could not convert input to list"); usage(what)
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
            try:
               inputs['input_tdate'] = string2tdate( str(a) )
            except:
               print('-t/--tdate input has to be an integer or a datestring (YYYY-MM-DD)!'); usage(what)
      elif o in ("-d", "--dates"):
         try:
            dates = a.split(",")
            inputs["input_dates"] = (string2tdate( dates[0] ), string2tdate( dates[1] ))
         except:
            #TODO: make it possible to enter single dates rather than a range (maybe date1;date2)
            print('-d/--dates input has to be a list of 2 dates (YYYY-MM-DD,YYYY-MM-DD)!'); usage(what)
      elif o in ("-n", "--filename"):
         inputs['input_filename'] = str(a)
      elif o in ("-v", "--verbose"):
         inputs['input_verbose'] = True
      else:
         assert False, "unhandled option"

   # - If alldates is True and additionally
   #   a tdate is set: stop.
   if inputs['input_alldates'] and not inputs['input_tdate'] == None:
      exit('Input -a/--alldates and -t/--tdate cannot be combined!')


   return inputs


# -------------------------------------------------------------------
# - Show the usage and exit.
# -------------------------------------------------------------------
def usage(what=None):
   """Script usage.

   Args:
      what (:obj:`str`): String to specify which usage should be used.

   .. todo:: A bug! Change iputcheck, add propper usage.
   """

   import sys
   from pywetterturnier import getobs, database

   config = readconfig('config.conf')
   db     = database.database(config)                
   cities = db.get_cities()                             
   IDs, names, hashes = [],[],[]                        
   for i in list(range(len(cities))):                      
      IDs.append(cities[i]['ID'])                          
      names.append(cities[i]['name'])                      
      hashes.append(cities[i]['hash'])

   if what == None:
      print("""
      Run into the usage from the inputcheck module with None type.
      You should set an explcit 'what' type when calling the usage
      so that I can give you a propper exit statement and some
      explanation which input options are allowed.
      """)
   else:
      print("""
      Sorry, wrong usage for type %s.
      Allowed inputs for this script are:
      
      -u/--user:     A userID or a user_login name. Most 
                     script accept this and compute the points
                     or whatever it is for this user only.
      -s/--users:    A list of user names, seperated by commas, no spaces!
      -c/--city:     City can be given by its ID, name or hash
                     IDs:     %s
                     names:   %s
                     hashes:  %s
      -a/--alldates  Cannot be combined with the -t/--tdate option.
                     If set loop over all available dates. 
      -t/--tdate:    Tournament date in days since 1970-01-01
      -p/--param:    A list of paramIDs.
      -n/--filename  A filename for exporting tables/data.
      -d/--dates:    A range of dates seperated by ","
      -a/--alldates: ignores -t input. Takes all tournament dates
                     from the database to compute the points.
      -f/--force:    Please DO NOT USE. This was for testing
                     purpuses to bypass some securety features
                     of the scripts!!!! But these securety
                     features are there for some reason. So
                     please do not use.
      """ % (what, IDs, names, hashes))

   exit('This is/was the usage (what: %s).' % what)


# -------------------------------------------------------------------
# - Reading configuration file
# -------------------------------------------------------------------
def readconfig(file='config.conf',inputs=None,conversion_table=None):
   """Reading config file. There is a 'global' wetterturnier backend
   config file which is necessary to handle all the actions.
   This method also checks some parameters. E.g., if a required directory or
   file does not exist, the script stops.

   Args:
      file   (:obj:`str`):  string File name of the config file. Default is ``config.conf``.
      inputs (:obj:`dict`): Usually the input dict from :meth:`utils.inputcheck`.
                            Default is None. If it is a dict: all parameters will be added to 
                            the config dict which will be generated in this method.
                            In case a key exists in the config dict (created in here) and is duplicated
                            in the inputs dict the script will stop immediately.
   Returns:
      dict: A dict containing all necessary configs.
   """

   import sys, os

   if not os.path.isfile(file):
      exit('Cannot read file %s. Not readable or not existing' % file)

   # - Import ConfigParser
   from configparser import ConfigParser
   CNF = ConfigParser()
   CNF.read(file)

   # - Checks if directory exists.
   def check_directory( name ):
      if not os.path.isdir( name ):
         exit('Directory %s does not exist as requried by config file.' % name)
   # - Checks if file exists.
   def check_file( name ):
      if not os.path.isfile( name ):
         exit('File %s does not exist as requried by config file.' % name)

   # ----------------------------------------------------------------
   # - Reading mysql config
   config = {} 
   config['conversion_table'] = conversion_table
   try:
      config['mysql_host']       = CNF.get('database','mysql_host')
      config['mysql_user']       = CNF.get('database','mysql_user')
      config['mysql_pass']       = CNF.get('database','mysql_pass')
      config['mysql_db']         = CNF.get('database','mysql_db')
      config['mysql_prefix']     = CNF.get('database','mysql_prefix')
      config['mysql_port']       = int(CNF.get('database','mysql_port'))
      config['mysql_obstable']   = CNF.get('database','mysql_obstable')
   except:
      exit('Problems reading the database config from the config file %s' % file)

   # ----------------------------------------------------------------
   # - Reading migration flags
   try:
      config['migrate_groups']         = CNF.getboolean('migrate','groups')
      config['migrate_mitspieler']     = CNF.getboolean('migrate','mitspieler')
      config['migrate_mitspielerfile'] = CNF.get('migrate','mitspielerfile')
      config['migrate_wpconfig']       = CNF.get('migrate','wpconfig')
      tmp = CNF.get('migrate','citytags')
      config['migrate_citytags'] = []
      for i in tmp.split(','):
         config['migrate_citytags'].append( i.strip() )
   except:
      config['migrate_mitspieler'] = False
      config['migrate_groups']     = False
      config['migrate_citytags']   = None

   # ----------------------------------------------------------------
   # - datelock if set
   try:
      config['datelock']           = CNF.get('migrate','datelock')
   except:
      config['datelock']           = None

   # - Whether the system is allowed to create users or not
   try:
      config['allow_create_users'] = CNF.getboolean('migrate','allow_create_users')
   except:
      config['allow_create_users'] = False

   # ----------------------------------------------------------------
   # - Loading operational and test judgingclass
   try:
      config['judging_operational'] = CNF.get('judging','operational')
      config['judging_test']        = CNF.get('judging','test')
   except:
      exit('Problems reading necessary judging config!') 

   # ----------------------------------------------------------------
   # - Some configs where the data are.
   #   data_moses:     where Klaus Knuepffer stores the moses equations 
   try:
      config['data_moses']       = CNF.get('data','moses')
   except:
      exit('Problems rading all required data infos from config file')
   if not os.path.isdir( config['data_moses'] ):
      print("[WARNING] Could not find directory %s necessary for ComputeMoses" % config['data_moses']) 
      print("          ComputeMoes will crash!")
   try:
      config['data_moses_out']   = CNF.get('data','moses_out')
      # If folder does not exist: ignore
      if not os.path.isdir( config['data_moses_out'] ):
         print("[WARNING] Output directory for moses (moses_out=\"{0:s}\")".format(config['data_moses_out']))
         print("          does not exist, ignore!")
         config['data_moses_out'] = None
   except:
      exit('No [data] modes_out directory set, will not copy files to webserver.')
      config['data_moses_out']   = None

   # ----------------------------------------------------------------
   # - The rawdir is used by archive.py to import old 
   #   wetterturnier data. Should never be used in the final version.
   try:
      config['rawdir']           = CNF.get('system','rawdir')
   except:
      exit('Problems rading all required system infos from config file')

   # ----------------------------------------------------------------
   # - Reading all stations
   tmp = CNF.items('stations')
   stn = {}
   for i in tmp:
      stn[ i[0] ] = int( i[1] )
   config['stations']         = stn

   # ----------------------------------------------------------------
   # - Adding inputs if set
   if not inputs == None:
      for k in list(inputs.keys()):
         # - Duplicated?
         if k in list(config.keys()):
            exit("inputs dict contains keys which are generated in this " + \
                     "method as well. Duplication! Exit. Key is: %s" % k)
         # - Else append
         if inputs[k] == 'None':
            config[k] = None 
         else:
            config[k] = inputs[k]

   return config


# -------------------------------------------------------------------
# - Reading wmo ww conversion file.
# -------------------------------------------------------------------
class wmowwConversion( object ):
    """Helper class to convert observed weather types into the classes
    0/4/5/6/7/8/9 as used by Wetterturnier.de.
    Reads the wmo ww config file using :obj:`ConfigParser.ConfigParser`.
    The file contains the conversion rules from received observations to
    one of the main weather types (0,4,5,6,7,8,9). Can be used for present
    weather (ww) and past weather (w1/w2).

    Args:
        file (:obj:`str`): String, file name containing the specifications.
    """

    _past_weather_    = None
    _present_weather_ = None

    def __init__( self, file ):

        import sys, os
        if not os.path.isfile( file ):
            print("Sorry, cannot find file \"{0:s}\"".format(file))
            sys.exit(8)
        # Save file
        self.file = file

        # Use configparser to read the file
        from configparser import ConfigParser
        CNF = ConfigParser()
        try:
            CNF.read( file )
        except Exception as e:
            print(e)
            print("ERROR reading the file \"{0:s}\"".format(file))
            sys.exit(9)

        self._past_weather_    = self._read_section_(CNF,"past weather")
        self._present_weather_ = self._read_section_(CNF,"present weather")

    def _read_section_( self, CNF, section ):
        """Reading specific section of the config file and parses the settins.
        If the section does not exist: return None. Else a list is returned
        containing a dict for each valid setting entry in the config file.
        The dict keys are "integers as string", the weather type code as
        reported in the BUFR file. The dict for each key contains a "name"
        and a "gets" argument. "name" is simply the description of the setting,
        "gets" is either None (if defined to convert to None) or an integer
        (the new code flag in which the observed one should be converted).

        Args:
            CNf (:obj:`ConfigParser.ConfigParser`): The config file handler.
            section (:obj:`str`): String, which section to be read.
        Returns:
            list/None: None if section does not exist. Else a list with dicts.
        """

        if not CNF.has_section(section): return None

        import sys, re
        res = {}
        for i in CNF.items(section):
            name = i[0].strip()

            mtch = re.match("^([0-9]+)\s+gets\s+([0-9]+|None)$", i[1])
            if not mtch:
                print("    [!] Misspecified: \"{0:s}\". Ignore.".format(i))
                continue
            # Use integer key as string key
            if mtch.group(2) == "None":     val = None
            else:                           val = int(mtch.group(2))
            # Append Result
            res[mtch.group(1)] = {"name" : i[0].strip(), "gets" : val}

        return res

    def convert( self, section, code ):
        """Convert an observed weather code into the new one.
        "section" defines the conversion table. If set to "past" (or "w1" or "w2"; not
        case sensitive) the [past weather] conversion table will be used. If set to
        "present" (or "ww") the [present weather] will be used.
        Returns the value in which the observed "code" is converted. If no specificiation
        is available a "None" is returned.

        Args:
            section (:obj:`str`): One of past/w1/w2 or present/ww. Not case sensitive.
            code (:obj:`int`): Integer with the observed code. If None is given, None
                will be returned. Same yields if "code" is no integer (None returned).

        Returns:
            int/None: Returns an integer or None, depending on the settings.
        """

        if code is None:          return None
        try: code = int(code)
        except TypeError:
           import sys
           sys.exit("Type conversion failed!")
        #if not type(code) == int: return None

        strcode = "{:d}".format(code)
        if section.lower() in ["past","w1","w2"]:
            lookup = self._past_weather_
        elif section.lower() in ["present","ww"]:
            lookup = self._present_weather_
        else:
            import sys
            sys.exit("Problems with wmowwConversion.convert input argument \"section\". " + \
                    "Input section=\"{:s}\" is unknown.".format(section))

        # If key is not defined: return None 
        if not strcode in list(lookup.keys()):        return None
        # Else return the corresponding convert-to value
        return lookup[strcode]["gets"]


    def show( self ):
        """Development method: prints content of the object to stdout.
        """

        print("\nwmoww Config Section \"past weather\":")
        if not self._past_weather_:
            print(" - Nothing defined")
        else:
            for key,values in self._past_weather_.items():
                if values["gets"]:
                    print(" - {0:<50s}: {1:3d} gets {2:4d}".format(values["name"],int(key),values["gets"]))
                else:
                    print(" - {0:<50s}: {1:3d} gets None".format(values["name"],int(key)))

        print("\nwmoww Config Section \"present weather\":")
        if not self._present_weather_:
            print(" - Nothing defined")
        else:
            for key,values in self._present_weather_.items():
                if values["gets"]:
                    print(" - {0:<50s}: {1:3d} gets {2:4d}".format(values["name"],int(key),values["gets"]))
                else:
                    print(" - {0:<50s}: {1:3d} gets None".format(values["name"],int(key)))

#   Helper function which creates a timestamp from a datetime object
def timestamp( dt ):
    "Return POSIX timestamp from datetime object as float"
    import time as t
    return t.mktime( dt.timetuple() )


def datetime2tdate( datetime ):
    "Convert datetime object to tdate"
    return np.floor( timestamp( datetime ) / 86400 )


def tdate2datetime( tdate ):
    "Convert tdate to datetime object"
    from datetime import datetime as dt
    return dt.fromtimestamp( tdate * 86400 )

# -------------------------------------------------------------------
# - Convert date since 1970-01-01 into a readable string 
# -------------------------------------------------------------------
def tdate2string( tdate, moses=False ):
   """ Converts tdate into string of form YYYY-MM-DD.
   Note: a so called tdate is nothing else than an integer value
   indicating the days since 1970-01-01 which is used extensively
   in the wetterturnier (especially to optimize the databases).

   Args:
      date (:obj:`int`): Days since 1970-01-01

   Returns:
      string: Formatted string, format ``%Y-%m-%d``.
   """
   if moses: fmt = "dat%y%m%d"
   else: fmt = "%Y-%m-%d"
   return tdate2datetime( tdate ).strftime( fmt )


def string2tdate( datestring, moses = False ):
    "opposite of the above function"
    from datetime import datetime as dt

    if moses: #mosesYYMMDD
       year = int(datestring[0:2])
       mon  = int(datestring[2:4])
       day  = int(datestring[4:6])
    else:
       year  = int(datestring[0:4])
       mon   = int(datestring[5:7])
       day   = int(datestring[8:10])

    dtobj = dt(year, mon, day)
    return int( timestamp2tdate( timestamp( dtobj ) ) )


def timestamp2tdate( timestamp ):
    return int( timestamp / 86400 )


def tdate2timestamp( tdate ):
    return tdate * 86400


def today_tdate():
    "Returns the current date as tdate"
    from datetime import datetime as dt
    return timestamp2tdate( timestamp( dt.utcnow() ) )
    #today = int( dt.datetime.now().strftime('%s') / 86400 )

# -------------------------------------------------------------------
# - Manipulate special characters to get propper names 
# -------------------------------------------------------------------
def nicename( string, conversion_table = None ):
   """Creates a nice username.
   Mainly used for migration where (from the text files of the old
   wetterturnier archive) a few usernames were including special characters,
   blanks, or other special things. The new Wetterturnier only allows
   propper non-special-character usernames. This function converts
   possibly impropper usernames to its propper equivalent.

   Args:
      string (:obj:`str`): Possibly impropper user name.
      conversion_table (:obj:`dict`): Dict used for string translation. 
                           Default None (unused).

   Returns:
      string: String with nice username without special characters and shit.
   """

   import unicodedata
   import re

   # Check whether conversion table is set. If: check if
   # User is in the conversion table keys. If so, rename
   string = string.strip()
   if conversion_table is not None:
      if string in list(conversion_table.keys()):
         string = conversion_table[string]

   # Escape dangerous characters
   string = re.escape(string).strip()

   nicename = unicodedata.normalize('NFKD', str(string,'ISO-8859-1')) \
                  .encode('ascii', 'ignore')
   if not "Titisee" in nicename and not "Neustadt" in nicename:
      nicename = nicename.replace('/','_')
      nicename = nicename.replace('\/','')
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
   nicename = nicename.replace(' ','_')
   nicename = nicename.replace('\e','e')
   nicename = nicename.replace('?','')
   # - This is only for the Grossmeister
   nicename = nicename.replace('\m','ss')
   if "\\" in nicename:
       exit('nicename is with special ' + nicename)

   return nicename


# -------------------------------------------------------------------
# - Customized exit handling
# -------------------------------------------------------------------
def exit(msg="unknown error"):
   """Simple exit wrapper.
   Can be used to create kind of user-defined exit handling.

   Args:
      msg (:obj:`str`): String, the error message which should be dropped (stderr).
   """

   import sys
   sys.exit('[!] ERROR: %s' % msg)
