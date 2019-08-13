# -------------------------------------------------------------------
# - NAME:        AstralTable.py
# - AUTHOR:      Reto Stauffer
# - DATE:        2018-01-08
# -------------------------------------------------------------------
# - DESCRIPTION: Compute/create astral sunshine duration tables.
# -------------------------------------------------------------------
# - EDITORIAL:   2018-01-08, RS: Created file on thinkreto.
# -------------------------------------------------------------------
# - L@ST MODIFIED: 2018-01-22 18:10 on marvin
# -------------------------------------------------------------------


if __name__ == "__main__":

   import datetime as dt



   import sys, os
   # - Wetterturnier specific modules
   from pywetterturnier import utils
   from pywetterturnier import database
   from pywetterturnier import getobs
   # - Astral package
   import astral
   # - Numpy for the computation
   import numpy as np

   # - Evaluating input arguments
   inputs = utils.inputcheck('ComputePetrus')
   # - Read configuration file
   config = utils.readconfig('config.conf',inputs)

   # - If input_user was given as string we have to find the
   #   corresponding userID first!
   if not config['input_user'] == None:
      print '[!] NOTE: got input -u/--user. Will be ignored in ComputePetrus.'
      config['input_user'] = None


   # - Initializing class and open database connection
   db        = database.database(config)

   # - Looping over cities
   cities     = db.get_cities()

   # - Store result in a numpy ndarray
   ndays = 365

   # - Count stations
   stations = []
   for city in cities:
       for station in db.get_stations_for_city(city["ID"]):
           stations.append( station.wmo )

   # Store results in an ndarray of length ndays
   res = np.ndarray( (ndays,len(stations)), dtype = "float" )

   # Base date
   base_date = dt.date( 2019, 1, 1 ) # Has to be a leap year!

   # - Looping over all cities
   j = -1
   for city in cities:

       # We don't need the obs but use this object as in the computation
       # of the points as it includes the get_maximum_Sd method.
       obj = getobs.getobs( config, db, city, base_date )

       # Looping over stations
       for station in db.get_stations_for_city(city.get("ID")):

          # Increase column index
          j += 1

          # Dummy
          for i in range(0,ndays):

              # Loop date
              date = base_date + dt.timedelta(i)

              # Getting maximum sunshine duration
              sd = obj.get_maximum_Sd( [station], date )

              # Store sunshine duration in hours 
              res[i,j] = sd[station.wmo] / 60.


   # - Create temporary file
   #from tempfile import NamedTemporaryFile
   #ofile = NamedTemporaryFile( delete = False )
   #print "RESULTS will be written into {0:s}".format( ofile.name )

   ofile = open("AstralTable.txt","w")


   header = """# -----------------------------------------------------------------------------------
# Contains the day length (in hours) for all stations used in the Wetterturnier.
# This table has been generated statically using the backend script 'AstralTable.py'
# and might be re-generated when stations are removed and/or added.
#
# This day length is used to convert the observed sunshine duration into relative
# sunshine duration (in percent) as used on Wetterturnier.de as one of the parameters
# to be forecasted.
# To be more explicit, the python astral package is called using the following lines:
#
#   ## Setting up location using station longitude/latitude
#   loc = astral.Location( (nam,'Region',lat,lon,'Europe/London',elevation) )
#   ## Compute sunshine/daylength duration for a specific date
#   res = loc.sun(local=True,date=date)
#   ## Extract day length as maximum sunshine duration possible between
#   ## sunrise and sunset.
#   daylen = int(res['sunset'].strftime('%s')) - int(res['sunrise'].strftime('%s'))
#   daylen = daylen / 60.
#
# This file has been created {0:1s}
# -----------------------------------------------------------------------------------
"""
   ofile.write( header.format(dt.date.today().strftime("%Y-%m-%d")) )

   # - Show results
   # - First: header line with city name
   ofile.write( "{0:>5s} {1:>5s} ".format("","") )
   for city in cities:
       for i in range(0,len(db.get_stations_for_city(city["ID"]))):
            ofile.write( "{0:>10s}".format(city["name"]) )
   ofile.write( "\n" )

   # - Second: header line with colum names
   ofile.write( "{0:>5s} {1:>5s} ".format("month","day") )
   for city in cities:
       for station in db.get_stations_for_city(city["ID"]):
          ofile.write( "{0:10d}".format(station.wmo))
   ofile.write( "\n" )

   # Append data
   for i in range(0,ndays):
      date = base_date + dt.timedelta(i)

      ofile.write( "{0:5d} {1:5d} ".format( int(date.strftime("%m")), int(date.strftime("%d")) ) )
      for c in range(0,len(stations)):
          ofile.write( "{0:10.2f}".format( res[i,c] ) )
      ofile.write( "\n" )








