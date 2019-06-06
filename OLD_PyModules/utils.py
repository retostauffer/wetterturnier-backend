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
# -------------------------------------------------------------------
# - L@ST MODIFIED: 2015-08-03 12:28 on prognose2.met.fu-berlin.de
# -------------------------------------------------------------------


# -------------------------------------------------------------------
# - Reading configuration file
# -------------------------------------------------------------------
def readconfig(file='config.conf',inputs=None):

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
   # - Reading setup
   try:
      config['htuserfile']       = CNF.get('setup','htuserfile')
   except:
      utils.exit('Problems reading htuserfile from config file')


   # ----------------------------------------------------------------
   # - Loading operational and test judgingclass
   try:
      config['judging_operational'] = CNF.get('judging','operational')
      config['judging_test']        = CNF.get('judging','test')
   except:
      utils.exit('Problems reading necessary judging config!') 
   # - Now we have to check if these files exists.
   check_file("PyModules/judgingclass%s.py" % config['judging_operational'])
   check_file("PyModules/judgingclass%s.py" % config['judging_test']       )


   # ----------------------------------------------------------------
   # - Some configs where the data are.
   #   data_moses:     where Klaus Knuepffer stores the moses equations 
   try:
      config['data_moses']       = CNF.get('data','moses')
   except:
      utils.exit('Problems rading all required data infos from config file')
   check_directory( config['data_moses'] )

   # ----------------------------------------------------------------
   # - Reading system relevant things
   try:
      config['rawdir']           = CNF.get('system','rawdir')
   except:
      utils.exit('Problems rading all required system infos from config file')
   check_directory( config['rawdir'] )

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
         if inputs[k] == 'None':
            config[k] = None 
         else:
            config[k] = inputs[k]

   return config


# -------------------------------------------------------------------
# - Convert date since 1970-01-01 into a readable string 
# -------------------------------------------------------------------
def tdate2string( date ):

   from datetime import datetime as dt

   return dt.fromtimestamp( date*86400 ).strftime('%Y-%m-%d')


# -------------------------------------------------------------------
# - Manipulate special characters to get propper names 
# -------------------------------------------------------------------
def nicename( string ):

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

   import sys
   sys.exit('[!] ERROR: %s' % msg)

