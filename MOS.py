#!/home/wetterturnier/wetterturnier-backend/venv/bin/python
# -*- coding: utf-8 -*-
"""
This script gets automatically computed at certain times (3z, 9z) to read the MOS tips
and add them to the JSON array which can then be read by the tournament page
``MOS Forecasts´´
The MOS tips get also mixed in a group tip
"""

import sys, os
from glob import glob
import numpy as np
from datetime import datetime as dt
from datetime import timedelta as td
import json
#import jsonmerge
from pywetterturnier import database
from pywetterturnier import utils
#from pywetterturnier.MOSfunctions import *
from collections import OrderedDict

# We only need an output file here since the bet come directly from the database
outfile = "/var/www/html/referrerdata/mos/mos.json"

# - Evaluating input arguments
inputs = utils.inputcheck('MOS')
# - Read configuration file
config = utils.readconfig('config.conf',inputs)

# - Initializing class and open database connection
db     = database.database(config)

import time

def to_seconds(date):
    return time.mktime(date.timetuple())

# get current "run"
z         = dt.utcnow().hour
utc       = dt.utcnow()
utc2      = dt.utcnow() - td(hours=2)

timestamp = int( round( to_seconds(utc) ) )


if config['input_tdate'] == None:
   tdate     = db.current_tournament()
else:
   tdate     = config['input_tdate']

cities     = db.get_cities()
citynames  = db.get_city_names()
paramnames = db.get_parameter_names(sort=True)


# - If input city set, then drop all other cities.
if not config['input_city'] == None:
   tmp = []
   for elem in cities:
      if elem['name'] == config['input_city']: tmp.append( elem )
   cities = tmp

# ----------------------------------------------------------------
# - Check if we are allowed to perform the computation of the
#   MOS bets on this date
# ----------------------------------------------------------------
check = utils.datelock(config, tdate)

if check:
   print '    Date is \'locked\' (datelock). Dont execute.'
   import sys; sys.exit(0)

# -------------------------------------------------------------
# Remove boolean values from list
# -------------------------------------------------------------
def remove_bool_from_list( x ):
   res = {}
   for elem in x:
      if not isinstance(elem,bool):
         res.append( elem )
   return res

#get MOS Group ID. The mean bet of our json table also takes part in
#the tournament as the good old "MOS-Mix" which is now considered as a
#group.
MOS_ID = db.get_group_id("MOS")

#get individual MOS names
MOS_names=[]
MOSSE=db.get_users_in_group( MOS_ID, sort=True )
for i in MOSSE:
   MOS_names.append( db.get_username_by_id(i) )
print MOS_names

# create results dict
datastring="data_"+str(timestamp)
res = { datastring : {}, "models": MOS_names, "locations": citynames, "parameters": paramnames, "timestamps": [timestamp] } 
res = OrderedDict( [ (datastring, {}), ("models",MOS_names), ("locations",citynames), ("parameters",paramnames), ("timestamps", [timestamp]) ] )
print res

for city in cities:
   print city['name']
   res[datastring][city['name']] = {} 
   for ID, MOS_name in zip(MOSSE, MOS_names):
      res[datastring][city['name']][MOS_name] = {}
      for param in paramnames:
         paramID = db.get_parameter_id( param )
         res[datastring][city['name']][MOS_name][param] = []
         for bdate in range(1,3):
	    #print '    - Searching MOS parameter %s' % param
	         # - Loading Parameter ID
	    #if param in ["PPP","TTm","TTn","TTd","RR"]:
	    #   res[datastring][city['name']][MOS_name][param].append( float( res[datastring][city['name']][MOS_name][param].append( db.get_bet_data("user",ID,city['ID'],paramID,tdate,bdate)[0]/10.) ) )
	         #else:
            #print type(db.get_bet_data("user",ID,city['ID'],paramID,tdate,bdate)[0])
            if db.get_bet_data("user",ID,city['ID'],paramID,tdate,bdate) == False:
               res[datastring][city['name']][MOS_name][param].append( 0 )
	    else:
               #if param in ["PPP","TTm","TTn","TTd","RR"]:
               #   print type(db.get_bet_data("user",ID,city['ID'],paramID,tdate,bdate)[0]/10.)
               #   res[datastring][city['name']][MOS_name][param].append( float( res[datastring][city['name']][MOS_name][param].append( db.get_bet_data("user",ID,city['ID'],paramID,tdate,bdate)[0]/10.) ) )
               #else:
               res[datastring][city['name']][MOS_name][param].append( db.get_bet_data("user",ID,city['ID'],paramID,tdate,bdate)[0]/10. )
   

#append result to dict:

z=11
print res

if z == 5:
   pass
   #delete JSON if exists and create new JSON file, append 5z forecast runs
elif z == 11:
   #until we dont get old DWD-MOS runs, only grab bets at 11z
   fid = open(outfile,"w")
   fid.write( json.dumps( res, sort_keys=True ) )
   fid.close()
else:
   res[datastring] = timestamp
   #jsonmerge
   #else append new runs to existing JSON or merge
